# File: routes/fixture_routes.py
from fastapi import APIRouter, BackgroundTasks, HTTPException
from pydantic import BaseModel, Field
from typing import List

from integrations.fixture_details_processor.fixture_processor import (
    process_all_fixtures,
)

router = APIRouter(prefix="/fixtures", tags=["Fixtures"])


class FixtureProcessRequest(BaseModel):
    folder_path: str = Field(
        ...,
        description="Rota à pasta que contem os arquivos fixture_*.json.",
        example="json/fetched",
    )
    tables: List[str] = Field(
        ...,
        description="Lista de tabelas a popular.",
        example=["events", "lineups", "statistics", "player_stats"],
    )


@router.post("/process-files")
async def process_fixtures_endpoint(
    payload: FixtureProcessRequest, background_tasks: BackgroundTasks
):
    try:
        background_tasks.add_task(
            process_all_fixtures, payload.folder_path, payload.tables
        )
        return {
            "message": "O processamento dos arquivos da fixture comezou no segundo plano."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
