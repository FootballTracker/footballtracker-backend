from fastapi import APIRouter, BackgroundTasks, HTTPException

from integrations.players_processor import fetch_and_store_players

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("/fetch")
async def fetch_players(background_tasks: BackgroundTasks):
    """Endpoint para obter jogadores e guardar no banco de dados"""
    try:
        background_tasks.add_task(fetch_and_store_players)
        return {"message": "Download dos jogadores iniciado em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
