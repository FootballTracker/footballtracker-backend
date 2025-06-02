from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, literal_column
from sqlalchemy.orm import joinedload
from database.database import get_db_session
from schemas import LeagueResponse, MatchResponse, TeamInfo, SeasonResponse
from typing import List, Dict, Union
from models.league import League
from models.user_favorite_league import UserFavoriteLeague
from models.fixture import Fixture
from models.league_team import LeagueTeam

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
            .join(UserFavoriteLeague, League.api_id == UserFavoriteLeague.api_league_id)
            .where(UserFavoriteLeague.user_id == user_id)
        )
        result = await db.execute(stmt)
        favorite_leagues = result.scalars().all()
        favorite_league_ids = {league.id for league in favorite_leagues}

    stmt = select(League)
    result = await db.execute(stmt)
    leagues = result.scalars().all()

    favorite_leagues_response = [
        LeagueResponse(
            id=league.id,
            name=league.name,
            season=league.season,
            logo_url=league.logo_url,
            api_id=league.api_id,
            is_favorite=True
        )
        for league in favorite_leagues
    ]

    all_leagues_response = [
        LeagueResponse(
            id=league.id,
            name=league.name,
            season=league.season,
            logo_url=league.logo_url,
            api_id=league.api_id,
            is_favorite=league.id in favorite_league_ids
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
        .join(UserFavoriteLeague, League.api_id == UserFavoriteLeague.api_league_id)
        .where(UserFavoriteLeague.user_id == user_id)
    )
    result = await db.execute(stmt)
    favorite_leagues = result.scalars().all()

    favorite_leagues_response = [
        LeagueResponse(
            id=league.id,
            name=league.name,
            season=league.season,
            logo_url=league.logo_url,
            api_id=league.api_id,
            is_favorite=True
        )
        for league in favorite_leagues
    ]

    return favorite_leagues_response

@router.get("/league", response_model=Dict[str, Union[List[SeasonResponse], LeagueResponse]])
async def get_league(
    league_id: int,
    user_id: int | None = None,
    db: AsyncSession = Depends(get_db_session),
):

    if(user_id):
        stmt = select(League, case(
                    (UserFavoriteLeague.user_id != None, True),
                    else_=False
                ).label("is_favorite")
            ).outerjoin(UserFavoriteLeague, (League.api_id == UserFavoriteLeague.api_league_id) & (UserFavoriteLeague.user_id == user_id)
            ).where(League.id == league_id)
    else:
        stmt = select(League, literal_column("false").label("is_favorite")).where(League.id == league_id)

    result = await db.execute(stmt)
    row = result.first()

    league, is_favorite = row

    league_response = LeagueResponse(
        id=league.id,
        name=league.name,
        season=league.season,
        logo_url=league.logo_url,
        api_id=league.api_id,
        is_favorite=is_favorite
    )

    stmt = select(League.id, League.season).where(League.api_id == league.api_id)
    result = await db.execute(stmt)
    league_seasons = result.all()

    seasons_response: List[SeasonResponse] = []

    for s in league_seasons:
        new_season = SeasonResponse(
            id = s.id,
            season = s.season
        )

        seasons_response.append(new_season)

    return {
        "league": league_response,
        "seasons": seasons_response
    }

@router.get(
    "/matches",
    response_model=List[MatchResponse]
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
        .order_by(Fixture.date)
    )

    result = await db.execute(stmt)
    fixtures = result.scalars().all()

    matches = []
    for fixture in fixtures:
        home = fixture.home_team.team
        away = fixture.away_team.team

        match = MatchResponse(
            id=fixture.api_id,
            home_team=TeamInfo(
                score=fixture.home_team_score_goals, logo=home.logo_url, name=home.name
            ),
            away_team=TeamInfo(
                score=fixture.away_team_score_goals, logo=away.logo_url, name=away.name
            ),
            date=fixture.date,
        )

        matches.append(match)

    return matches
