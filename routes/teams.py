from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, case, literal_column
from sqlalchemy.orm import joinedload, selectinload
from models.league import League
from database.database import get_db_session
from models.fixture import Fixture
from models.league_team import LeagueTeam
from models.base_team import BaseTeam
from models.fixture_lineup import FixtureLineup
from models.fixture_player_stat import FixturePlayerStat
from models.user import User
from collections import defaultdict

router = APIRouter(tags=["Teams"])

@router.get("/teams")
async def get_teams(user_id: int | None = None, session: AsyncSession = Depends(get_db_session)):

    favorite_team = None

    if user_id:
        result = await session.execute(
            select(User)
            .options(joinedload(User.favorite_team))
            .where(User.id == user_id)
        )

        user = result.scalar_one_or_none()

        favorite_team = user.favorite_team if user else None
    
    if(favorite_team):
        result = await session.execute(
            select(BaseTeam).where(BaseTeam.api_id != favorite_team.api_id)
        )
    else:
        result = await session.execute(
            select(BaseTeam)
        )

    teams = result.scalars().all()

    return {
        "favorite_team": {
            "id": favorite_team.api_id,
            "name": favorite_team.name,
            "logo": favorite_team.logo_url,
            "is_favorite": True
        } if favorite_team else [],
        "teams": [
            {
                "id": team.api_id,
                "name": team.name,
                "logo": team.logo_url,
                "is_favorite": favorite_team and team.api_id == favorite_team.api_id
            }
            for team in teams
        ]
    }


@router.get("/teams/{team_id}")
async def get_team_details(team_id: int, user_id: int | None = None, session: AsyncSession = Depends(get_db_session)):


    # Fetch basic team info
    if(user_id):
        stmt = (
            select(BaseTeam, case(
                (User.id != None, True),
                else_=False
            ).label("is_favorite"))
            .options(
                joinedload(BaseTeam.country)
            )
            .outerjoin(User, (BaseTeam.api_id == User.favorite_team_api_id) & (User.id == user_id))
            .where(BaseTeam.api_id == team_id)
        )
    else:
        stmt = (
            select(BaseTeam, literal_column("false").label("is_favorite"))
            .options(
                joinedload(BaseTeam.country)
            )
            .where(BaseTeam.api_id == team_id)
        )

    result = await session.execute(stmt)
    row = result.first()

    team, is_favorite = row

    if not team:
        raise HTTPException(status_code=404, detail="Time não encontrado")

    # Get all league teams IDs for this base team
    result = await session.execute(
        select(LeagueTeam)
        .options(selectinload(LeagueTeam.venue))
        .join(League)
        .where(LeagueTeam.base_team_api_id == team_id)
        .order_by(League.season.desc())
    )
    league_teams = result.scalars().all()
    
    if not league_teams:
        raise HTTPException(status_code=404, detail="Não foram encontradas competições para esse time")

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
                        select(FixtureLineup)
                        .join(Fixture)
                        .filter(FixtureLineup.league_team_id == league_teams[0].id)
                        .order_by(Fixture.date.desc())
                        .options(joinedload(FixtureLineup.coach)))
    latest_lineup = result.scalars().first()

    if latest_lineup:
        result = await session.execute( 
                        select(FixturePlayerStat)
                        .filter_by(fixture_id=latest_lineup.fixture_id, league_team_id=league_teams[0].id)
                        .options(joinedload(FixturePlayerStat.player))
                        )

        players_stats = result.scalars().all()

        squad = defaultdict(list)
        for stat in players_stats:
            player = stat.player
            position = (stat.position or '').lower()
            if position == 'g':
                key = 'goalkeeper'
            elif position == 'd':
                key = 'defensor'
            elif position == 'm':
                key = 'mid_field'
            elif position == 'f':
                key = 'attacker'
            else:
                key = 'mid_field'  # fallback to midfield if unclear

            squad[key].append({
                "id": player.api_id,
                "player": player.name,
                "playerImage": player.photo_url
            })

        coach = latest_lineup.coach

        latest_players = {
            "coach": coach.name if coach else None,
            "coach_imagem": coach.photo_url if coach else None,
            "goalkeeper": squad["goalkeeper"],
            "defensor": squad["defensor"],
            "mid_field": squad["mid_field"],
            "attacker": squad["attacker"]
        }

    else: latest_players = []


    return {
        "team": {
            "id": team.api_id,
            "name": team.name,
            "logo": team.logo_url,
            "founded": team.founded,
            "code": team.code,
            "country": team.country.name,
            "country_flag": team.country.flag_url,
            "is_favorite": is_favorite,
        },
        "team_venue": {
            "address": team_venue.address,
            "name": team_venue.name,
            "city": team_venue.city,
            "capacity": team_venue.capacity,
            "surface": team_venue.surface,
            "image_url": team_venue.image_url,
        } if team_venue else None,
        "leagues": [{"id": l.id, "name": l.name, "season": l.season, "logo_url": l.logo_url} for l in leagues],
        "last_matches": [
            {
                "id": f.api_id,
                "date": f.date.isoformat() if f.date else None,
                "home_team": {
                    "name": f.home_team.team.name,
                    "logo": f.home_team.team.logo_url,
                    "score": f.home_team_score_goals,
                } if f.home_team and f.home_team.team else None,
                "away_team": {
                    "name": f.away_team.team.name,
                    "logo": f.away_team.team.logo_url,
                    "score": f.away_team_score_goals,
                } if f.away_team and f.away_team.team else None,
            }
            for f in fixtures
        ],
        "players": latest_players,
    }

@router.get("/teams-mock")
async def get_mock_team():
    # Mock player object
    mock_player = {
        "player": "Omar Ammar",
        "playerImage": "https://media.api-sports.io/football/players/2659.png"
    }

    # Mock coach
    mock_coach = {
        "coach": "Mock Coach",
        "coach_imagem": "https://media.api-sports.io/football/coaches/1.png"
    }

    # Construct mock players in positions
    latest_players = {
        **mock_coach,
        "goalkeeper": [mock_player],
        "defensor": [mock_player] * 4,
        "mid_field": [mock_player] * 4,
        "attacker": [mock_player] * 4
    }

    # Static data (Bahia etc.)
    return {
        "team": {
            "id": 118,
            "name": "Bahia",
            "logo": "https://media.api-sports.io/football/teams/118.png",
            "founded": 1931
        },
        "team_venue": {
            "id": 216,
            "name": "Arena Fonte Nova",
            "city": "Salvador, Bahia",
            "capacity": 56500,
            "surface": "grass",
            "image_url": "https://media.api-sports.io/football/venues/216.png"
        },
        "leagues": [
            {
                "id": 1,
                "name": "Serie A"
            }
        ],
        "last_matches": [
            {
                "id": 1006027,
                "date": "2023-12-07T00:30:00",
                "home_team": {
                    "id": 118,
                    "name": "Bahia",
                    "logo": "https://media.api-sports.io/football/teams/118.png"
                },
                "away_team": {
                    "id": 1062,
                    "name": "Atletico-MG",
                    "logo": "https://media.api-sports.io/football/teams/1062.png"
                },
                "home_score": 4,
                "away_score": 1
            },
            {
                "id": 1006018,
                "date": "2023-12-03T21:30:00",
                "home_team": {
                    "id": 125,
                    "name": "America Mineiro",
                    "logo": "https://media.api-sports.io/football/teams/125.png"
                },
                "away_team": {
                    "id": 118,
                    "name": "Bahia",
                    "logo": "https://media.api-sports.io/football/teams/118.png"
                },
                "home_score": 3,
                "away_score": 2
            },
            {
                "id": 1006007,
                "date": "2023-11-29T23:00:00",
                "home_team": {
                    "id": 118,
                    "name": "Bahia",
                    "logo": "https://media.api-sports.io/football/teams/118.png"
                },
                "away_team": {
                    "id": 126,
                    "name": "Sao Paulo",
                    "logo": "https://media.api-sports.io/football/teams/126.png"
                },
                "home_score": 0,
                "away_score": 1
            }
        ],
        "players": latest_players
    }