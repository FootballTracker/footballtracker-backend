from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
from integrations.save_json import fetch_and_save_to_json
from integrations.venues_processor import process_venues_json_and_save_to_db

router = APIRouter(prefix="/venues", tags=["Venues"])


@router.post("/fetch")
async def fetch_venues(
    background_tasks: BackgroundTasks,
    id: Optional[int] = Query(None, description="Filtrar por id do estadio"),
    name: Optional[str] = Query(None, description="Filtrar pelo nome do estadio"),
    city: Optional[str] = Query(None, description="Filtrar pela cidade do estadio"),
    country: Optional[str] = Query(None, description="Filtrar pelo pais do estadio"),
    search: Optional[str] = Query(
        None, description="Nome, cidade ou pais do estadio", min_length=3
    ),
):
    """Endpoint para obter os estadios e guardar num arquivo Json"""
    params = {}
    filename_parts = ["venues"]

    if id is not None:
        params["id"] = id
        filename_parts.append(f"id_{id}")
    if name is not None:
        params["name"] = name
        filename_parts.append(f"name_{name.lower().replace(' ', '_')}")
    if city is not None:
        params["city"] = city
        filename_parts.append(f"city_{city.lower().replace(' ', '_')}")
    if country is not None:
        params["country"] = country
        filename_parts.append(f"country_{country.lower().replace(' ', '_')}")
    if search is not None:
        params["search"] = search
        filename_parts.append(f"search_{search.lower().replace(' ', '_')}")

    filename = "_".join(filename_parts) + ".json"

    try:
        background_tasks.add_task(
            fetch_and_save_to_json, "/venues", filename, params=params
        )
        return {"message": "Download dos estadios iniciada em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/save")
async def save_venues_in_db(background_tasks: BackgroundTasks):
    """Endpoint para salvar os estadios no banco de dados"""
    try:
        background_tasks.add_task(
            process_venues_json_and_save_to_db, "venues_country_brazil.json"
        )
        return {"message": "Processamento dos estadios iniciado em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
