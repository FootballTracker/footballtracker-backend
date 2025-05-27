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
from models.fixture_lineup import FixtureLineup
from models.fixture_player_stat import FixturePlayerStat
from datetime import date, timedelta

router = APIRouter(tags=["Teams"])

@router.get("/teams/{team_id}")
async def get_team_details(team_id: int, session: AsyncSession = Depends(get_db_session)):
    # Fetch basic team info
    result = await session.execute(
        select(BaseTeam).where(BaseTeam.api_id == team_id)
    )
    team = result.scalar_one_or_none()
    print("Team: ", team)
    if not team:
        raise HTTPException(status_code=404, detail="Team not found")

    # Get all league teams IDs for this base team
    result = await session.execute(
        select(LeagueTeam)
        .options(selectinload(LeagueTeam.venue))
        .join(League)
        .where(LeagueTeam.base_team_api_id == team_id)
        .order_by(League.season.desc())
    )
    league_teams = result.scalars().all()
    print("League teams: ", league_teams)
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
    print("Leagues: ", leagues)

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
    print("Fixtures: ", fixtures)

    # Fetch all PlayerSeasonStats for the team
    result = await session.execute(
                        select(FixtureLineup)
                        .join(Fixture)
                        .filter(FixtureLineup.league_team_id == league_teams[0].id)
                        .order_by(Fixture.date.desc())
                        .options(joinedload(FixtureLineup.coach)))
    latest_lineup = result.scalars().first()
    print("latest lineup: ",latest_lineup)
    if latest_lineup:
        result = await session.execute( 
                        select(FixturePlayerStat)
                        .filter_by(fixture_id=latest_lineup.fixture_id, league_team_id=league_teams[0].id)
                        .options(joinedload(FixturePlayerStat.player))
                        .all())

        players_stats = result.scalar().all()
        print("Player stats: ", players_stats)

        squad = defaultdict(list)
        for stat in players_stats:
            player = stat.player
            position = (stat.position or '').lower()
            if 'keeper' in position:
                key = 'goalkeeper'
            elif 'defense' in position or 'back' in position or position == 'defender':
                key = 'defensor'
            elif 'mid' in position:
                key = 'mid_field'
            elif 'attack' in position or 'forward' in position or position == 'attacker':
                key = 'attacker'
            else:
                key = 'mid_field'  # fallback to midfield if unclear

            squad[key].append({
                "player": player.name,
                "playerImage": player.photo_url
            })

        coach = latest_lineup.coach

        print("Coach: ", coach)

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