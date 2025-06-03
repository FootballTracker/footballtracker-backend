from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from models.fixture_player_stat import FixturePlayerStat
from models.league_team import LeagueTeam
from models.league import League


async def process_fixture_player_stats(session: AsyncSession, fixture_data: dict):
    print(" Processando estadísticas do jogador...")
    fixture_api_id = fixture_data["fixture"]["id"]
    league_api_id = fixture_data["league"]["id"]

    starter_ids = {
        player["player"]["id"]
        for lineup in fixture_data.get("lineups", [])
        for player in lineup.get("startXI", [])
    }

    for team_players_data in fixture_data.get("players", []):
        team_api_id = team_players_data["team"]["id"]

        query = (
            select(LeagueTeam.id)
            .join(League, LeagueTeam.league_id == League.id)
            .where(
                LeagueTeam.base_team_api_id == team_api_id,
                League.api_id == league_api_id,
            )
        )
        league_team_id = (await session.execute(query)).scalar_one_or_none()

        if not league_team_id:
            print(
                f"ADVERTENCIA: Não se encontrou LeagueTeam para team_api_id {team_api_id} e league_api_id {league_api_id}"
            )
            continue

        for player_entry in team_players_data.get("players", []):
            player_api_id = player_entry["player"]["id"]

            if not player_api_id:
                player_name = player_entry.get("player", {}).get("name", "N/A")
                print(
                    f"  ADVERTENCIA (Player Stats): Encontrado jogador com ID 0 ou nulo. Nome: {player_name}. Omitindo."
                )
                continue

            stats = player_entry["statistics"][0]

            games_stats = stats.get("games", {})
            shots_stats = stats.get("shots", {})
            goals_stats = stats.get("goals", {})
            passes_stats = stats.get("passes", {})
            tackles_stats = stats.get("tackles", {})
            duels_stats = stats.get("duels", {})
            dribbles_stats = stats.get("dribbles", {})
            fouls_stats = stats.get("fouls", {})
            cards_stats = stats.get("cards", {})
            penalty_stats = stats.get("penalty", {})

            new_player_stat = FixturePlayerStat(
                fixture_id=fixture_api_id,
                league_team_id=league_team_id,
                base_player_api_id=player_api_id,
                jersey_number=games_stats.get("number"),
                is_starter=player_api_id in starter_ids,
                game_minute=games_stats.get("minutes"),
                game_number=games_stats.get("number"),
                position=games_stats.get("position"),
                game_position=None,
                game_captain=games_stats.get("captain", False),
                game_substitute=games_stats.get("substitute", False),
                offsides=stats.get("offsides"),
                shots_total=shots_stats.get("total"),
                shots_on=shots_stats.get("on"),
                goals=goals_stats.get("total"),
                goals_conceded=goals_stats.get("conceded"),
                assists=goals_stats.get("assists"),
                goals_saves=goals_stats.get("saves"),
                passes_total=passes_stats.get("total"),
                passes_key=passes_stats.get("key"),
                passes_accuracy=str(passes_stats.get("accuracy")),
                tackles_total=tackles_stats.get("total"),
                tackles_blocks=tackles_stats.get("blocks"),
                tackles_interceptions=tackles_stats.get("interceptions"),
                duels_total=duels_stats.get("total"),
                duels_won=duels_stats.get("won"),
                dribbles_attempts=dribbles_stats.get("attempts"),
                dribbles_success=dribbles_stats.get("success"),
                dribbles_past=dribbles_stats.get("past"),
                fouls_drawn=fouls_stats.get("drawn"),
                fouls_committed=fouls_stats.get("committed"),
                cards_yellow=cards_stats.get("yellow"),
                cards_red=cards_stats.get("red"),
                penalty_won=penalty_stats.get("won"),
                penalty_commited=penalty_stats.get("commited"),
                penalty_scored=penalty_stats.get("scored"),
                penalty_missed=penalty_stats.get("missed"),
                penalty_saved=penalty_stats.get("saved"),
                last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(new_player_stat)
