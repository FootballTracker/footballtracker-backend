import json
import os
from database.database import async_session_factory
from datetime import datetime, timezone
from models.league_team import LeagueTeam
from models.league import League
from models.base_team import BaseTeam
from models.venue import Venue
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


async def link_teams_to_league_and_venues(
    file_name: str, api_league_id: int, season: int
):
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)

        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:

                query_league = select(League).where(
                    League.api_id == api_league_id, League.season == season
                )
                result_league = await session.execute(query_league)
                db_league = result_league.scalar_one_or_none()

            if not db_league:
                print(
                    f"Campeonato com ID {api_league_id} e temporada {season} não encontrado."
                )
                return

            leagues_teams_to_add = []

            for team_data_wrapper in data["response"]:
                team_info = team_data_wrapper.get("team")
                venue_info = team_data_wrapper.get("venue")

                if not team_info or not venue_info:
                    print("Dados incompletos para o time ou estadio.")
                    continue

                team_id_from_api = team_info.get("id")
                venue_id_from_api = venue_info.get("id")
                team_name = team_info.get("name")

                if team_id_from_api is not None and venue_id_from_api is not None:
                    query_team = select(BaseTeam).where(
                        BaseTeam.api_id == team_id_from_api
                    )
                    result_team = await session.execute(query_team)
                    db_team = result_team.scalar_one_or_none()

                    query_venue = select(Venue).where(Venue.api_id == venue_id_from_api)
                    result_venue = await session.execute(query_venue)
                    db_venue = result_venue.scalar_one_or_none()

                    if db_team and db_venue:
                        db_league_team = LeagueTeam(
                            league_id=db_league.id,
                            base_team_api_id=db_team.api_id,
                            venue_id=db_venue.api_id,
                            last_updated=datetime.now(timezone.utc).replace(
                                tzinfo=None
                            ),
                        )
                        leagues_teams_to_add.append(db_league_team)
                    else:
                        if not db_team:
                            print(
                                f"  Equipe (ID API: {team_id_from_api}, Nome: {team_name}) não encontrado na base de dados BaseTeam."
                            )
                        if not db_venue:
                            print(
                                f"  Estadio (ID API: {venue_id_from_api}, Nome: {venue_info.get('name', 'Desconhecido')}) não encontrado na base de dados Venue."
                            )
                else:
                    print(
                        f"  ID da equipe ou ID do estadio não encontrado para o time {team_name}."
                    )

            session.add_all(leagues_teams_to_add)

            try:
                await session.commit()
                print(
                    f"Se juntaram {len(leagues_teams_to_add)} equipes no campeonato (ID API: {api_league_id}, Temporada: {season})."
                )
            except IntegrityError:
                await session.rollback()
                print(
                    f"Erro de integridade: intentando juntar uma equipe (api_id) no campeonato (ID DB: {db_league.id}) mais de uma vez."
                )
            except Exception as e:
                await session.rollback()
                print(f"Erro durante o commit de LeagueTeam: {e}")

        else:
            print(
                "Formato JSON inesperado para equipes: 'response' não encontrado ou não é uma lista."
            )
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except json.JSONDecodeError:
        print(f"Erro: Não foi possível decodificar o arquivo JSON {file_path}.")
    except Exception as e:
        print(f"Erro ao processar ou enlazar os dados de equipes e campeonatos: {e}")
