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
from models.team_season_stat import TeamSeasonStat
from schemas import (
    UserFavoriteTeamData,
    TeamLeagues,
    TeamLeagues,
    TeamLeagueStat,
    TeamLeagueGeneralStats,
    TeamLeagueFormations,
    TeamLeagueStatistics
) 
from collections import defaultdict
from typing import List

router = APIRouter(tags=["Teams"])

@router.get("/teams")
async def get_teams(user_id: int | None = None, text: str | None = None, session: AsyncSession = Depends(get_db_session)):
    

    if text:
        stmt = select(BaseTeam).where(BaseTeam.name.icontains(text.lower()))

        result = await session.execute(stmt)
        teams = result.scalars().all()

        response = {
            "all_teams": [
                {
                    "id": team.api_id,
                    "name": team.name,
                    "logo": team.logo_url,
                    "is_favorite": False
                }
                for team in teams
            ]
        }

    else:
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

        response = {
            "favorite_team": [{
                "id": favorite_team.api_id,
                "name": favorite_team.name,
                "logo": favorite_team.logo_url,
                "is_favorite": True
            }] if favorite_team else [],
            "all_teams": [
                {
                    "id": team.api_id,
                    "name": team.name,
                    "logo": team.logo_url,
                    "is_favorite": False
                }
                for team in teams
            ]
        }

    return response

@router.post("/team/favorite")
async def favorite_team(data: UserFavoriteTeamData, session: AsyncSession = Depends(get_db_session)):

    result = await session.execute(
        select(User)
        .where(User.id == data.user_id)
    )

    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(404, detail="Usuário não encontrado")
    
    result = await session.execute(
        select(BaseTeam)
        .where(BaseTeam.api_id == data.team_id)
    )

    team = result.scalar_one_or_none()

    if not team:
        raise HTTPException(404, detail="Time não encontrado")


    if user.favorite_team_api_id == data.team_id:
        user.favorite_team_api_id = None
    else:
        user.favorite_team_api_id = data.team_id

    await session.commit()

    return {
        "message": "Time favoritado/desfavoritado"
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
                    "id": None,
                    "name": f.home_team.team.name,
                    "logo": f.home_team.team.logo_url,
                    "score": f.home_team_score_goals,
                } if f.home_team and f.home_team.team else None,
                "away_team": {
                    "id": None,
                    "name": f.away_team.team.name,
                    "logo": f.away_team.team.logo_url,
                    "score": f.away_team_score_goals,
                } if f.away_team and f.away_team.team else None,
            }
            for f in fixtures
        ],
        "players": latest_players,
    }

@router.get("/team/{team_id}/leagues")
async def get_team_leagues(team_id: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(League)
        .join(LeagueTeam, League.id == LeagueTeam.league_id)
        .where(LeagueTeam.base_team_api_id == team_id)
    )

    all_leagues = result.scalars().all()

    team_leagues = {}
    for league in all_leagues:
        if league.api_id not in team_leagues:
            team_leagues[league.api_id] = TeamLeagues(
                api_id=f"{league.api_id}", name=league.name, seasons=[]
            )
        team_leagues[league.api_id].seasons.append(league.season)

    for key in team_leagues.keys():
        team_leagues[key].seasons.sort()

    return list(team_leagues.values())

@router.get("/team/{team_id}/league/{league_api_id}", response_model=TeamLeagueStatistics)
async def get_team_leagues(team_id: int, league_api_id: int, season: int, session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        select(LeagueTeam)
        .join(League, League.id == LeagueTeam.league_id)
        .options(
            joinedload(LeagueTeam.season_stats),
            selectinload(LeagueTeam.fixtures_home),
            selectinload(LeagueTeam.fixtures_away)
        )
        .where((League.api_id == league_api_id) & (League.season == season) & (LeagueTeam.base_team_api_id == team_id))
    )

    league_team = result.scalar_one_or_none()

    if not league_team:
        raise HTTPException(404, detail={
            "message": "Estatísticas do time indisponíveis para essa liga",
            "ok": True
        })

    matches = [0, 0]
    victories = [0, 0]
    draws = [0, 0]
    loses = [0, 0]
    gp = [0, 0]
    gc = [0, 0]
    most_goals_for_home = 0
    most_goals_for_away = 0
    most_goals_against_home = 0
    most_goals_against_away = 0

    for match in league_team.fixtures_home:
        matches[0] += 1
        if match.home_team_score_goals > match.away_team_score_goals:
            victories[0] += 1
        elif match.home_team_score_goals == match.away_team_score_goals:
            draws[0] += 1
        else:
            loses[0] += 1
        gp[0] += match.home_team_score_goals
        gc[0] += match.away_team_score_goals

        if match.home_team_score_goals > most_goals_for_home: most_goals_for_home = match.home_team_score_goals
        if match.away_team_score_goals > most_goals_against_home: most_goals_against_home = match.away_team_score_goals

    for match in league_team.fixtures_away:
        matches[1] += 1
        if match.home_team_score_goals < match.away_team_score_goals:
            victories[1] += 1
        elif match.home_team_score_goals == match.away_team_score_goals:
            draws[1] += 1
        else:
            loses[1] += 1
        gp[1] += match.away_team_score_goals
        gc[1] += match.home_team_score_goals

        if match.home_team_score_goals > most_goals_against_away: most_goals_against_away = match.home_team_score_goals
        if match.away_team_score_goals > most_goals_for_away: most_goals_for_away = match.away_team_score_goals

    infos = []

    infos.append(TeamLeagueStat(
        name="Partidas",
        home=matches[0],
        away=matches[1],
        total=matches[0]+matches[1]
    ))

    infos.append(TeamLeagueStat(
        name="Vitórias",
        home=victories[0],
        away=victories[1],
        total=victories[0]+victories[1]
    ))

    infos.append(TeamLeagueStat(
        name="Empates",
        home=draws[0],
        away=draws[1],
        total=draws[0]+draws[1]
    ))

    infos.append(TeamLeagueStat(
        name="Derrotas",
        home=loses[0],
        away=loses[1],
        total=loses[0]+loses[1]
    ))

    infos.append(TeamLeagueStat(
        name="GP",
        home=gp[0],
        away=gp[1],
        total=gp[0]+gp[1]
    ))

    avg_home = round(gp[0]/matches[0], 2) if matches[0] > 0 else 0
    avg_away = round(gp[1]/matches[1], 2) if matches[1] > 0 else 0
    infos.append(TeamLeagueStat(
        name="Média GP",
        home=avg_home,
        away=avg_away,
        total=round((avg_home+avg_away)/2, 2)
    ))

    infos.append(TeamLeagueStat(
        name="GC",
        home=gc[0],
        away=gc[1],
        total=gc[0]+gc[1]
    ))

    avg_home = round(gc[0]/matches[0], 2) if matches[0] > 0 else 0
    avg_away = round(gc[1]/matches[1], 2) if matches[1] > 0 else 0
    infos.append(TeamLeagueStat(
        name="Média GC",
        home=avg_home,
        away=avg_away,
        total=round((avg_home+avg_away)/2, 2)
    ))

    season: TeamSeasonStat = league_team.season_stats

    split = season.biggest_win.split(" ")
    biggest_win_home = split[0] if len(split) > 4 else "Desconhecida"
    biggest_win_away = split[3] if len(split) > 4 else "Desconhecida"

    split = season.biggest_loss.split(" ")
    biggest_loss_home = split[0] if len(split) > 4 else "Desconhecida"
    biggest_loss_away = split[3] if len(split) > 4 else "Desconhecida"
    general_stats = TeamLeagueGeneralStats(
        biggestWinHome=biggest_win_home,
        biggestWinAway=biggest_win_away,
        biggestLoseHome=biggest_loss_home,
        biggestLoseAway=biggest_loss_away,
        mostDrawsSeq=season.biggest_streak_draws,
        mostGoalsAgainstAway=most_goals_against_away,
        mostGoalsAgainstHome=most_goals_against_home,
        mostGoalsForAway=most_goals_for_away,
        mostGoalsForHome=most_goals_for_home,
        mostLosesSeq=season.biggest_streak_loses,
        mostWinsSeq=season.biggest_streak_wins,
        penaltyGoals=season.penalty_scored,
        penaltyMisses=season.penalty_missed
    )

    formations: List[TeamLeagueFormations] = [
        TeamLeagueFormations(
            formation=lineup["formation"],
            times=lineup["played"]
        ) for lineup in season.lineups
    ]

    return TeamLeagueStatistics(
        form=season.form,
        formations=formations,
        infos=infos,
        statistics=general_stats
    )


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