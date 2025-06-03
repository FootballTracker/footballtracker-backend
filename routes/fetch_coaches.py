from fastapi import APIRouter, BackgroundTasks, HTTPException

from integrations.coaches_processor import fetch_and_store_coaches

router = APIRouter(prefix="/coaches", tags=["Coaches"])


@router.post("/fetch")
async def fetch_coaches(background_tasks: BackgroundTasks):
    """Endpoint para obter treinadores e guardar no banco de dados"""
    try:
        background_tasks.add_task(fetch_and_store_coaches)
        return {"message": "Download dos treinadores iniciado em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
