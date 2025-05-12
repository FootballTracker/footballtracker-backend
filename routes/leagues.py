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

router = APIRouter(tags=["Leagues"])


@router.get("/leagues", response_model=Dict[str, List[LeagueResponse]])
async def get_leagues(
    user_id: int | None = None, db: AsyncSession = Depends(get_db_session)
):

    favorite_league_ids = set()
    favorite_leagues: list[League] = []

    if user_id:
        stmt = (
            select(League)
            .join(UserFavoriteLeague)
            .where(UserFavoriteLeague.user_id == user_id)
        )
        result = await db.execute(stmt)
        favorite_leagues = result.scalars().all()
        favorite_league_ids = {league.id for league in favorite_leagues}

    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()

    favorite_leagues_response = [
        LeagueResponse.model_validate(league, from_attributes=True).model_copy(
            update={"favorita": True}
        )
        for league in favorite_leagues
    ]

    all_leagues_response = [
        LeagueResponse.model_validate(league, from_attributes=True).model_copy(
            update={"favorita": league.id in favorite_league_ids}
        )
        for league in leagues
    ]

    return {
        "favorite_leagues": favorite_leagues_response,
        "all_leagues": all_leagues_response,
    }


@router.get("/favorite_leagues", response_model=List[LeagueResponse])
async def get_leagues(user_id: int, db: AsyncSession = Depends(get_db_session)):

    favorite_leagues: list[League] = []

    stmt = (
        select(League)
        .join(UserFavoriteLeague)
        .where(UserFavoriteLeague.user_id == user_id)
    )
    result = await db.execute(stmt)
    favorite_leagues = result.scalars().all()

    favorite_leagues_response = [
        LeagueResponse.model_validate(league, from_attributes=True).model_copy(
            update={"favorita": True}
        )
        for league in favorite_leagues
    ]

    return favorite_leagues_response


@router.get("/league", response_model=Dict[str, Union[List[int], LeagueResponse]])
async def get_league(
    league_id: int,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
):

    favorite_league_ids = set()

    stmt = select(League).where(League.id == league_id)
    result = await db.execute(stmt)
    league = result.scalar_one_or_none()

    if user_id:
        stmt = select(League).where(UserFavoriteLeague.user_id == user_id)
        result = await db.execute(stmt)
        favorite_leagues = result.scalars().all()
        favorite_league_ids = {league.id for league in favorite_leagues}

    league_response = LeagueResponse.model_validate(
        league, from_attributes=True
    ).model_copy(update={"favorita": league.id in favorite_league_ids})

    stmt = select(League.season).where(League.api_id == league.api_id)
    result = await db.execute(stmt)
    seasons = result.scalars().all()

    return {"league": league_response, "seasons": seasons}


@router.get(
    "/matches", response_model=List[Dict[str, Union[date, List[MatchResponse]]]]
)
async def get_completed_matches(
    round: str | None, id: int, season: int, db: AsyncSession = Depends(get_db_session)
):

    if not round:
        round = "1"

    round = f"Regular Season - {round}"

    stmt = (
        select(Fixture)
        .where(
            Fixture.league_id == id, Fixture.season == season, Fixture.round == round
        )
        .options(
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team),
        )
    )

    result = await db.execute(stmt)
    fixtures = result.scalars().all()

    matches = []
    daysIndex = {}
    for fixture in fixtures:
        home = fixture.home_team.team
        away = fixture.away_team.team
        date = fixture.date - timedelta(hours=3)

        match = MatchResponse(
            id=fixture.api_id,
            home_team=TeamInfo(
                score=fixture.home_team_score_goals, logo=home.logo_url, name=home.name
            ),
            away_team=TeamInfo(
                score=fixture.away_team_score_goals, logo=away.logo_url, name=away.name
            ),
            time=f"{date.time().strftime('%H:%M')}",
        )

        date = date.date()

        if date not in daysIndex:
            daysIndex[date] = len(matches)
            matches.append({"day": date, "matches": []})

        index = daysIndex[date]
        matches[index]["matches"].append(match)

    return matches
