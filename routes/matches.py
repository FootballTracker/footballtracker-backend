from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, update
from sqlalchemy.orm import joinedload, selectinload
from typing import List
from database.database import get_db_session
from schemas import (
    FullMatchResponse,
    MatchResponse,
    TeamInfo,
    MatchInfo,
    MatchTeamsStatistics,
    MatchTeamStatistic,
    EventPlayer,
    EventAssist,
    MatchEvent,
    MatchMinuteEvent,
    Lineup,
    Coach,
    LineupPlayer,
    Lineup,
    FullLineup
)
from models.fixture import Fixture
from models.fixture_event import FixtureEvent
from models.fixture_lineup import FixtureLineup
from models.fixture_player_stat import FixturePlayerStat
from models.league_team import LeagueTeam
from models.league import League
from models.venue import Venue

router = APIRouter(tags=["Matches"], prefix="/match")

@router.get("/{id}", response_model=FullMatchResponse)
async def get_match(id: int, session: AsyncSession = Depends(get_db_session)):

    result = await session.execute(
        select(Fixture)
        .options(
            joinedload(Fixture.home_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.away_team).joinedload(LeagueTeam.team),
            joinedload(Fixture.venue).joinedload(Venue.country),
            joinedload(Fixture.league).joinedload(League.country),
            selectinload(Fixture.statistics)
        )
        .where(Fixture.api_id == id)
    )

    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, detail="Partida não encontrada")

    if match.statistics:
        if match.statistics[0].league_team_id == match.home_team_id:
            home_team_stats = match.statistics[0]
            away_team_stats = match.statistics[1]
        else:
            home_team_stats = match.statistics[1]
            away_team_stats = match.statistics[0]

    match_response = FullMatchResponse(
        match = MatchResponse(
            id = match.api_id,
            home_team = TeamInfo(
                id = match.home_team.team.api_id, score = match.home_team_score_goals, logo = match.home_team.team.logo_url, name = match.home_team.team.name
            ),
            away_team = TeamInfo(
                id = match.away_team.team.api_id, score = match.away_team_score_goals, logo = match.away_team.team.logo_url, name = match.away_team.team.name
            ),
            date = match.date
        ),
        info = MatchInfo(
            referee = match.referee,
            venue = match.venue.name if match.venue else "Indisponível",
            city = match.venue.city if match.venue else "Indisponível",
            status = match.status,
            matchTime = str(match.elapsed),
            league = match.league.name if match.league else "Indisponível",
            leagueLogo = match.league.logo_url if match.league else "",
            country = match.league.country.name if match.league else "Indisponível",
            countryFlag = match.league.country.flag_url if match.league else "",
            season = match.season,
            round = (match.round.split('-')[-1].strip()),
        ),
        statistics = MatchTeamsStatistics(
            home_team = MatchTeamStatistic(
                shotsOnGoal = home_team_stats.shots_on_goal if home_team_stats.shots_on_goal else 0,
                shotsOffGoal = home_team_stats.shots_off_goal if home_team_stats.shots_off_goal else 0,
                shotsInsidebox = home_team_stats.shots_insidebox if home_team_stats.shots_insidebox else 0,
                shotsOutsidebox = home_team_stats.shots_outsidebox if home_team_stats.shots_outsidebox else 0,
                totalShots = home_team_stats.total_shots if home_team_stats.total_shots else 0,
                blockedShots = home_team_stats.blocked_shots if home_team_stats.blocked_shots else 0,
                fouls = home_team_stats.fouls if home_team_stats.fouls else 0,
                cornerKicks = home_team_stats.corner_kicks if home_team_stats.corner_kicks else 0,
                offsides = home_team_stats.offsides if home_team_stats.offsides else 0,
                ballPossession = home_team_stats.ball_possession if home_team_stats.ball_possession else 0,
                yellowCards = home_team_stats.yellow_cards if home_team_stats.yellow_cards else 0,
                redCards = home_team_stats.red_cards if home_team_stats.red_cards else 0,
                goalkeeperSaves = home_team_stats.goalkeeper_saves if home_team_stats.goalkeeper_saves else 0,
                totalPasses = home_team_stats.total_passes if home_team_stats.total_passes else 0,
                passesAccurate = home_team_stats.passes_accurate if home_team_stats.passes_accurate else 0,
                passesPercentage = home_team_stats.passes_percentage if home_team_stats.passes_percentage else 0,
            ),
            away_team = MatchTeamStatistic(
                shotsOnGoal = away_team_stats.shots_on_goal if away_team_stats.shots_on_goal else 0,
                shotsOffGoal = away_team_stats.shots_off_goal if away_team_stats.shots_off_goal else 0,
                shotsInsidebox = away_team_stats.shots_insidebox if away_team_stats.shots_insidebox else 0,
                shotsOutsidebox = away_team_stats.shots_outsidebox if away_team_stats.shots_outsidebox else 0,
                totalShots = away_team_stats.total_shots if away_team_stats.total_shots else 0,
                blockedShots = away_team_stats.blocked_shots if away_team_stats.blocked_shots else 0,
                fouls = away_team_stats.fouls if away_team_stats.fouls else 0,
                cornerKicks = away_team_stats.corner_kicks if away_team_stats.corner_kicks else 0,
                offsides = away_team_stats.offsides if away_team_stats.offsides else 0,
                ballPossession = away_team_stats.ball_possession if away_team_stats.ball_possession else 0,
                yellowCards = away_team_stats.yellow_cards if away_team_stats.yellow_cards else 0,
                redCards = away_team_stats.red_cards if away_team_stats.red_cards else 0,
                goalkeeperSaves = away_team_stats.goalkeeper_saves if away_team_stats.goalkeeper_saves else 0,
                totalPasses = away_team_stats.total_passes if away_team_stats.total_passes else 0,
                passesAccurate = away_team_stats.passes_accurate if away_team_stats.passes_accurate else 0,
                passesPercentage = away_team_stats.passes_percentage if away_team_stats.passes_percentage else 0,
            ) 
        ) if match.statistics else None
    )

    return match_response


event_comments_translation = {
    "Handling": "Mão na bola",
    "Off the ball foul": "Falta fora de lance",
    "Roughing": "Entrada dura",
    "Unallowed field entering": "Entrada não autorizada em campo",
    "Simulation": "Simulação",
    "Time wasting": "Cera",
    "Professional foul last man": "Falta como último homem",
    "Serious foul": "Falta grave",
    "Handball": "Mão na bola",
    "Persistent fouling": "Faltas em sequência",
    "Professional handball": "Mão intencional",
    "Unsportsmanlike conduct": "Conduta antidesportiva",
    "Foul": "Falta",
    "Dangerous play": "Jogo perigoso",
    "Violent conduct": "Conduta violenta",
    "Delay of game": "Cera",
    "Fighting": "Briga",
    "Tripping": "Tranco",
    "Argument": "Discussão",
    "Holding": "Agarrão",
    "Diving": "Simulação",
    "Elbowing": "Cotovelada"
}

def add_event_to_list(events_response: List[MatchMinuteEvent], event: FixtureEvent, scores: List[int], substitutions: List[int], home_team_id: int):
    if event.team_api_id == home_team_id:
        if event.type == "subst":
            event.type = "Subst"
            substitutions[0] += 1
            event.detail = f"Substitution {substitutions[0]}"

        events_response[-1].home_team.append(MatchEvent(
            player = EventPlayer(
                id = event.player_api_id if event.player_api_id else 0,
                name = event.player.name if event.player_api_id else ""
            ),
            assist = EventAssist(
                id = event.assist_player_api_id,
                name = event.assist.name if event.assist else None
            ),
            type = event.type,
            detail = event.detail,
            comments = event_comments_translation[event.comments] if event.comments else None
        ))
        if event.type == "Goal":
            scores[0] += 1
            events_response[-1].scoreboard = f"{scores[0]} x {scores[1]}"

    else:
        if event.type == "subst":
            event.type = "Subst"
            substitutions[1] += 1
            event.detail = f"Substitution {substitutions[1]}"

        events_response[-1].away_team.append(MatchEvent(
            player = EventPlayer(
                id = event.player_api_id if event.player_api_id else 0,
                name = event.player.name if event.player_api_id else ""
            ),
            assist = EventAssist(
                id = event.assist_player_api_id,
                name = event.assist.name if event.assist else None
            ),
            type = event.type,
            detail = event.detail,
            comments = event_comments_translation[event.comments] if event.comments else None
        ))
        if event.type == "Goal":
            scores[1] += 1
            events_response[-1].scoreboard = f"{scores[0]} x {scores[1]}"


@router.get("/{id}/events", response_model=List[MatchMinuteEvent])
async def get_match_events(id: int, session: AsyncSession = Depends(get_db_session)):

    result = await session.execute(
        select(Fixture)
        .options(
            joinedload(Fixture.home_team)
        )
        .where(Fixture.api_id == id)
    )

    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, detail="Partida não encontrada")

    result = await session.execute(
        select(FixtureEvent)
        .options(
            joinedload(FixtureEvent.player),
            joinedload(FixtureEvent.assist)
        )
        .where(FixtureEvent.fixture_api_id == id)
        .order_by(FixtureEvent.time_elapsed, FixtureEvent.time_extra)
    )

    events = result.scalars().all()

    home_team_id = match.home_team.base_team_api_id

    events_response: List[MatchMinuteEvent] = []

    scores = [0, 0]
    substitutions = [0, 0]

    for event in events:
        curr_time = event.time_elapsed
        if event.time_extra: curr_time += event.time_extra

        if len(events_response) and curr_time == events_response[-1].time:
            add_event_to_list(events_response, event, scores, substitutions, home_team_id)
        else:
            events_response.append(MatchMinuteEvent(
                time = curr_time,
                home_team = [],
                away_team = [],
                scoreboard = ""
            ))
            add_event_to_list(events_response, event, scores, substitutions, home_team_id)

    return events_response


@router.get("/{id}/lineups", response_model=FullLineup)
async def get_match_lineups(id: int, session: AsyncSession = Depends(get_db_session)):
    
    result = await session.execute(
        select(Fixture)
        .options(
            selectinload(Fixture.lineups).joinedload(FixtureLineup.coach),
            selectinload(Fixture.player_stats).joinedload(FixturePlayerStat.player)
        )
        .where(Fixture.api_id == id)
    )

    match = result.scalar_one_or_none()

    if not match:
        raise HTTPException(404, detail="Partida não encontrada")
    
    home_league_team_id = match.home_team_id

    if match.lineups[0].league_team_id == home_league_team_id:
        home_team_lineup_index = 0
        away_team_lineup_index = 1
    else:
        home_team_lineup_index = 1
        away_team_lineup_index = 0
    

    partial_initial_home_players: List[FixturePlayerStat] = []
    partial_initial_away_players: List[FixturePlayerStat] = []
    subs_home_players: List[LineupPlayer] = []
    subs_away_players: List[LineupPlayer] = []

    for player_stat in match.player_stats:

        if player_stat.is_starter:
            if player_stat.league_team_id == home_league_team_id:
                partial_initial_home_players.append(player_stat)
            else:
                partial_initial_away_players.append(player_stat)
        else:
            player = LineupPlayer(
                id = player_stat.player.api_id,
                name = player_stat.player.name,
                number = player_stat.jersey_number
            )

            if player_stat.league_team_id == home_league_team_id:
                subs_home_players.append(player)
            else:
                subs_away_players.append(player)

    initial_home_players: List[List[LineupPlayer]] = [[]]
    initial_away_players: List[List[LineupPlayer]] = [[]]
    
    
    if match.lineups[home_team_lineup_index].formation:
        partial_initial_home_players.sort(key=lambda player: player.grid)

        for player_stat in partial_initial_home_players:

            row = int(player_stat.grid.split(":")[0])

            if row != len(initial_home_players):
                initial_home_players.append([])
                
            initial_home_players[-1].append(LineupPlayer(
                id=player_stat.base_player_api_id if player_stat.base_player_api_id else 0,
                name=player_stat.player.name if player_stat.player else "",
                number=player_stat.jersey_number,
            ))

        for line in initial_home_players:
            line.reverse()

    else:
        initial_home_players.append([]) # defenders line
        initial_home_players.append([]) # midfielders line
        initial_home_players.append([]) # strikers line

        for player_stat in partial_initial_home_players:
            index = 0
            if player_stat.position == "D":
                index = 1
            elif player_stat.position == "M":
                index = 2
            elif player_stat.position == "F":
                index = 3
            
            initial_home_players[index].append(LineupPlayer(
                id=player_stat.base_player_api_id if player_stat.base_player_api_id else 0,
                name=player_stat.player.name if player_stat.player else "",
                number=player_stat.jersey_number,
            ))
        

    if match.lineups[away_team_lineup_index].formation:
        partial_initial_away_players.sort(key=lambda player: player.grid)

        for player_stat in partial_initial_away_players:

            row = int(player_stat.grid.split(":")[0])

            if row != len(initial_away_players):
                initial_away_players.append([])

            initial_away_players[-1].append(LineupPlayer(
                id=player_stat.base_player_api_id  if player_stat.base_player_api_id else 0,
                name=player_stat.player.name  if player_stat.player else "",
                number=player_stat.jersey_number,
            ))
    
    else:
        initial_away_players.append([]) # defenders line
        initial_away_players.append([]) # midfielders line
        initial_away_players.append([]) # strikers line

        for player_stat in partial_initial_away_players:
            index = 1
            if player_stat.position == "M":
                index = 2
            elif player_stat.position == "F":
                index = 3
            elif player_stat.position == "G":
                index = 0
                
            initial_away_players[index].append(LineupPlayer(
                id=player_stat.base_player_api_id if player_stat.base_player_api_id else 0,
                name=player_stat.player.name if player_stat.player else "",
                number=player_stat.jersey_number,
            ))

    initial_away_players.reverse()

    response: FullLineup = FullLineup(
        home = Lineup(
            coach = Coach(
                id = match.lineups[home_team_lineup_index].coach.api_id if match.lineups[home_team_lineup_index].coach else 0,
                name = match.lineups[home_team_lineup_index].coach.name if match.lineups[home_team_lineup_index].coach else "Indisponível",
                image = match.lineups[home_team_lineup_index].coach.photo_url if match.lineups[home_team_lineup_index].coach else ""
            ),
            initial = initial_home_players,
            substitutes = subs_home_players
        ),
        away = Lineup(
            coach = Coach(
                id = match.lineups[away_team_lineup_index].coach.api_id if match.lineups[away_team_lineup_index].coach else 0,
                name = match.lineups[away_team_lineup_index].coach.name if match.lineups[away_team_lineup_index].coach else "Indisponível",
                image = match.lineups[away_team_lineup_index].coach.photo_url if match.lineups[away_team_lineup_index].coach else ""
            ),
            initial = initial_away_players,
            substitutes = subs_away_players
        )
    )

    return response



@router.get("/update_all/status")
async def update_match_status(session: AsyncSession = Depends(get_db_session)):
    result = await session.execute(
        update(Fixture)
        .where(Fixture.status == "Match Finished")
        .values(status = "Partida Finalizada")
    )

    await session.commit()

    return {"message": "deu certo", "num": result.rowcount}