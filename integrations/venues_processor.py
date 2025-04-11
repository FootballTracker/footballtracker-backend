import json
import os
from database.database import async_session_factory
from datetime import datetime, timezone
from models.venue import Venue
from models.country import Country
from sqlalchemy.future import select


async def process_venues_json_and_save_to_db(file_name):
    json_dir = "json"
    file_path = os.path.join(json_dir, file_name)

    try:
        with open(file_path, "r") as json_file:
            data = json.load(json_file)
        if "response" in data and isinstance(data["response"], list):
            async with async_session_factory() as session:
                for venue_data in data["response"]:
                    venue_id_from_api = venue_data.get("id")
                    venue_name = venue_data.get("name")
                    venue_address = venue_data.get("address")
                    venue_city = venue_data.get("city")
                    venue_capacity = venue_data.get("capacity")
                    venue_surface = venue_data.get("surface")
                    venue_image = venue_data.get("image")
                    country_name = venue_data.get("country")

                    if country_name:
                        query = select(Country).where(Country.name == country_name)
                        result = await session.execute(query)
                        country = result.scalar_one_or_none()

                        if country and venue_id_from_api is not None:
                            venue = Venue(
                                api_id=venue_id_from_api,
                                name=venue_name,
                                address=venue_address,
                                city=venue_city,
                                capacity=venue_capacity,
                                surface=venue_surface,
                                image_url=venue_image,
                                last_updated=datetime.now(timezone.utc).replace(
                                    tzinfo=None
                                ),
                                country_id=country.id,
                            )
                            session.add(venue)
                        elif not country:
                            print(
                                f"  País '{country_name}' não encontrado na base de dados para o estadio '{venue_name}'."
                            )
                        elif venue_id_from_api is None:
                            print(
                                f"  ID do estadio não encontrado na API para o estadio '{venue_name}'."
                            )
                    else:
                        print(
                            f"  Nome do país não encontrado para o estadio '{venue_name}'."
                        )
                await session.commit()
                print(
                    f"Foram salvos {len(data['response'])} estadios na base de dados."
                )
        else:
            print(
                "Formato JSON inesperado para estadios: 'response' não encontrado ou não é uma lista."
            )

    except FileNotFoundError:
        print(f"Arquivo não encontrado: {file_path}")
    except Exception as e:
        print(f"Erro ao processar os dados: {e}")
