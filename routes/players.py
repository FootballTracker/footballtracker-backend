from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc, insert
from sqlalchemy.orm import joinedload, selectinload
from typing import List, Dict

from database.database import get_db_session
from models.base_player import BasePlayer
from models.country import Country
from models.player_season_stat import PlayerSeasonStat
from models.league_team import LeagueTeam
from models.base_team import BaseTeam
from models.league import League
from models.user import User
from models.user_favorite_player import UserFavoritePlayer
from models.fixture_player_stat import FixturePlayerStat
from models.fixture import Fixture
from models.fixture_lineup import FixtureLineup
from schemas import (
    PlayerProfileResponse,
    TeamParticipation,
    PlayerTeamInfo,
    CountryInfo, TeamInfo,
    CompetitionInfo,
    Rank,
    Rankings, PlayerResponse,
    UserFavoritePlayerData
)

router = APIRouter(tags=["Players"])

@router.get("/players", response_model=Dict[str, List[PlayerResponse]])
async def get_players(
    user_id: int | None = None, text: str | None = None, session: AsyncSession = Depends(get_db_session)
):

    if text:
        stmt = select(BasePlayer).where(BasePlayer.name.icontains(text.lower()))

        result = await session.execute(stmt)
        players = result.scalars().all()

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
            "all_players": all_players_response
        }
        
    else:
        favorite_players_ids = set()
        favorite_players: list[BasePlayer] = []

        if user_id:
            stmt = (
                select(BasePlayer)
                .join(UserFavoritePlayer, BasePlayer.api_id == UserFavoritePlayer.player_api_id)
                .where(UserFavoritePlayer.user_id == user_id)
            )
            result = await session.execute(stmt)
            favorite_players = result.scalars().all()
            favorite_players_ids = {player.api_id for player in favorite_players}
            

        if favorite_players_ids:
            stmt = select(BasePlayer).where(~BasePlayer.api_id.in_(favorite_players_ids)).limit(20).offset(1074)
        else:
            stmt = select(BasePlayer).limit(20).offset(1074)
            
        result = await session.execute(stmt)
        players = result.scalars().all()

        favorite_players_response = [
            PlayerResponse(
                id=player.api_id,
                name=player.name,
                photo=player.photo_url,
                is_favorite=True
            )
            for player in favorite_players
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
            "favorite_players": favorite_players_response,
            "all_players": all_players_response
        }

    return response

@router.post("/player/favorite")
async def favorite_player(data: UserFavoritePlayerData, session: AsyncSession = Depends(get_db_session)):

    result = await session.execute(
        select(User)
        .where(User.id == data.user_id)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, detail="Usuário não encontrado")
    
    result = await session.execute(
        select(BasePlayer)
        .where(BasePlayer.api_id == data.player_id)
    )

    player = result.scalar_one_or_none()

    if not player:
        raise HTTPException(404, detail="Jogador não encontrado")
    

    result = await session.execute(
        select(UserFavoritePlayer)
        .where((UserFavoritePlayer.user_id == data.user_id) & (UserFavoritePlayer.player_api_id == data.player_id))
    )

    favorite_player = result.scalars().all()

    if favorite_player:
        await session.delete(favorite_player[0])
    else:
        await session.execute(
            insert(UserFavoritePlayer).values(user_id = data.user_id, player_api_id = data.player_id)
        )
    await session.commit()

    return {
        "message": "Jogador favoritado/desfavoritado"
    }


@router.get("/players/rankings", response_model=Rankings)
async def get_player_rankings(db: AsyncSession = Depends(get_db_session)):
    async def get_top_players(order_by_column, label: str, limit: int = 10):
        stmt = (
            select(
                PlayerSeasonStat,
                BasePlayer.name.label("player_name"),
                BasePlayer.api_id.label("player_id"),
                BaseTeam.api_id.label("team_id"),
                order_by_column.label("value")
            )
            .join(BasePlayer, BasePlayer.api_id == PlayerSeasonStat.base_player_api_id)
            .join(LeagueTeam, LeagueTeam.id == PlayerSeasonStat.league_team_id)
            .join(BaseTeam, BaseTeam.api_id == LeagueTeam.base_team_api_id)
            .where(order_by_column != None)
            .order_by(desc(order_by_column))
            .limit(limit)
        )
        result = await db.execute(stmt)
        return [
            Rank(
                id=str(row.player_id),
                name=row.player_name,
                value=float(row.value),
                teamId=str(row.team_id)
            )
            for row in result.all()
        ]

    top_goals = await get_top_players(PlayerSeasonStat.goals, "goals")
    top_assists = await get_top_players(PlayerSeasonStat.assists, "assists")
    top_ratings = await get_top_players(PlayerSeasonStat.rating, "avgScores")

    return Rankings(
        goals=top_goals,
        assists=top_assists,
        avgScores=top_ratings
    )

@router.get("/players/{player_id}", response_model=PlayerProfileResponse)
async def get_player_profile(player_id: int, user_id: int | None = None, db: AsyncSession = Depends(get_db_session)):
    # Get player and their nationality/birth country
    if user_id:
        stmt = (
            select(BasePlayer, case(
                (UserFavoritePlayer.user_id != None, True),
                else_=False
            ).label("is_favorite"))
            .options(
                joinedload(BasePlayer.nationality),
                joinedload(BasePlayer.birth_country),
            )
            .outerjoin(UserFavoritePlayer, (BasePlayer.api_id == UserFavoritePlayer.player_api_id) & (UserFavoritePlayer.user_id == user_id))
            .where(BasePlayer.api_id == player_id)
        )
    else:
        stmt = (
            select(BasePlayer, literal_column("false").label("is_favorite"))
            .options(
                joinedload(BasePlayer.nationality),
                joinedload(BasePlayer.birth_country),
            )
            .where(BasePlayer.api_id == player_id)
        )
    result = await db.execute(stmt)
    row = result.first()

    if not row:
        raise HTTPException(status_code=404, detail="Player not found")
    
    player, is_favorite = row

    # Get all teams and competitions the player participated in
    stmt = (
        select(PlayerSeasonStat)
        .join(LeagueTeam, LeagueTeam.id == PlayerSeasonStat.league_team_id)
        .join(BaseTeam, BaseTeam.api_id == LeagueTeam.base_team_api_id)
        .join(League, League.id == LeagueTeam.league_id)
        .where(PlayerSeasonStat.base_player_api_id == player_id)
        .options(
            joinedload(PlayerSeasonStat.league_team).joinedload(LeagueTeam.team),
            joinedload(PlayerSeasonStat.league_team).joinedload(LeagueTeam.league),
        )
    )
    result = await db.execute(stmt)
    participations: List[PlayerSeasonStat] = result.scalars().all()

    # Process participations
    teams_dict = {}
    for p in participations:
        league = p.league_team.league
        team = p.league_team.team

        key = team.api_id
        if key not in teams_dict:
            teams_dict[key] = TeamParticipation(
                team=PlayerTeamInfo(id=team.api_id, name=team.name, logo=team.logo_url),
                competitions=[]
            )

        competition = CompetitionInfo(id=league.id, name=league.name, logo=league.logo_url, season=league.season)
        if competition not in teams_dict[key].competitions:
            teams_dict[key].competitions.append(competition)

    # Get position (first non-null)
    position = None
    for stat in participations:
        pos = (stat.position or '').lower()
        if pos in ['g', 'd', 'm', 'f']:
            position = (
                'Goleiro' if pos == 'g' else
                'Defensor' if pos == 'd' else
                'Meia' if pos == 'm' else
                'Atacante'
            )
        break

    # Assemble response
    response = PlayerProfileResponse(
        id=player.api_id,
        name=player.name,
        firstname=player.firstname,
        lastname=player.lastname,
        birth_date=player.birth_date,
        birth_place=player.birth_place,
        height=player.height,
        weight=player.weight,
        injured=player.injured,
        photo_url=player.photo_url,
        position=position,
        birth_country=CountryInfo(
            name=player.birth_country.name,
            flag_url=player.birth_country.flag_url
        ) if player.birth_country else None,
        nationality=CountryInfo(
            name=player.nationality.name,
            flag_url=player.nationality.flag_url
        ) if player.nationality else None,
        teams=list(teams_dict.values()),
        is_favorite=is_favorite
    )

    return response

@router.get("/player/{player_id}/team/{team_id}/league/{league_id}/stats")
async def get_player_stats(player_id: int, team_id: int, league_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(
            PlayerSeasonStat, League, BaseTeam
        ).join(
            LeagueTeam, PlayerSeasonStat.league_team_id == LeagueTeam.id
        ).join(
            League, LeagueTeam.league_id == League.id
        ).join_from(
            LeagueTeam, BaseTeam, LeagueTeam.base_team_api_id == BaseTeam.api_id
        ).where(
            (PlayerSeasonStat.base_player_api_id == player_id) & (LeagueTeam.league_id == league_id) & (LeagueTeam.base_team_api_id == team_id)
        )
    )

    player_stats, league, team = result.one_or_none()

    if not player_stats:
        raise HTTPException(404, {
            "message": "Estatísticas do jogador não disponíveis para essa liga",
            "ok": True
        })
    
    player_stats.position = player_stats.position.upper()
    if player_stats.position == "F":
        player_stats.position = "Atacante"
    elif player_stats.position == "D":
        player_stats.position = "Defensor"
    elif player_stats.position == "G":
        player_stats.position = "Goleiro"
    else:
        player_stats.position = "Meia"

    return {
        "player_stats": player_stats,
        "league": league,
        "team": team
    }

@router.get("/match/missing/players")
async def get_missing_players_from_match(session: AsyncSession = Depends(get_db_session)):

    result = await session.execute(
        select(Fixture)
        .options(
            selectinload(Fixture.lineups).joinedload(FixtureLineup.coach),
            selectinload(Fixture.player_stats).joinedload(FixturePlayerStat.player),
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team)
        )
    )

    matches = result.scalars().all()
    if not matches:
        raise HTTPException(404, detail="Partida não encontrada")
    

    found = False
    for match in matches:

        home_league_team_id = match.home_team_id

        partial_initial_home_players: List[FixturePlayerStat] = []
        partial_initial_away_players: List[FixturePlayerStat] = []

        for player_stat in match.player_stats:

            if player_stat.is_starter:
                if player_stat.league_team_id == home_league_team_id:
                    partial_initial_home_players.append(player_stat)
                else:
                    partial_initial_away_players.append(player_stat)

        if len(partial_initial_home_players) < 11 or len(partial_initial_away_players) < 11:
            found = True
            print(f"Partida: {match.api_id}.\
                  Home: {match.home_team.team.name} {len(partial_initial_home_players)}.\
                  Away: {match.away_team.team.name} {len(partial_initial_away_players)}\
                  \tRound: {match.round} \n\n")

    if found:
        return {
            "message": "missing players found. see logs"
        }
    
    return {
        "message": "no missing players found"
    }

# trocar jogador de id 305833 por id 374356 na partida 1005670. Arrumar estatisticas e eventos da partida. Jogador 374356: is_starter = true, grid = 3:1
# partida de id 1005689 faltando diversos jogadores na lineup