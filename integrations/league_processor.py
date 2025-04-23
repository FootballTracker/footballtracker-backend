import json
import os
from config import API_HOST, HEADERS
from database.database import async_session_factory
from datetime import datetime, timezone
from models.league import League
from models.country import Country
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


async def process_league_json_and_save_to_db(file_name):
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)

        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:
                for league_data in data["response"]:
                    league_info = league_data.get("league")
                    country_info = league_data.get("country")
                    seasons_list = league_data.get("seasons")

                    if not league_info or not country_info or not seasons_list:
                        print(f"Campos ausentes em league_data: {league_data}")
                        continue

                    league_id_from_api = league_info.get("id")
                    league_name = league_info.get("name")
                    league_type = league_info.get("type")
                    league_logo = league_info.get("logo")
                    country_name = country_info.get("name")

                    if country_name:
                        query = select(Country).where(Country.name == country_name)
                        result = await session.execute(query)
                        country = result.scalar_one_or_none()

                        if country:
                            for season_data in seasons_list:
                                season_year = season_data.get("year")
                                season_start = season_data.get("start")
                                season_end = season_data.get("end")

                                if season_year and season_start and season_end:
                                    db_league = League(
                                        name=league_name,
                                        country_id=country.id,
                                        api_id=league_id_from_api,
                                        season=season_year,
                                        type=league_type,
                                        logo_url=league_logo,
                                        start_date=datetime.strptime(
                                            season_start, "%Y-%m-%d"
                                        ).replace(tzinfo=timezone.utc),
                                        end_date=datetime.strptime(
                                            season_end, "%Y-%m-%d"
                                        ).replace(tzinfo=timezone.utc),
                                        last_updated=datetime.now(timezone.utc).replace(
                                            tzinfo=None
                                        ),
                                    )
                                    session.add(db_league)
                                else:
                                    print(
                                        f"Dados incompletos para o campeonato {league_name} com o ID API: {league_id_from_api}"
                                    )

                        else:
                            print(
                                f"Pais {country_name} na base de dados para o campeonato {league_name}"
                            )

                    else:
                        print(
                            f"Nome do pais não encontrado para o campeonato {league_name}"
                        )

                await session.commit()
                print(f"Campeonatos salvos com sucesso no banco de dados")

        else:
            print(
                "Formato JSON inesperado para campeonatos: 'response' não encontrado ou não é uma lista"
            )

    except FileNotFoundError:
        print(f"Arquivo JSON não encontrado: {file_path}")
    except json.JSONDecodeError as e:
        print(f"Erro ao decodificar JSON: {e}")
    except IntegrityError:
        await session.rollback()
        print(
            f"Erro de integridade ao salvar no banco de dados: Tentando guardar um campeonato (api_id, season) duplicada"
        )
    except Exception as e:
        print(f"Erro ao processar o arquivo JSON: {e}")
