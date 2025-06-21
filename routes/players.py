from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import List

from database.database import get_db_session
from models.base_player import BasePlayer
from models.country import Country
from models.player_season_stat import PlayerSeasonStat
from models.league_team import LeagueTeam
from models.base_team import BaseTeam
from models.league import League
from schemas import PlayerProfileResponse, TeamParticipation, PlayerTeamInfo, CountryInfo, TeamInfo, CompetitionInfo

router = APIRouter(tags=["Players"])

@router.get("/players/{player_id}", response_model=PlayerProfileResponse)

@router.get("/players/{player_id}", response_model=PlayerProfileResponse)
async def get_player_profile(player_id: int, db: AsyncSession = Depends(get_db_session)):
    # Get player and their nationality/birth country
    stmt = (
        select(BasePlayer)
        .options(
            joinedload(BasePlayer.nationality),
            joinedload(BasePlayer.birth_country),
        )
        .where(BasePlayer.api_id == player_id)
    )
    result = await db.execute(stmt)
    player: BasePlayer | None = result.scalar_one_or_none()

    if not player:
        raise HTTPException(status_code=404, detail="Player not found")

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
                'goalkeeper' if pos == 'g' else
                'defensor' if pos == 'd' else
                'mid_field' if pos == 'm' else
                'attacker'
            )
        break

    # Assemble response
    response = PlayerProfileResponse(
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
        teams=list(teams_dict.values())
    )

    return response