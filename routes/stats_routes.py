from fastapi import APIRouter, BackgroundTasks, HTTPException
from integrations.season_stats_aggregator import aggregate_player_season_stats

router = APIRouter(prefix="/stats", tags=["Statistics"])


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
