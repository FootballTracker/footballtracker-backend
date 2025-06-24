from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fixture_statistic import FixtureStatistic
from models.league_team import LeagueTeam
from models.league import League


async def process_fixture_statistics(session: AsyncSession, fixture_data: dict):
    print(" Processando estadísticas do time...")
    fixture_api_id = fixture_data["fixture"]["id"]
    league_api_id_from_json = fixture_data["league"]["id"]

    for team_stats_data in fixture_data.get("statistics", []):
        team_api_id = team_stats_data["team"]["id"]

        query = (
            select(LeagueTeam.id)
            .join(League, LeagueTeam.league_id == League.id)
            .where(
                LeagueTeam.base_team_api_id == team_api_id,
                League.api_id == league_api_id_from_json,
            )
        )
        league_team_id = (await session.execute(query)).scalar_one_or_none()

        if not league_team_id:
            print(
                f"ADVERTENCIA: Não se encontrou LeagueTeam para team_api_id {team_api_id} e league_api_id {league_api_id_from_json}"
            )
            continue

        stats_map = {
            stat["type"]: stat["value"]
            for stat in team_stats_data.get("statistics", [])
        }

        expected_goals_value = stats_map.get("expected_goals")

        new_fixture_stat = FixtureStatistic(
            fixture_id=fixture_api_id,
            league_team_id=league_team_id,
            shots_on_goal=stats_map.get("Shots on Goal"),
            shots_off_goal=stats_map.get("Shots off Goal"),
            total_shots=stats_map.get("Total Shots"),
            blocked_shots=stats_map.get("Blocked Shots"),
            shots_insidebox=stats_map.get("Shots insidebox"),
            shots_outsidebox=stats_map.get("Shots outsidebox"),
            fouls=stats_map.get("Fouls"),
            corner_kicks=stats_map.get("Corner Kicks"),
            offsides=stats_map.get("Offsides"),
            ball_possession=(
                str(stats_map.get("Ball Possession")).replace("%", "")
                if stats_map.get("Ball Possession")
                else None
            ),
            yellow_cards=stats_map.get("Yellow Cards"),
            red_cards=stats_map.get("Red Cards"),
            goalkeeper_saves=stats_map.get("Goalkeeper Saves"),
            total_passes=stats_map.get("Total passes"),
            passes_accurate=stats_map.get("Passes accurate"),
            passes_percentage=(
                str(stats_map.get("Passes %")).replace("%", "")
                if stats_map.get("Passes %")
                else None
            ),
            expected_goals=(
                float(expected_goals_value)
                if expected_goals_value is not None
                else None
            ),
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(new_fixture_stat)
