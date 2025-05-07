from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
from integrations.save_json import fetch_and_save_to_json
from integrations.teams_processor import process_teams_json_and_save_to_db

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.post("/fetch")
async def fetch_teams(
    background_tasks: BackgroundTasks,
    league: int = Query(None, description="The id of the league"),
    season: int = Query(None, description="The season of the league (e.g., 2023)"),
    id: Optional[int] = Query(None, description="The id of the team"),
    name: Optional[str] = Query(None, description="The name of the team"),
    country: Optional[str] = Query(None, description="The country name of the team"),
    code: Optional[str] = Query(None, description="The code of the team"),
    venue: Optional[int] = Query(None, description="The id of the venue"),
    search: Optional[str] = Query(
        None, min_length=3, description="The name or the country name of the team"
    ),
):
    """Endpoint para obter equipes e guardar num arquivo Json e no banco de dados"""
    params = {}
    filename_parts = ["teams"]

    if id is not None:
        params["id"] = id
        filename_parts.append(f"id_{id}")
    if league is not None:
        params["league"] = league
        filename_parts.append(f"league_{league}")
    if season is not None:
        params["season"] = season
        filename_parts.append(f"season_{season}")
    if name is not None:
        params["name"] = name
        filename_parts.append(f"name_{name.lower().replace(' ', '_')}")
    if country is not None:
        params["country"] = country
        filename_parts.append(f"country_{country.lower().replace(' ', '_')}")
    if code is not None:
        params["code"] = code
        filename_parts.append(f"code_{code.lower()}")
    if venue is not None:
        params["venue"] = venue
        filename_parts.append(f"venue_{venue}")
    if search is not None:
        params["search"] = search
        filename_parts.append(f"search_{search.lower().replace(' ', '_')}")

    filename = "_".join(filename_parts) + ".json"

    try:
        background_tasks.add_task(
            fetch_and_save_to_json, "/teams", filename, params=params
        )
        background_tasks.add_task(process_teams_json_and_save_to_db, filename)

        return {
            "message": f"Download e processamento de equipes iniciado em segundo plano. Arquivo: {filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
