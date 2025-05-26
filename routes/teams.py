from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models.league import League
from models.user_favorite_league import UserFavoriteLeague
from database.database import get_db_session
from schemas import LeagueResponse, MatchResponse, TeamInfo
from typing import List, Dict, Union
from models.fixture import Fixture
from models.league_team import LeagueTeam
from datetime import date, timedelta

router = APIRouter(tags=["Teams"])

@router.get("/teams/{team_id}")
async def get_team_details(team_id: int, session: AsyncSession = Depends(get_async_session)):
    # Fetch basic team info
    result = await session.execute(
        select(BaseTeam).where(BaseTeam.api_id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Fetch leagues the team is in
    result = await session.execute(
        select(League).join(LeagueTeam).where(LeagueTeam.base_team_api_id == team_id)
    )
    leagues = result.scalars().all()

    # Fetch last 5 fixtures involving the team
    result = await session.execute(
        select(Fixture)
        .where((Fixture.home_team_id == team_id) | (Fixture.away_team_id == team_id))
        .order_by(Fixture.api_id.desc())  # assuming higher ID = newer
        .limit(5)
    )
    fixtures = result.scalars().all()

    # Fetch players by season
    result = await session.execute(
        select(PlayersSeasonStats)
        .options(selectinload(PlayersSeasonStats.base_player))
        .where(PlayersSeasonStats.league_team_id.in_(
            select(LeagueTeam.id).where(LeagueTeam.base_team_api_id == team_id)
        ))
    )
    stats = result.scalars().all()

    # Organize players by season
    players_by_season = {}
    for stat in stats:
        season = stat.season
        if season not in players_by_season:
            players_by_season[season] = []
        players_by_season[season].append({
            "id": stat.base_player.api_id,
            "name": stat.base_player.name,
            "position": stat.position,
            "goals": stat.goals,
            "assists": stat.assists
        })

    return {
        "team": {
            "id": team.api_id,
            "name": team.name,
            "logo": team.logo_url
        },
        "leagues": [{"id": l.id, "name": l.name} for l in leagues],
        "last_matches": [
            {
                "id": f.api_id,
                "date": f.date.isoformat() if f.date else None,
                "home_team_id": f.home_team_id,
                "away_team_id": f.away_team_id,
                "home_score": f.home_score,
                "away_score": f.away_score
            } for f in fixtures
        ],
        "players_by_season": players_by_season
    }