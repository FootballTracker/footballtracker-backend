from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Query
from typing import Optional
from database.database import get_db_session, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from integrations.save_json import fetch_and_save_to_json
from integrations.venues_processor import process_venues_json_and_save_to_db
from models import (
    base_coach,
    base_player,
    base_team,
    country,
    fixture_lineup,
    fixture_player_stat,
    fixture_statistic,
    fixture,
    league_classification,
    league,
    league_team,
    player_season_stat,
    venue,
)

app = FastAPI()


@app.post("/fetch-countries")
async def fetch_countries(background_tasks: BackgroundTasks):
    """Endpoint para obter os paises e guardar num arquivo Json"""
    try:
        background_tasks.add_task(
            fetch_and_save_to_json("/countries", "countries.json")
        )
        return {"message": "Download dos países iniciada em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/fetch-venues")
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


@app.post("/save_venues_in_db")
async def save_venues_in_db(background_tasks: BackgroundTasks):
    """Endpoint para salvar os estadios no banco de dados"""
    try:
        background_tasks.add_task(
            process_venues_json_and_save_to_db, "venues_country_brazil.json"
        )
        return {"message": "Processamento dos estadios iniciado em segundo plano"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root(db: AsyncSession = Depends(get_db_session)):
    return {"message": "Conexão establecida com o banco de dados"}
