from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel
from integrations.season_stats_aggregator import aggregate_player_season_stats
from integrations.team_season_stats_processor import process_and_store_team_season_stats


router = APIRouter(prefix="/stats", tags=["Statistics"])


class TeamSeasonRequest(BaseModel):
    league_api_id: int
    season: int


@router.post("/aggregate-season-stats")
async def aggregate_stats_endpoint(background_tasks: BackgroundTasks):
    """
    Inicia a tarefa de agregação para calcular e preencher as estatísticas
    da temporada dos jogadores (PlayerSeasonStat).
    """
    try:
        background_tasks.add_task(aggregate_player_season_stats)
        return {
            "message": "A agregação das estatísticas da temporada foi iniciada em segundo plano."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/fetch-team-season-stats")
async def fetch_team_stats_endpoint(
    payload: TeamSeasonRequest, background_tasks: BackgroundTasks
):
    """
    Inicia a busca e armazenamento das estatísticas de temporada para todos os times.
    """
    try:
        background_tasks.add_task(
            process_and_store_team_season_stats,
            league_api_id=payload.league_api_id,
            season=payload.season,
        )
        return {
            "message": "A busca por estatísticas de temporada dos times foi iniciada em segundo plano."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
