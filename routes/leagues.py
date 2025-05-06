from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models.league import League
from database.database import get_db_session
from schemas import LeagueResponse, MatchResponse, TeamInfo
from typing import List
from models.fixture import Fixture
from models.league_team import LeagueTeam

router = APIRouter()


@router.get("/leagues", response_model=List[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db_session)):
    
    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()
    print(leagues)
    return leagues


@router.get("/matches", response_model=List[MatchResponse])
async def get_completed_matches(league_id: int = Query(...), db: AsyncSession = Depends(get_db_session)):
    stmt = (
        select(Fixture)
        .where(Fixture.league_id == league_id)
        .options(
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team)
        )
    )

    result = await db.execute(stmt)
    fixtures = result.scalars().all()

    matches = []
    for fixture in fixtures:
        home = fixture.home_team.team
        away = fixture.away_team.team

        match = MatchResponse(
            home_team=TeamInfo(
                score=fixture.home_team_score_goals,
                logo=home.logo_url,
                name=home.name
            ),
            away_team=TeamInfo(
                score=fixture.away_team_score_goals,
                logo=away.logo_url,
                name=away.name
            ),
            timestamp_match=fixture.date
        )
        matches.append(match)

    return matches