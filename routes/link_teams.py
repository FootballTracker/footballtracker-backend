from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
from integrations.save_json import fetch_and_save_to_json
from integrations.league_teams_processor import link_teams_to_league_and_venues

router = APIRouter(prefix="/link_teams", tags=["Link_Teams"])


@router.post("/link-teams-to-league")
async def link_teams_to_league(
    background_tasks: BackgroundTasks,
    file_name: str = Query(
        ..., description="Nome do arquivo JSON de equipes (dentro da pasta json/)"
    ),
    api_league_id: int = Query(
        ..., description="ID da liga segundo a API para o enlace"
    ),
    season: int = Query(..., description="Temporada da liga para o enlace"),
):
    """Endpoint para enlazar equipes de um arquivo JSON a uma liga e temporada específicas no banco de dados."""
    try:
        background_tasks.add_task(
            link_teams_to_league_and_venues, file_name, api_league_id, season
        )
        return {
            "message": f"Processo de enlace de equipes do arquivo '{file_name}' à liga (ID API: {api_league_id}, Temporada: {season}) iniciado em segundo plano."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
