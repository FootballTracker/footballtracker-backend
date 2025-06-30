from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from models.fixture_event import FixtureEvent


async def process_fixture_events(session: AsyncSession, fixture_data: dict):
    print(" Processando eventos...")
    fixture_api_id = fixture_data["fixture"]["id"]

    for event_data in fixture_data.get("events", []):
        new_event = FixtureEvent(
            fixture_api_id=fixture_api_id,
            team_api_id=event_data["team"]["id"],
            player_api_id=event_data.get("player", {}).get("id"),
            assist_player_api_id=event_data.get("assist", {}).get("id"),
            time_elapsed=event_data["time"]["elapsed"],
            time_extra=event_data["time"].get("extra"),
            type=event_data["type"],
            detail=event_data["detail"],
            comments=event_data.get("comments"),
            last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
        )
        session.add(new_event)
