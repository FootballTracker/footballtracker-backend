from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import case, literal_column
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, desc
from sqlalchemy.orm import joinedload
from typing import List

from database.database import get_db_session
from models.base_player import BasePlayer
from models.country import Country
from models.player_season_stat import PlayerSeasonStat
from models.league_team import LeagueTeam
from models.base_team import BaseTeam
from models.league import League
from models.user_favorite_player import UserFavoritePlayer
from schemas import PlayerProfileResponse, TeamParticipation, PlayerTeamInfo, CountryInfo, TeamInfo, CompetitionInfo, Rank, Rankings

router = APIRouter(tags=["Players"])


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

        competition = CompetitionInfo(id=league.id, name=league.name)
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

