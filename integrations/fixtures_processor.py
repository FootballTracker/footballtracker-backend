import json
import os
from database.database import async_session_factory
from datetime import datetime, timezone
from models.fixture import Fixture
from models.league import League
from models.venue import Venue
from models.league_team import LeagueTeam
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy import and_


async def process_fixtures_json_and_save_to_db(file_name: str):
    """
    Lê um arquivo JSON de partidas e salva os dados na tabela fixtures.
    Busca os IDs de liga, equipes e estádios nas tabelas correspondentes
    (incluindo league_teams para as equipes no contexto da liga),
    baseando-se no modelo Fixture fornecido.

    Args:
        file_name (str): O nome do arquivo JSON de partidas (dentro da pasta json/).
    """
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)

        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:
                fixtures_to_add = []

                for fixture_data_wrapper in data["response"]:
                    fixture_info = fixture_data_wrapper.get("fixture")
                    league_info = fixture_data_wrapper.get("league")
                    teams_info = fixture_data_wrapper.get("teams")
                    score_info = fixture_data_wrapper.get("score")

                    if not fixture_info or not league_info or not teams_info:
                        print(
                            f"Dados incompletos para uma partida no wrapper: {fixture_data_wrapper.get('fixture', {}).get('id', 'N/A')}. Pulando."
                        )
                        continue

                    # Extrair dados do JSON
                    fixture_id_from_api = fixture_info.get("id")
                    fixture_referee = fixture_info.get("referee")
                    fixture_timezone = fixture_info.get("timezone")
                    fixture_date_str = fixture_info.get("date")
                    venue_info = fixture_info.get(
                        "venue"
                    )  # Informação do estádio dentro de fixture
                    status_info = fixture_info.get(
                        "status"
                    )  # Informação do status da partida

                    league_id_from_api = league_info.get("id")
                    league_season = league_info.get(
                        "season"
                    )  # Campo 'season' do modelo Fixture
                    league_round = league_info.get("round")

                    home_team_info = teams_info.get("home")
                    away_team_info = teams_info.get("away")

                    # Extrair scores de tempo integral
                    home_score_fulltime = (
                        score_info.get("fulltime", {}).get("home")
                        if score_info
                        else None
                    )
                    away_score_fulltime = (
                        score_info.get("fulltime", {}).get("away")
                        if score_info
                        else None
                    )

                    # Extrair informações de status
                    fixture_status_long = (
                        status_info.get("long") if status_info else None
                    )  # Campo 'status' do modelo
                    fixture_status_short = (
                        status_info.get("short") if status_info else None
                    )  # Campo 'status_short' do modelo
                    fixture_elapsed = (
                        status_info.get("elapsed") if status_info else None
                    )  # Campo 'elapsed' do modelo

                    venue_id_from_api = (
                        venue_info.get("id") if venue_info else None
                    )  # Pode ser None se não houver info de estádio

                    # --- Validar dados essenciais antes de buscar no DB ---
                    if (
                        fixture_id_from_api is None
                        or league_id_from_api is None
                        or league_season is None
                        or league_round is None  # 'round' é NOT NULL no modelo
                        or fixture_status_short is None
                        or not home_team_info
                        or not away_team_info
                    ):
                        print(
                            f"Dados essenciais faltando para a partida com ID API {fixture_id_from_api}. Pulando."
                        )
                        continue

                    home_team_id_from_api = home_team_info.get("id")
                    away_team_id_from_api = away_team_info.get("id")

                    if home_team_id_from_api is None or away_team_id_from_api is None:
                        print(
                            f"ID de equipe local ou visitante faltando no JSON para a partida ID API {fixture_id_from_api}. Pulando."
                        )
                        continue

                    # Converter a data de string para datetime e remover zona horária para TIMESTAMP WITHOUT TIME ZONE
                    fixture_date = None
                    if fixture_date_str:
                        try:
                            # Tentar parsear com e sem fuso horário 'Z'
                            dt_object = datetime.fromisoformat(
                                fixture_date_str.replace("Z", "+00:00")
                            )
                            # Remover informação de fuso horário para a coluna TIMESTAMP WITHOUT TIME ZONE
                            fixture_date = dt_object.replace(tzinfo=None)

                        except ValueError:
                            print(
                                f"  Não foi possível parsear a data '{fixture_date_str}' para a partida ID API {fixture_id_from_api}. Pulando."
                            )
                            continue
                    # Verificar se a data foi parseada com sucesso (se fixture_date_str não era None)
                    elif (
                        fixture_date_str is not None
                    ):  # A API pode enviar null, mas se enviou string que não parseou
                        print(
                            f"  Data da partida não fornecida no JSON para a partida ID API {fixture_id_from_api}. Pulando."
                        )
                        continue

                    print(
                        f"Processando partida ID API: {fixture_id_from_api}, Liga ID API: {league_id_from_api}, Temporada: {league_season}, Rodada: {league_round}"
                    )

                    # --- Buscar os IDs correspondentes no banco de dados ---

                    # 1. Buscar a Liga no banco de dados para obter seu ID do DB
                    # Usamos api_id e season para encontrar a entrada correta da Liga no DB
                    query_league = select(League).where(
                        and_(
                            League.api_id == league_id_from_api,
                            League.season == league_season,
                        )
                    )
                    result_league = await session.execute(query_league)
                    db_league = result_league.scalar_one_or_none()

                    if not db_league:
                        print(
                            f"  Liga (ID API: {league_id_from_api}, Temporada: {league_season}) não encontrada no banco de dados para a partida ID API {fixture_id_from_api}. Pulando."
                        )
                        continue  # Não podemos salvar a partida sem a liga

                    # 2. Buscar o ID de LeagueTeam para a equipe Local
                    # Precisamos do ID do LeagueTeam que vincula a liga e o time local (usando api_id do time)
                    db_home_league_team_id = None
                    if home_team_id_from_api is not None:
                        query_home_league_team = select(LeagueTeam.id).where(
                            and_(
                                LeagueTeam.league_id
                                == db_league.id,  # Usamos o ID da liga do DB
                                LeagueTeam.base_team_api_id
                                == home_team_id_from_api,  # Usamos o api_id da equipe
                            )
                        )
                        result_home_league_team = await session.execute(
                            query_home_league_team
                        )
                        db_home_league_team_id = (
                            result_home_league_team.scalar_one_or_none()
                        )

                    if not db_home_league_team_id:
                        print(
                            f"  Entrada em LeagueTeam para Equipe Local (ID API: {home_team_id_from_api}) na Liga (ID DB: {db_league.id}) não encontrada. Pulando partida ID API {fixture_id_from_api}."
                        )
                        continue  # Não podemos salvar a partida sem o vínculo LeagueTeam para a equipe local

                    # 3. Buscar o ID de LeagueTeam para a equipe Visitante
                    # Precisamos do ID do LeagueTeam que vincula a liga e o time visitante (usando api_id do time)
                    db_away_league_team_id = None
                    if away_team_id_from_api is not None:
                        query_away_league_team = select(LeagueTeam.id).where(
                            and_(
                                LeagueTeam.league_id
                                == db_league.id,  # Usamos o ID da liga do DB
                                LeagueTeam.base_team_api_id
                                == away_team_id_from_api,  # Usamos o api_id da equipe
                            )
                        )
                        result_away_league_team = await session.execute(
                            query_away_league_team
                        )
                        db_away_league_team_id = (
                            result_away_league_team.scalar_one_or_none()
                        )

                    if not db_away_league_team_id:
                        print(
                            f"  Entrada em LeagueTeam para Equipe Visitante (ID API: {away_team_id_from_api}) na Liga (ID DB: {db_league.id}) não encontrada. Pulando partida ID API {fixture_id_from_api}."
                        )
                        continue  # Não podemos salvar a partida sem o vínculo LeagueTeam para a equipe visitante

                    # 4. Buscar o Estádio no banco de dados (pode ser None)
                    db_venue = None
                    db_venue_api_id = (
                        None  # Usaremos o api_id do estádio do DB para o campo venue_id
                    )
                    if venue_id_from_api is not None:
                        # Assumindo que Venue.api_id é o ID da API do estádio
                        query_venue = select(Venue).where(
                            Venue.api_id == venue_id_from_api
                        )  # Busca por Venue.api_id
                        result_venue = await session.execute(query_venue)
                        db_venue = result_venue.scalar_one_or_none()

                        if db_venue:
                            db_venue_api_id = (
                                db_venue.api_id
                            )  # Usamos db_venue.api_id para o FK em Fixture
                        else:
                            print(
                                f"  Estádio (ID API: {venue_id_from_api}) não encontrado no banco de dados Venue (buscando por api_id) para a partida ID API {fixture_id_from_api}. O campo venue_id será NULL."
                            )

                    # --- Criar o objeto Fixture se todos os IDs necessários foram encontrados ---
                    # Se chegarmos aqui, db_league, db_home_league_team_id e db_away_league_team_id estão garantidos
                    db_fixture = Fixture(
                        api_id=fixture_id_from_api,
                        league_id=db_league.id,  # ID da liga do DB
                        season=league_season,  # Campo 'season'
                        date=fixture_date,  # Objeto datetime sem fuso horário (match_DATE)
                        status=fixture_status_long,  # Campo 'status' (status longo)
                        status_short=fixture_status_short,  # Campo 'status_short' (status curto)
                        venue_id=db_venue_api_id,  # ID do estádio do DB (api_id) (ou None)
                        referee=fixture_referee,
                        home_team_id=db_home_league_team_id,  # ID de LeagueTeam para a equipe local
                        away_team_id=db_away_league_team_id,  # ID de LeagueTeam para a equipe visitante
                        home_team_score_goals=home_score_fulltime,  # Placar local tempo integral
                        away_team_score_goals=away_score_fulltime,  # Placar visitante tempo integral
                        elapsed=fixture_elapsed,  # Tempo decorrido
                        timezone=fixture_timezone,  # Fuso horário
                        round=league_round,  # Rodada da liga
                        last_updated=datetime.now(timezone.utc).replace(
                            tzinfo=None
                        ),  # Sem fuso horário
                    )
                    fixtures_to_add.append(db_fixture)
                    # print(f"  Partida ID API {fixture_id_from_api} adicionada à sessão.")

                # Adicionar todos os objetos Fixture à sessão de uma vez
                session.add_all(fixtures_to_add)

                try:
                    await session.commit()
                    print(
                        f"Foram salvas {len(fixtures_to_add)} partidas no banco de dados."
                    )
                except IntegrityError:
                    await session.rollback()
                    print(
                        f"Erro de integridade ao salvar partidas: tentando salvar uma partida (api_id) duplicada."
                    )
                except Exception as e:
                    await session.rollback()
                    print(f"Erro durante o commit de Fixtures: {e}")

        else:
            print(
                "Formato JSON inesperado para partidas: 'response' não encontrado ou não é uma lista."
            )

    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except json.JSONDecodeError:
        print(f"Erro: Não foi possível decodificar o arquivo JSON {file_path}.")
    except Exception as e:
        print(f"Erro ao processar ou salvar os dados de partidas: {e}")
