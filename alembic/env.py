import logging
from sqlalchemy.ext.asyncio import create_async_engine

from alembic import context

from database.database import Base, DATABASE_URL
from models import (
    base_coach,
    base_player,
    base_team,
    country,
    fixture_lineup,
    fixture_player_stat,
    fixture_statistic,
    fixture,
    league_classification,
    league,
    league_team,
    player_season_stat,
    venue,
)

import asyncio

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

logger.info("O script env.py está sendo executado!")

target_metadata = Base.metadata


def run_migrations_online():
    logger.info("Iniciando run_migrations_online")
    engine = create_async_engine(DATABASE_URL)

    def do_run_migrations(connection):
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            compare_type=True,
            dialect_opts={"paramstyle": "named"},
        )

        with context.begin_transaction():
            context.run_migrations()

    async def run_async():
        async with engine.connect() as connection:
            logger.info("Conexão com o banco de dados bem-sucedida")
            await connection.run_sync(do_run_migrations)
            logger.info("Migrações concluídas")

    try:
        asyncio.run(run_async())
    except Exception as e:
        logger.error(f"Erro durante a migração: {e}")
        raise


run_migrations_online()
logger.info("O script env.py terminou de ser executado!")
