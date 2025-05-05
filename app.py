from fastapi import FastAPI, Depends, BackgroundTasks, HTTPException, Query
from typing import Optional
from database.database import get_db_session, engine, Base
from sqlalchemy.ext.asyncio import AsyncSession
from integrations.save_json import fetch_and_save_to_json
from integrations.venues_processor import process_venues_json_and_save_to_db
from integrations.league_processor import process_league_json_and_save_to_db
from integrations.teams_processor import process_teams_json_and_save_to_db
from integrations.league_teams_processor import link_teams_to_league_and_venues
from integrations.fixtures_processor import process_fixtures_json_and_save_to_db
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

from routes import auth, leagues

app = FastAPI()


@app.post("/fetch-countries")
async def fetch_countries(background_tasks: BackgroundTasks):
    """Endpoint para obter os paises e guardar num arquivo Json"""
    try:
        background_tasks.add_task(
            fetch_and_save_to_json, "/countries", "countries.json"
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


@app.post("/fetch-leagues")
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


@app.post("/fetch-teams")
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


@app.post("/link-teams-to-league")
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


@app.post("/fetch-fixtures")
async def fetch_fixtures(
    background_tasks: BackgroundTasks,
    id: Optional[int] = Query(None, description="O id da partida"),
    ids: Optional[str] = Query(
        None, description="Máximo de 20 ids de partidas (ex: 123-456-789)"
    ),
    live: Optional[str] = Query(
        None,
        description='Todos ou vários ids de ligas para partidas ao vivo (ex: "all", "123-456")',
    ),
    date: Optional[str] = Query(None, description="Uma data válida (YYYY-MM-DD)"),
    league: Optional[int] = Query(None, description="O id da liga"),
    season: Optional[int] = Query(None, description="A temporada da liga (ex: 2023)"),
    team: Optional[int] = Query(None, description="O id da equipe"),
    last: Optional[int] = Query(
        None, le=20, description="Para as X últimas partidas (<= 20)"
    ),
    next: Optional[int] = Query(
        None, le=20, description="Para as X próximas partidas (<= 20)"
    ),
    from_date: Optional[str] = Query(
        None, description="Uma data válida de início (YYYY-MM-DD)"
    ),
    to_date: Optional[str] = Query(
        None, description="Uma data válida de fim (YYYY-MM-DD)"
    ),
    round: Optional[str] = Query(None, description="A rodada da partida"),
    status: Optional[str] = Query(
        None, description='Um ou mais status curtos da partida (ex: "NS", "HT-FT")'
    ),
    venue: Optional[int] = Query(None, description="O id do estádio da partida"),
    timezone: Optional[str] = Query(
        None, description="Um fuso horário válido do endpoint Timezone"
    ),
):
    """Endpoint para baixar dados de partidas da API e salvar em um arquivo JSON."""
    params = {}
    filename_parts = ["fixtures"]

    # Adiciona parâmetros se não forem None e constrói partes do nome do arquivo
    if id is not None:
        params["id"] = id
        filename_parts.append(f"id_{id}")
    if ids is not None:
        params["ids"] = ids
        filename_parts.append(f"ids_{ids.replace('-', '_')}")
    if live is not None:
        params["live"] = live
        filename_parts.append(f"live_{live.replace('-', '_')}")
    if date is not None:
        params["date"] = date
        filename_parts.append(f"date_{date}")
    if league is not None:
        params["league"] = league
        filename_parts.append(f"league_{league}")
    if season is not None:
        params["season"] = season
        filename_parts.append(f"season_{season}")
    if team is not None:
        params["team"] = team
        filename_parts.append(f"team_{team}")
    if last is not None:
        params["last"] = last
        filename_parts.append(f"last_{last}")
    if next is not None:
        params["next"] = next
        filename_parts.append(f"next_{next}")
    if from_date is not None:
        params["from"] = from_date
        filename_parts.append(f"from_{from_date}")
    if to_date is not None:
        params["to"] = to_date
        filename_parts.append(f"to_{to_date}")
    if round is not None:
        params["round"] = round
        cleaned_round = (
            round.lower().replace(" ", "_").replace("-", "_").replace(":", "_")
        )
        filename_parts.append(f"round_{cleaned_round}")
    if status is not None:
        params["status"] = status
        filename_parts.append(f"status_{status.lower().replace('-', '_')}")
    if venue is not None:
        params["venue"] = venue
        filename_parts.append(f"venue_{venue}")
    if timezone is not None:
        params["timezone"] = timezone
        filename_parts.append(f"timezone_{timezone.lower().replace('/', '_')}")

    # Constrói o nome do arquivo dinamicamente ou usa um padrão
    if len(filename_parts) > 1:
        filename = "_".join(filename_parts) + ".json"
    else:
        filename = "fixtures_data.json"  # Nome padrão se nenhum filtro for usado

    try:
        # Lança a tarefa de download e salvamento em JSON
        background_tasks.add_task(
            fetch_and_save_to_json, "/fixtures", filename, params=params
        )

        return {
            "message": f"Download de partidas iniciado em segundo plano. Arquivo: {filename}"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- Rota para processar o arquivo JSON de partidas e salvar no banco de dados ---


@app.post("/process-fixtures")
async def process_fixtures(
    background_tasks: BackgroundTasks,
    file_name: str = Query(
        ...,
        description="Nome do arquivo JSON de partidas a ser processado (dentro da pasta json/)",
    ),
):
    """Endpoint para processar um arquivo JSON de partidas e salvar os dados no banco de dados."""
    try:
        # Lança a tarefa de processamento e salvamento no banco de dados
        background_tasks.add_task(process_fixtures_json_and_save_to_db, file_name)

        return {
            "message": f"Processamento da partida do arquivo '{file_name}' iniciado em segundo plano para salvar no banco de dados."
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/")
async def root(db: AsyncSession = Depends(get_db_session)):
    return {"message": "Conexão establecida com o banco de dados"}


app.include_router(auth.router, prefix="/auth", tags=["auth"])
app.include_router(leagues.router, prefix="/leagues", tags=['league'])