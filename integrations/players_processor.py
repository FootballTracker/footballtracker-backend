import os
import json
import time
import requests
from datetime import datetime, timezone
from database.database import async_session_factory
from models.base_player import BasePlayer
from models.country import Country
from sqlalchemy import select
from config import HEADERS, API_HOST
from integrations.save_json import (
    load_rate_limit_data,
    save_rate_limit_data,
    is_rate_limit_reached,
    get_rate_limit_status,
)

RATE_LIMIT_PATH = "json/rate_limit.json"
REQUEST_INTERVAL_SECONDS = 20
FETCHED_FOLDER = "json/fetched"


async def fetch_player_by_id(api_id: int):
    print(f"Buscando jogador com ID {api_id}...")
    response = requests.get(
        f"https://{API_HOST}/players/profiles",
        headers=HEADERS,
        params={"player": api_id},
    )

    if response.status_code != 200:
        print(f"Erro ao buscar jogador {api_id}: {response.status_code}")
        return None

    data = response.json().get("response", [])
    if not data:
        return None

    return data[0]


async def fetch_and_store_players():
    rate_data = load_rate_limit_data()
    current_requests = get_rate_limit_status()
    if current_requests is None:
        current_requests = rate_data.get("current_requests", 0)

    files = sorted(
        [
            f
            for f in os.listdir(FETCHED_FOLDER)
            if f.startswith("fixture_") and f.endswith(".json")
        ]
    )

    seen_player_ids = set()

    for file_name in files:
        print(f"\n Processando arquivo: {file_name}")
        file_path = os.path.join(FETCHED_FOLDER, file_name)
        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        response = content.get("response", [])

        async with async_session_factory() as session:
            for item in response:
                team_players = item.get("players", [])

                for player_entry in team_players:
                    players_list = player_entry.get("players", [])

                    for player_info_entry in players_list:
                        player_info = player_info_entry.get("player", {})
                        api_id = player_info.get("id")

                        if not api_id or api_id in seen_player_ids:
                            continue

                        seen_player_ids.add(api_id)

                        existing = await session.execute(
                            select(BasePlayer).where(BasePlayer.api_id == api_id)
                        )
                        if existing.scalar():
                            continue

                        if is_rate_limit_reached():
                            print("Limite diário de requisições atingido.")
                            return

                        full_data = await fetch_player_by_id(api_id)
                        if not full_data:
                            continue

                        player_data = full_data.get("player", {})
                        birth_country_name = player_data.get("birth", {}).get("country")
                        nationality_name = player_data.get("nationality")

                        birth_country_id = None
                        nationality_id = None

                        if birth_country_name:
                            result = await session.execute(
                                select(Country.id).where(
                                    Country.name == birth_country_name
                                )
                            )
                            birth_country_id = result.scalar()

                        if nationality_name:
                            result = await session.execute(
                                select(Country.id).where(
                                    Country.name == nationality_name
                                )
                            )
                            nationality_id = result.scalar()

                        birth_date = player_data.get("birth", {}).get("date")
                        birth_date = (
                            datetime.strptime(birth_date, "%Y-%m-%d").date()
                            if birth_date
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
                            last_updated=datetime.now(timezone.utc).replace(
                                tzinfo=None
                            ),
                        )

                        print(f"Adicionando jogador {player.name} ({player.api_id})")
                        session.add(player)
                        await session.commit()

                        current_requests += 1
                        save_rate_limit_data(
                            current_requests=current_requests,
                            last_page=0,
                        )

                        print(f"Esperando {REQUEST_INTERVAL_SECONDS}s...")
                        time.sleep(REQUEST_INTERVAL_SECONDS)
