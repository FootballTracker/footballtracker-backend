import asyncio
from sqlalchemy import text
from database.database import async_session_factory


async def aggregate_player_season_stats():
    print("Iniciando a agregação das estatísticas da temporada dos jogadores...")
    truncate_query = text("TRUNCATE TABLE players_season_stats RESTART IDENTITY;")
    insert_query = text(
        """
        INSERT INTO players_season_stats (
            base_player_api_id, league_team_id, appearances, lineups, minutes,
            position, rating, captain, substitute_in, substitutes_out, substitutes_bench,
            shots_total, shots_on, goals, goals_conceded, assists, goals_saves,
            passes_total, passes_key, passes_accuracy, tackles_total, tackles_blocks,
            tackles_interceptions, duels_total, duels_won, dribbles_attempts,
            dribbles_success, dribbles_completed, fouls_drawn, fouls_committed,
            cards_yellow, cards_red, penalty_won, penalty_commited, penalty_scored,
            penalty_missed, penalty_saved, last_updated
        )
        SELECT
            fps.base_player_api_id,
            fps.league_team_id,
            COUNT(fps.id),
            SUM(CASE WHEN fps.is_starter THEN 1 ELSE 0 END),
            SUM(fps.game_minute),
            MAX(fps.position),
            AVG(fps.rating),
            SUM(CASE WHEN fps.game_captain THEN 1 ELSE 0 END) > 0,
            SUM(CASE WHEN fps.is_starter = false AND fps.game_minute > 0 THEN 1 ELSE 0 END),
            SUM(CASE WHEN fps.is_starter = true AND (fps.game_minute > 0 AND fps.game_minute < 90) THEN 1 ELSE 0 END),
            SUM(CASE WHEN fps.game_minute = 0 OR fps.game_minute IS NULL THEN 1 ELSE 0 END),
            SUM(fps.shots_total), SUM(fps.shots_on), SUM(fps.goals),
            SUM(fps.goals_conceded), SUM(fps.assists), SUM(fps.goals_saves),
            SUM(fps.passes_total), SUM(fps.passes_key), MAX(fps.passes_accuracy),
            SUM(fps.tackles_total), SUM(fps.tackles_blocks), SUM(fps.tackles_interceptions),
            SUM(fps.duels_total), SUM(fps.duels_won), SUM(fps.dribbles_attempts),
            SUM(fps.dribbles_success), SUM(fps.dribbles_success),
            SUM(fps.fouls_drawn), SUM(fps.fouls_committed), SUM(fps.cards_yellow),
            SUM(fps.cards_red), SUM(fps.penalty_won), SUM(fps.penalty_commited),
            SUM(fps.penalty_scored), SUM(fps.penalty_missed), SUM(fps.penalty_saved),
            NOW()
        FROM
            fixture_player_stats AS fps
        GROUP BY
            fps.base_player_api_id, fps.league_team_id;
    """
    )
    async with async_session_factory() as session:
        async with session.begin():
            print("1. Limpando a tabela de estatísticas da temporada...")
            await session.execute(truncate_query)

            print("2. Calculando e inserindo as novas estatísticas agregadas...")
            await session.execute(insert_query)

    print("✅ Agregação das estatísticas da temporada completada com sucesso.")
