import httpx
import asyncio
from datetime import datetime, timezone
from sqlalchemy import select

from database.database import async_session_factory
from models.league_team import LeagueTeam
from models.league import League
from models.team_season_stat import TeamSeasonStat
from config import HEADERS, API_HOST
from integrations.save_json import wait_for_api_slot


async def fetch_team_stats_from_api(league_api_id: int, season: int, team_api_id: int):
    url = f"https://{API_HOST}/teams/statistics"
    params = {
        "league": str(league_api_id),
        "season": str(season),
        "team": str(team_api_id),
    }

    async with httpx.AsyncClient() as client:
        try:
            response = await client.get(
                url, headers=HEADERS, params=params, timeout=30.0
            )
            response.raise_for_status()
            data = response.json().get("response")
            if not data or not data.get("league"):
                print(
                    f"  - Sem dados de estadísticas para team {team_api_id} em league {league_api_id}, season {season}"
                )
                return None
            return data
        except httpx.HTTPStatusError as e:
            print(
                f"Erro na API para team {team_api_id}: {e.response.status_code} - {e.response.text}"
            )
            return None
        except Exception as e:
            print(f"Erro inesperado para team {team_api_id}: {e}")
            return None


async def process_and_store_team_season_stats(league_api_id: int, season: int):
    print(
        f"Iniciando busca por estatísticas para a liga {league_api_id}, temporada {season}..."
    )
    async with async_session_factory() as session:
        league_teams_query = (
            select(LeagueTeam.id, LeagueTeam.base_team_api_id)
            .join(League)
            .where(League.api_id == league_api_id, League.season == season)
        )
        result = await session.execute(league_teams_query)
        teams_in_league = result.all()

        if not teams_in_league:
            print(
                f"Nenhum time encontrado no banco de dados para a liga {league_api_id} e temporada {season}."
            )
            return

        print(f"Encontrados {len(teams_in_league)} times para processar.")

        for lt_id, team_api_id in teams_in_league:
            existing_stat_query = select(TeamSeasonStat.id).where(
                TeamSeasonStat.league_team_id == lt_id
            )
            existing_stat_check = await session.execute(existing_stat_query)
            if existing_stat_check.scalar_one_or_none() is not None:
                print(
                    f"  - Estatísticas para o time {team_api_id} (league_team_id: {lt_id}) já existem. Omitindo."
                )
                continue

            print(f"Processando team {team_api_id}...")

            can_proceed = await wait_for_api_slot()
            if not can_proceed:
                print("Processo interrompido pelo limite de requisições.")
                break

            stats_data = await fetch_team_stats_from_api(
                league_api_id, season, team_api_id
            )
            if not stats_data:
                continue

            fixtures = stats_data.get("fixtures", {})
            biggest = stats_data.get("biggest", {})
            penalty = stats_data.get("penalty", {})

            biggest_win_str = f"{biggest.get('wins', {}).get('home')} (H) / {biggest.get('wins', {}).get('away')} (A)"
            biggest_loss_str = f"{biggest.get('loses', {}).get('home')} (H) / {biggest.get('loses', {}).get('away')} (A)"

            new_stat = TeamSeasonStat(
                league_team_id=lt_id,
                form=stats_data.get("form", ""),
                fixtures_played=fixtures.get("played", {}).get("total"),
                fixtures_wins=fixtures.get("wins", {}).get("total"),
                fixtures_draws=fixtures.get("draws", {}).get("total"),
                fixtures_loses=fixtures.get("loses", {}).get("total"),
                biggest_streak_wins=biggest.get("streak", {}).get("wins"),
                biggest_streak_draws=biggest.get("streak", {}).get("draws"),
                biggest_streak_loses=biggest.get("streak", {}).get("loses"),
                biggest_win=biggest_win_str,
                biggest_loss=biggest_loss_str,
                clean_sheets=stats_data.get("clean_sheet", {}).get("total"),
                failed_to_score=stats_data.get("failed_to_score", {}).get("total"),
                penalty_scored=penalty.get("scored", {}).get("total"),
                penalty_missed=penalty.get("missed", {}).get("total"),
                penalty_total=penalty.get("total"),
                lineups=stats_data.get("lineups", []),
                cards_by_minute=stats_data.get("cards", {}),
                last_updated=datetime.now(timezone.utc).replace(tzinfo=None),
            )
            session.add(new_stat)
            await session.commit()
            print(f"  + Estatísticas para team {team_api_id} guardadas.")

    print("✅ Processo concluído.")
