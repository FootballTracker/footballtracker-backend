import json
import os
from database.database import async_session_factory
from datetime import datetime, timezone
from models.country import Country


async def process_countries_json_and_save_to_db(file_name="countries.json"):
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:
                for country_data in data["response"]:
                    country = Country(
                        name=country_data["name"],
                        flag_url=country_data["flag"],
                        last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
                    )
                    session.add(country)

                await session.commit()

        print("Dados dos países processados e salvos no banco de dados com sucesso!")
    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except Exception as e:
        print(f"Erro ao processar os dados: {e}")
