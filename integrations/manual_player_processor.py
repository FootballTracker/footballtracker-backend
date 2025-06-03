import time
from datetime import datetime, timezone
from sqlalchemy import select
from database.database import async_session_factory
from models.base_player import BasePlayer
from models.country import Country
from integrations.players_processor import fetch_player_by_id
from integrations.save_json import (
    load_rate_limit_data,
    save_rate_limit_data,
    is_rate_limit_reached,
    get_rate_limit_status,
)

REQUEST_INTERVAL_SECONDS = 20


async def fetch_and_store_specific_players(player_ids: list[int]):
    print(f"Iniciando busca específica para os IDs: {player_ids}")

    rate_data = load_rate_limit_data()
    current_requests = get_rate_limit_status()
    if current_requests is None:
        current_requests = rate_data.get("current_requests", 0)

    unique_player_ids = set(player_ids)

    async with async_session_factory() as session:
        for api_id in unique_player_ids:
            existing_result = await session.execute(
                select(BasePlayer).where(BasePlayer.api_id == api_id)
            )
            if existing_result.scalar_one_or_none():
                print(f"Jogador com ID {api_id} já existe no banco de dados. Omitindo.")
                continue

            if is_rate_limit_reached():
                print("Limite diário de requisições da API atingido. Interrompendo.")
                return

            full_data = await fetch_player_by_id(api_id)
            if not full_data:
                print(
                    f"Não foram encontrados dados para o jogador com ID {api_id}. Omitindo."
                )
                continue

            player_data = full_data.get("player", {})
            birth_country_name = player_data.get("birth", {}).get("country")
            nationality_name = player_data.get("nationality")

            birth_country_id = None
            nationality_id = None

            if birth_country_name:
                country_result = await session.execute(
                    select(Country.id).where(Country.name == birth_country_name)
                )
                birth_country_id = country_result.scalar()

            if nationality_name:
                country_result = await session.execute(
                    select(Country.id).where(Country.name == nationality_name)
                )
                nationality_id = country_result.scalar()

            birth_date_str = player_data.get("birth", {}).get("date")
            birth_date = (
                datetime.strptime(birth_date_str, "%Y-%m-%d").date()
                if birth_date_str
                else None
            )

            player = BasePlayer(
                api_id=api_id,
                name=player_data.get("name", ""),
                firstname=player_data.get("firstname", ""),
                lastname=player_data.get("lastname"),
                age=player_data.get("age"),
                birth_date=birth_date,
                birth_place=player_data.get("birth", {}).get("place"),
                birth_country_id=birth_country_id,
                nationality_id=nationality_id,
                height=player_data.get("height"),
                weight=player_data.get("weight"),
                injured=player_data.get("injured", False),
                photo_url=player_data.get("photo"),
                last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
            )

            print(f"Adicionando jogador: {player.name} ({player.api_id})")
            session.add(player)
            await session.commit()

            current_requests += 1
            save_rate_limit_data(current_requests=current_requests, last_page=0)
            print(f"Esperando {REQUEST_INTERVAL_SECONDS}s...")
            time.sleep(REQUEST_INTERVAL_SECONDS)

    print("\n✅ Processo de busca específica de jogadores completado.")
