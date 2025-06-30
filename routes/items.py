from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.orm import selectinload
from database.database import get_db_session
from schemas import LeagueResponse, PlayerResponse
from models.league import League
from models.user_favorite_league import UserFavoriteLeague
from models.base_player import BasePlayer
from models.user import User
from models.base_team import BaseTeam
from models.user_favorite_player import UserFavoritePlayer


router = APIRouter(tags=["All Items"])

@router.get("/items")
async def get_all_items(user_id: int | None = None, session: AsyncSession = Depends(get_db_session)):

    favorite_league_ids = set()
    favorite_players_ids = set()
    favorite_leagues_response = []
    favorite_players_response = []

    if user_id:
        #get user
        stmt = (
            select(User)
            .options(
                selectinload(User.favorite_player_associations).selectinload(UserFavoritePlayer.player),
                selectinload(User.favorite_team),
            )
            .where(User.id == user_id)
        )

        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")

        # get favorite leagues
        stmt = (
            select(League)
            .join(UserFavoriteLeague, League.api_id == UserFavoriteLeague.api_league_id)
            .where(UserFavoriteLeague.user_id == user_id)
        )
        result = await session.execute(stmt)
        favorite_leagues = result.scalars().all()

        favorite_league_ids = {league.id for league in favorite_leagues}
        favorite_players_ids = {player.api_id for player in user.favorite_players}

        favorite_players_response = [
            PlayerResponse(
                id=player.api_id,
                name=player.name,
                photo=player.photo_url,
                is_favorite=True
            )
            for player in user.favorite_players
        ]

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
        

    #get all leagues
    if favorite_league_ids:
        stmt = select(League).where(~League.id.in_(favorite_league_ids))
    else:
        stmt = select(League)
        
    result = await session.execute(stmt)
    leagues = result.scalars().all()


    #get all teams
    if(user_id and user.favorite_team):
        result = await session.execute(
            select(BaseTeam).where(BaseTeam.api_id != user.favorite_team.api_id)
        )
    else:
        result = await session.execute(
            select(BaseTeam)
        )

    teams = result.scalars().all()
        

    #get all players
    if favorite_players_ids:
        stmt = select(BasePlayer).where(~BasePlayer.api_id.in_(favorite_players_ids)).limit(20).offset(1074)
    else:
        stmt = select(BasePlayer).limit(20).offset(1074)
        
    result = await session.execute(stmt)
    players = result.scalars().all()

    all_leagues_response = [
        LeagueResponse(
            id=league.id,
            name=league.name,
            season=league.season,
            logo_url=league.logo_url,
            api_id=league.api_id,
            is_favorite=False
        )
        for league in leagues
    ]

    all_players_response = [
        PlayerResponse(
            id=player.api_id,
            name=player.name,
            photo=player.photo_url,
            is_favorite=False
        )
        for player in players
    ]

    response = {
        "favorite_leagues": favorite_leagues_response,
        "all_leagues": all_leagues_response,
        "favorite_team": [{
            "id": user.favorite_team.api_id,
            "name": user.favorite_team.name,
            "logo": user.favorite_team.logo_url,
            "is_favorite": True
        }] if user_id and user.favorite_team else [],
        "all_teams": [
            {
                "id": team.api_id,
                "name": team.name,
                "logo": team.logo_url,
                "is_favorite": False
            }
            for team in teams
        ],
        "favorite_players": favorite_players_response,
        "all_players": all_players_response
    }

    return response


@router.get("/user/favorites")
async def get_favorites(user_id: int, session: AsyncSession = Depends(get_db_session)):

    stmt = (
        select(User)
        .options(
            selectinload(User.favorite_player_associations).selectinload(UserFavoritePlayer.player),
            selectinload(User.favorite_team),
        )
        .where(User.id == user_id)
    )

    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(status_code=404, detail="Usuário não encontrado")

    #favorite players by proxy
    favorite_players = [
        {
            "id": p.api_id,
            "name": p.name,
            "age": p.age,
            "photo": p.photo_url
        } for p in user.favorite_players
    ]

    #get favorite leagues
    league_assoc_stmt = (
        select(League)
        .join(UserFavoriteLeague, League.api_id == UserFavoriteLeague.api_league_id)
        .where(UserFavoriteLeague.user_id == user_id)
    )
    league_assoc_result = await session.execute(league_assoc_stmt)
    favorite_leagues_values = league_assoc_result.scalars().all()

    #load favorite leagues
    favorite_leagues = []
    for league in favorite_leagues_values:
        favorite_leagues.append({
            "id": league.id,
            "name": league.name,
            "season": league.season,
            "logo_url": league.logo_url,
            "api_id": league.api_id
        })

    #favorite team
    favorite_team = None
    if user.favorite_team:
        favorite_team = {
            "id": user.favorite_team.api_id,
            "name": user.favorite_team.name,
            "logo": user.favorite_team.logo_url,
        }

    return {
        "favorite_players": favorite_players,
        "favorite_leagues": favorite_leagues,
        "favorite_team": favorite_team
    }