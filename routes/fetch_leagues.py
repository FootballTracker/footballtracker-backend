from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
from integrations.save_json import fetch_and_save_to_json
from integrations.league_processor import process_league_json_and_save_to_db

router = APIRouter(prefix="/leagues", tags=["Leagues Fetch"])


@router.post("/fetch")
async def fetch_leagues(
    background_tasks: BackgroundTasks,
    id: Optional[int] = Query(None, description="The id of the league"),
    name: Optional[str] = Query(None, description="The name of the league"),
    country: Optional[str] = Query(None, description="The country name of the league"),
    code: Optional[str] = Query(
        None, min_length=2, max_length=6, description="The Alpha code of the country"
    ),
    season: Optional[int] = Query(
        None, description="The season of the league (e.g., 2023)"
    ),
    team: Optional[int] = Query(None, description="The id of the team"),
    type: Optional[str] = Query(
        None, description='The type of the league (e.g., "league", "cup")'
    ),
    current: Optional[str] = Query(
        None,
        description='Return the list of active seasons or the last... ("true", "false")',
    ),
    search: Optional[str] = Query(
        None, min_length=3, description="The name or the country of the league"
    ),
    last: Optional[int] = Query(
        None, le=2, description="The X last leagues/cups added in the API (<= 2)"
    ),
):
    """Endpoint para obter ligas e guardar num arquivo Json e no banco de dados"""
    params = {}
    filename_parts = ["leagues"]

    if id is not None:
        params["id"] = id
        filename_parts.append(f"id_{id}")
    if name is not None:
        params["name"] = name
        filename_parts.append(f"name_{name.lower().replace(' ', '_')}")
    if country is not None:
        params["country"] = country
        filename_parts.append(f"country_{country.lower().replace(' ', '_')}")
    if code is not None:
        params["code"] = code
        filename_parts.append(f"code_{code.lower()}")
    if season is not None:
        params["season"] = season
        filename_parts.append(f"season_{season}")
    if team is not None:
        params["team"] = team
        filename_parts.append(f"team_{team}")
    if type is not None:
        params["type"] = type
        filename_parts.append(f"type_{type.lower()}")
    if current is not None:
        params["current"] = current
        filename_parts.append(f"current_{current.lower()}")
    if search is not None:
        params["search"] = search
        filename_parts.append(f"search_{search.lower().replace(' ', '_')}")
    if last is not None:
        params["last"] = last
        filename_parts.append(f"last_{last}")

    filename = "_".join(filename_parts) + ".json"

    try:
        background_tasks.add_task(
            fetch_and_save_to_json, "/leagues", filename, params=params
        )
        background_tasks.add_task(process_league_json_and_save_to_db, filename)

        return {
            "message": f"Download e processamento de ligas iniciado em segundo plano. Arquivo: {filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
