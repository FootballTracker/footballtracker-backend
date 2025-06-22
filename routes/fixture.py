from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import joinedload
from typing import Dict

from database.database import get_db_session
from models.fixture import Fixture
from models.league import League
from models.country import Country
from models.base_team import BaseTeam
from models.league_team import LeagueTeam
from models.fixture_statistic import FixtureStatistic
from models.venue import Venue
from models.fixture_player_stat import FixturePlayerStat
from models.base_player import BasePlayer
from schemas import MatchStatisticsResponse, MatchInfoSchema, LeagueSchema, CountrySchema, TeamStatsSchema, FixturePlayerStatsResponse, TeamSummarySchema, PlayerStatSchema

router = APIRouter(tags=["Fixtures"])

@router.get("/match_statistics/{fixture_id}", response_model=MatchStatisticsResponse)
async def get_match_statistics(fixture_id: int, db: AsyncSession = Depends(get_db_session)):
    stmt = (
        select(Fixture)
        .options(
            joinedload(Fixture.league).joinedload(League.country),
            joinedload(Fixture.venue),
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team)
        )
        .where(Fixture.api_id == fixture_id)
    )
    result = await db.execute(stmt)
    fixture = result.scalar_one_or_none()

    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    league = fixture.league
    country = league.country
    venue = fixture.venue
    home_team = fixture.home_team.team
    away_team = fixture.away_team.team

    # Load statistics
    stats_stmt = select(FixtureStatistic).where(FixtureStatistic.fixture_id == fixture_id)
    stats_result = await db.execute(stats_stmt)
    stats = stats_result.scalars().all()

    stats_dict = {}
    for stat in stats:
        side = "home_team" if stat.league_team_id == fixture.home_team_id else "away_team"
        team = home_team if side == "home_team" else away_team

        stats_data = {
            "shots_on_goal": stat.shots_on_goal,
            "shots_off_goal": stat.shots_off_goal,
            "total_shots": stat.total_shots,
            "blocked_shots": stat.blocked_shots,
            "shots_insidebox": stat.shots_insidebox,
            "shots_outsidebox": stat.shots_outsidebox,
            "fouls": stat.fouls,
            "corner_kicks": stat.corner_kicks,
            "offsides": stat.offsides,
            "ball_possession": stat.ball_possession,
            "yellow_cards": stat.yellow_cards,
            "red_cards": stat.red_cards,
            "goalkeeper_saves": stat.goalkeeper_saves,
            "total_passes": stat.total_passes,
            "passes_accurate": stat.passes_accurate,
            "passes_percentage": stat.passes_percentage,
            "expected_goals": stat.expected_goals
        }

        stats_dict[side] = TeamStatsSchema(
            name=team.name,
            logo_url=team.logo_url,
            stats=stats_data
        )

    return MatchStatisticsResponse(
        information=MatchInfoSchema(
            referee=fixture.referee,
            stadium=venue.name if venue else None,
            city=venue.city if venue else None,
            status=fixture.status,
            date=fixture.date.isoformat() if fixture.date else None,
            league=LeagueSchema(
                name=league.name,
                logo_url=league.logo_url,
                season=str(fixture.season),
                round=fixture.round,
                country=CountrySchema(
                    name=country.name,
                    flag_url=country.flag_url
                ) if country else None
            )
        ),
        statistics=stats_dict
    )

@router.get("/get_player_match_statistics/{fixture_id}/player/{base_player_id}", response_model=FixturePlayerStatsResponse)
async def get_player_match_statistics(fixture_id: int, base_player_id: int, db: AsyncSession = Depends(get_db_session)):
    # Load fixture with teams
    stmt = (
        select(Fixture)
        .options(
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team),
        )
        .where(Fixture.api_id == fixture_id)
    )
    result = await db.execute(stmt)
    fixture = result.scalar_one_or_none()

    if not fixture:
        raise HTTPException(status_code=404, detail="Fixture not found")

    # Query player stats for the given fixture AND player
    stats_stmt = (
        select(FixturePlayerStat)
        .options(
            joinedload(FixturePlayerStat.player),
            joinedload(FixturePlayerStat.league_team).joinedload(LeagueTeam.team)
        )
        .where(
            FixturePlayerStat.fixture_id == fixture.api_id,
            FixturePlayerStat.base_player_api_id == base_player_id
        )
    )
    stats_result = await db.execute(stats_stmt)
    player_stats = stats_result.scalar_one_or_none()

    if not player_stats:
        raise HTTPException(status_code=404, detail="Estátiscas do jogador não encontradas para essa partida")

    # Prepare team summaries
    home_team = fixture.home_team.team
    away_team = fixture.away_team.team

    home_summary = TeamSummarySchema(
        name=home_team.name,
        logo_url=home_team.logo_url,
        score=fixture.home_team_score if hasattr(fixture, 'home_team_score') else 0
    )
    away_summary = TeamSummarySchema(
        name=away_team.name,
        logo_url=away_team.logo_url,
        score=fixture.away_team_score if hasattr(fixture, 'away_team_score') else 0
    )

    # Position standard 
    position = None
    pos = (player_stats.position or '').lower()
    if pos in ['g', 'd', 'm', 'f']:
        position = (
            'goalkeeper' if pos == 'g' else
            'defensor' if pos == 'd' else
            'mid_field' if pos == 'm' else
            'attacker'
        )

    player_stats_response = PlayerStatSchema(
        name=player_stats.player.name,
        player_url=player_stats.player.photo_url,
        team_logo=player_stats.league_team.team.logo_url,
        fixture_id=player_stats.fixture_id,
        jersey_number=player_stats.jersey_number,
        is_starter=player_stats.is_starter,
        game_minute=player_stats.game_minute,
        game_number=player_stats.game_number,
        position=position,
        game_captain=player_stats.game_captain,
        game_substitute=player_stats.game_substitute,
        offsides=player_stats.offsides,
        shots_total=player_stats.shots_total,
        shots_on=player_stats.shots_on,
        goals=player_stats.goals,
        goals_conceded=player_stats.goals_conceded,
        assists=player_stats.assists,
        goals_saves=player_stats.goals_saves,
        passes_total=player_stats.passes_total,
        passes_key=player_stats.passes_key,
        passes_accuracy=player_stats.passes_accuracy,
        tackles_total=player_stats.tackles_total,
        tackles_blocks=player_stats.tackles_blocks,
        tackles_interceptions=player_stats.tackles_interceptions,
        duels_total=player_stats.duels_total,
        duels_won=player_stats.duels_won,
        dribbles_attempts=player_stats.dribbles_attempts,
        dribbles_success=player_stats.dribbles_success,
        fouls_drawn=player_stats.fouls_drawn,
        fouls_committed=player_stats.fouls_committed,
        cards_yellow=player_stats.cards_yellow,
        cards_red=player_stats.cards_red,
        penalty_won=player_stats.penalty_won,
        penalty_commited=player_stats.penalty_commited,
        penalty_scored=player_stats.penalty_scored,
        penalty_missed=player_stats.penalty_missed,
        penalty_saved=player_stats.penalty_saved,
        dribbles_past=player_stats.dribbles_past,
        rating=float(player_stats.rating) if player_stats.rating is not None else None,
        grid=player_stats.grid
    )

    return FixturePlayerStatsResponse(
        home_team=home_summary,
        away_team=away_summary,
        player_stats=player_stats_response
    )