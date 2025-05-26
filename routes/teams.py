from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload, selectinload
from models.league import League
from models.user_favorite_league import UserFavoriteLeague
from database.database import get_db_session
from schemas import LeagueResponse, MatchResponse, TeamInfo
from typing import List, Dict, Union
from models.fixture import Fixture
from models.league_team import LeagueTeam
from models.base_team import BaseTeam
from models.player_season_stat import PlayerSeasonStat
from datetime import date, timedelta

router = APIRouter(tags=["Teams"])

@router.get("/teams/{team_id}")
async def get_team_details(team_id: int, session: AsyncSession = Depends(get_db_session)):
    # Fetch basic team info
    result = await session.execute(
        select(BaseTeam).where(BaseTeam.api_id == team_id)
    )
    team = result.scalar_one_or_none()
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get all league teams IDs for this base team
    result = await session.execute(
        select(LeagueTeam)
        .options(selectinload(LeagueTeam.venue))
        .where(LeagueTeam.base_team_api_id == team_id)
    )
    league_teams = result.scalars().all()
    if not league_teams:
        raise HTTPException(status_code=404, detail="No league teams found for this team")

    league_team_ids = [lt.id for lt in league_teams]

    # Get the team venue (take venue from any league team if exists)
    team_venue = None
    for lt in league_teams:
        if lt.venue:
            team_venue = lt.venue
            break

    # Fetch leagues the team is in
    league_ids = [lt.league_id for lt in league_teams]
    result = await session.execute(
        select(League).where(League.id.in_(league_ids))
    )
    leagues = result.scalars().all()

    # Fetch last 3 fixtures involving the team with eager loading for teams and base teams
    result = await session.execute(
        select(Fixture)
        .options(
            selectinload(Fixture.home_team).selectinload(LeagueTeam.team),
            selectinload(Fixture.away_team).selectinload(LeagueTeam.team),
        )
        .where(
            (Fixture.home_team_id.in_(league_team_ids)) | (Fixture.away_team_id.in_(league_team_ids))
        )
        .order_by(Fixture.api_id.desc())
        .limit(3)
    )
    fixtures = result.scalars().all()

    # Fetch all PlayerSeasonStats for the team
    result = await session.execute(
        select(PlayerSeasonStat)
        .options(selectinload(PlayerSeasonStat.player))
        .where(PlayerSeasonStat.league_team_id.in_(league_team_ids))
    )
    stats = result.scalars().all()
    print(stats)
    # Find latest update date among the player's stats
    latest_update = max([s.last_updated for s in stats if s.last_updated], default=None)

    # Filter player stats for latest season only
    latest_players = [
        {
            "id": stat.player.api_id,
            "name": stat.player.name,
            "position": stat.position,
            "goals": stat.goals,
            "assists": stat.assists,
        }
        for stat in stats
        if stat.last_updated == latest_update
    ]

    return {
        "team": {
            "id": team.api_id,
            "name": team.name,
            "logo": team.logo_url,
            "founded": team.founded,
        },
        "team_venue": {
            "id": team_venue.api_id,
            "name": team_venue.name,
            "city": team_venue.city,
            "capacity": team_venue.capacity,
            "surface": team_venue.surface,
            "image_url": team_venue.image_url,
        } if team_venue else None,
        "leagues": [{"id": l.id, "name": l.name} for l in leagues],
        "last_matches": [
            {
                "id": f.api_id,
                "date": f.date.isoformat() if f.date else None,
                "home_team": {
                    "id": f.home_team.team.api_id,
                    "name": f.home_team.team.name,
                    "logo": f.home_team.team.logo_url,
                } if f.home_team and f.home_team.team else None,
                "away_team": {
                    "id": f.away_team.team.api_id,
                    "name": f.away_team.team.name,
                    "logo": f.away_team.team.logo_url,
                } if f.away_team and f.away_team.team else None,
                "home_score": f.home_team_score_goals,
                "away_score": f.away_team_score_goals,
            }
            for f in fixtures
        ],
        "players": latest_players,
    }
