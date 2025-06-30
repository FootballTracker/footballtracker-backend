from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
from integrations.save_json import fetch_and_save_to_json
from integrations.countries_processor import process_countries_json_and_save_to_db

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.post("/fetch")
async def fetch_countries(background_tasks: BackgroundTasks):
    """Endpoint para obter os paises e guardar num arquivo Json"""
    try:
        background_tasks.add_task(
            fetch_and_save_to_json, "/countries", "countries.json"
        )
        return {"message": "Download dos países iniciada em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
