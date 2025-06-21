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
        select(FixturePlayerStat, BasePlayer.name, BasePlayer.photo_url)
        .join(BasePlayer, FixturePlayerStat.base_player_api_id == BasePlayer.api_id)
        .where(
            FixturePlayerStat.fixture_id == fixture.api_id,
            FixturePlayerStat.base_player_api_id == base_player_id
        )
    )
    stats_result = await db.execute(stats_stmt)
    player_stats = stats_result.all()

    if not player_stats:
        raise HTTPException(status_code=404, detail="Player stats not found for this fixture")

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
    for stat, _, _ in player_stats:
        pos = (stat.position or '').lower()
        if pos in ['g', 'd', 'm', 'f']:
            position = (
                'goalkeeper' if pos == 'g' else
                'defensor' if pos == 'd' else
                'mid_field' if pos == 'm' else
                'attacker'
            )
        break

    player_stats_list = [
        PlayerStatSchema(
            name=player_name,
            player_url=player_url,
            fixture_id=stat.fixture_id,
            jersey_number=stat.jersey_number,
            is_starter=stat.is_starter,
            game_minute=stat.game_minute,
            game_number=stat.game_number,
            position=position,
            game_captain=stat.game_captain,
            game_substitute=stat.game_substitute,
            offsides=stat.offsides,
            shots_total=stat.shots_total,
            shots_on=stat.shots_on,
            goals=stat.goals,
            goals_conceded=stat.goals_conceded,
            assists=stat.assists,
            goals_saves=stat.goals_saves,
            passes_total=stat.passes_total,
            passes_key=stat.passes_key,
            passes_accuracy=stat.passes_accuracy,
            tackles_total=stat.tackles_total,
            tackles_blocks=stat.tackles_blocks,
            tackles_interceptions=stat.tackles_interceptions,
            duels_total=stat.duels_total,
            duels_won=stat.duels_won,
            dribbles_attempts=stat.dribbles_attempts,
            dribbles_success=stat.dribbles_success,
            fouls_drawn=stat.fouls_drawn,
            fouls_committed=stat.fouls_committed,
            cards_yellow=stat.cards_yellow,
            cards_red=stat.cards_red,
            penalty_won=stat.penalty_won,
            penalty_commited=stat.penalty_commited,
            penalty_scored=stat.penalty_scored,
            penalty_missed=stat.penalty_missed,
            penalty_saved=stat.penalty_saved,
            dribbles_past=stat.dribbles_past,
            rating=float(stat.rating) if stat.rating is not None else None,
            grid=stat.grid
        )
        for stat, player_name, player_url in player_stats
    ]

    return FixturePlayerStatsResponse(
        home_team=home_summary,
        away_team=away_summary,
        player_stats=player_stats_list
    )