from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fixture_lineup import FixtureLineup
from models.league_team import LeagueTeam
from models.league import League


async def process_fixture_lineups(session: AsyncSession, fixture_data: dict):
    print(" Procesando escalações...")
    fixture_api_id = fixture_data["fixture"]["id"]

    league_api_id = fixture_data["league"]["id"]

    for lineup_data in fixture_data.get("lineups", []):
        team_api_id = lineup_data["team"]["id"]

        query = (
            select(LeagueTeam.id)
            .join(League, LeagueTeam.league_id == League.id)
            .where(
                LeagueTeam.base_team_api_id == team_api_id,
                League.api_id == league_api_id,
            )
        )

        league_team_result = await session.execute(query)
        league_team_id = league_team_result.scalar_one_or_none()

        if not league_team_id:
            print(
                f"ADVERTENCIA: Não se encontrou LeagueTeam para team_api_id {team_api_id} e league_api_id {league_api_id}"
            )
            continue

        new_lineup = FixtureLineup(
            fixture_id=fixture_api_id,
            league_team_id=league_team_id,
            coach_api_id=lineup_data.get("coach", {}).get("id"),
            formation=lineup_data.get("formation"),
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(new_lineup)
