from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from integrations.league_classification_processor import (
    fetch_league_classification_and_save_db,
)


router = APIRouter(
    prefix="/classification_leagues", tags=["Classification Leagues Fetch"]
)


@router.post("/fetch")
async def fetch_leagues(
    background_tasks: BackgroundTasks,
    id: int = Query(None, description="The id of the league"),
    season: int = Query(None, description="The season of the league (e.g., 2023)"),
):
    """Endpoint para obter ligas e guardar num arquivo Json e no banco de dados"""
    params = {}

    if id is not None:
        params["league"] = id
    if season is not None:
        params["season"] = season

    try:
        background_tasks.add_task(fetch_league_classification_and_save_db, params)

        return {
            "message": f"Download e processamento da liga {id} na temporada {season} iniciado"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
