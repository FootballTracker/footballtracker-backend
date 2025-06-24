import os
import json
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from database.database import async_session_factory
from integrations.fixture_details_processor.events_processor import (
    process_fixture_events,
)
from integrations.fixture_details_processor.lineups_processor import (
    process_fixture_lineups,
)

from integrations.fixture_details_processor.statistics_processor import (
    process_fixture_statistics,
)
from integrations.fixture_details_processor.stats_processor import (
    process_fixture_player_stats,
)


async def process_fixture_file(
    session: AsyncSession, file_path: str, tables_to_process: list[str]
):
    with open(file_path, "r", encoding="utf-8") as f:
        content = json.load(f)

    fixture_data = content.get("response", [])
    if not fixture_data:
        print(
            f"  Arqhivo {os.path.basename(file_path)} está vacío ou mal formatado. Omitir."
        )
        return

    fixture_data = fixture_data[0]

    if "events" in tables_to_process:
        await process_fixture_events(session, fixture_data)

    if "lineups" in tables_to_process:
        await process_fixture_lineups(session, fixture_data)

    if "statistics" in tables_to_process:
        await process_fixture_statistics(session, fixture_data)

    if "player_stats" in tables_to_process:
        await process_fixture_player_stats(session, fixture_data)


async def process_all_fixtures(folder_path: str, tables_to_process: list[str]):

    print(f"Iniciando processamento das fixtures em: {folder_path}")
    print(f"Tabelas a popular: {tables_to_process}")

    files = sorted(
        [
            f
            for f in os.listdir(folder_path)
            if f.startswith("fixture_") and f.endswith(".json")
        ]
    )

    for file_name in files:
        file_path = os.path.join(folder_path, file_name)
        print(f"\nProcessando arquivo: {file_name}")

        try:
            async with async_session_factory() as session:
                async with session.begin():
                    await process_fixture_file(session, file_path, tables_to_process)
            print(f"Arquivo {file_name} processado e guardado exitosamente.")
        except Exception as e:
            print(f"ERRO ao processar o arquivo {file_name}: {e}")

    print("\n✅ Processo de todos os fixtures completado.")
