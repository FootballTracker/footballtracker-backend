from fastapi import APIRouter, BackgroundTasks, HTTPException
from integrations.manual_player_processor import fetch_and_store_specific_players
from integrations.players_processor import fetch_and_store_players
from pydantic import BaseModel
from typing import List

router = APIRouter(prefix="/players", tags=["Players"])


@router.post("/fetch")
async def fetch_players(background_tasks: BackgroundTasks):
    """Endpoint para obter jogadores e guardar no banco de dados"""
    try:
        background_tasks.add_task(fetch_and_store_players)
        return {"message": "Download dos jogadores iniciado em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


class PlayerIdRequest(BaseModel):
    player_ids: List[int]


@router.post("/fetch-by-ids")
async def fetch_players_by_ids(
    payload: PlayerIdRequest, background_tasks: BackgroundTasks
):
    if not payload.player_ids:
        raise HTTPException(
            status_code=400, detail="A lista 'player_ids' não pode estar vazia."
        )

    try:
        background_tasks.add_task(fetch_and_store_specific_players, payload.player_ids)
        count = len(payload.player_ids)
        return {
            "message": f"Busca para {count} jogador(es) específico(s) iniciada em segundo plano."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
