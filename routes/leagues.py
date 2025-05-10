from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import joinedload
from models.league import League
from database.database import get_db_session
from schemas import LeagueResponse, MatchResponse, TeamInfo
from typing import List, Dict
from models.fixture import Fixture
from models.league_team import LeagueTeam
from datetime import datetime

router = APIRouter()


@router.get("/leagues", response_model=List[LeagueResponse])
async def get_leagues(db: AsyncSession = Depends(get_db_session)):
    
    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()
    print(leagues)
    return leagues


@router.get("/matches", response_model=Dict[datetime, List[MatchResponse]])
async def get_completed_matches(round: str | None, id: int, season: int, db: AsyncSession = Depends(get_db_session)):

    if not round:
        round = '1'

    round = f"Regular Season - {round}"

    stmt = (
        select(Fixture)
        .where(Fixture.league_id == id, Fixture.season == season, Fixture.round == round)
        .options(
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team)
        )
    )

    result = await db.execute(stmt)
    fixtures = result.scalars().all()

    matches = defaultdict(list)
    for fixture in fixtures:
        home = fixture.home_team.team
        away = fixture.away_team.team
        date = fixture.date.date()

        match = MatchResponse(
            id = fixture.api_id,
            home_team = TeamInfo(
                score = fixture.home_team_score_goals,
                logo = home.logo_url,
                name = home.name
            ),
            away_team = TeamInfo(
                score = fixture.away_team_score_goals,
                logo = away.logo_url,
                name = away.name
            ),
            time = f"{fixture.date.time()}"
        )

        matches[date].append(match)

    return matches