import json
import os
from config import API_HOST, HEADERS
from database.database import async_session_factory
from datetime import datetime, timezone
from models.base_team import BaseTeam
from models.country import Country
from sqlalchemy.future import select
from sqlalchemy.exc import IntegrityError


async def process_teams_json_and_save_to_db(file_name):
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)

        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:
                for team_data_wrapper in data["response"]:
                    team_info = team_data_wrapper.get("team")
                    # venue_info = team_data_wrapper.get("venue")

                    if not team_info:
                        print(f"Datos incompletos para um time: {team_data_wrapper}")
                        continue

                    team_id_from_api = team_info.get("id")
                    team_name = team_info.get("name")
                    team_code = team_info.get("code")
                    country_name = team_info.get("country")
                    team_founded = team_info.get("founded")
                    team_national = team_info.get("national")
                    team_logo = team_info.get("logo")

                    print(
                        f"Procesando equipo: {team_name}, País: {country_name}, ID API: {team_id_from_api}"
                    )

                    if country_name:
                        query = select(Country).where(Country.name == country_name)
                        result = await session.execute(query)
                        country = result.scalar_one_or_none()

                        if country and team_id_from_api is not None:
                            # Verificar se o time já existe para evitar duplicados
                            existing_team = await session.get(
                                BaseTeam, team_id_from_api
                            )

                            if existing_team is None:
                                db_team = BaseTeam(
                                    api_id=team_id_from_api,
                                    name=team_name,
                                    code=team_code,
                                    founded=team_founded,
                                    national=team_national,
                                    logo_url=team_logo,
                                    last_updated=datetime.now(timezone.utc).replace(
                                        tzinfo=None
                                    ),
                                    country_id=country.id,
                                )
                                session.add(db_team)
                                print(f"  Time '{team_name}' agregado.")
                            else:
                                print(
                                    f"  Time '{team_name}' (ID API: {team_id_from_api}) já existe na base de dados. Pulando para o próximo"
                                )

                        elif not country:
                            print(
                                f"  País '{country_name}' não encontrado na base de dados para o time '{team_name}'."
                            )
                        elif team_id_from_api is None:
                            print(
                                f"  ID do time não encontrado na API para o time '{team_name}'."
                            )
                    else:
                        print(
                            f"  Nome do país não encontrado para o time equipo '{team_name}'."
                        )

                await session.commit()
                print(f"Processo de guardado dos times completado.")

        else:
            print(
                "Formato JSON inesperado para os times: 'response' não encontrado o não é uma lista."
            )

    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except json.JSONDecodeError:
        print(f"Erro: Não foi possível decodificar o arquivo JSON {file_path}.")
    except IntegrityError as e:
        await session.rollback()
        print(f"Error na integridade para guardar os times: {e}")
    except Exception as e:
        print(f"Erro ao processar os dados dos times: {e}")
