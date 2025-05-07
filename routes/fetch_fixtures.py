from fastapi import APIRouter, BackgroundTasks, HTTPException, Query
from typing import Optional
import os
import json
from integrations.save_json import fetch_and_save_to_json, is_rate_limit_reached
from integrations.fixtures_processor import process_fixtures_json_and_save_to_db

router = APIRouter(prefix="/fixtures", tags=["Fixtures"])


@router.post("/fetch")
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


@router.post("/save")
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


# Rota para automatizar a coleta de dados de cada uma das partidas desde um arquivo json


@router.post("/fetch_from_json")
async def fetch_from_json_file(
    background_task: BackgroundTasks,
    source_file: str = Query(
        ..., description="Nome do arquivo JSON base (obrigatório)"
    ),
):
    file_path = os.path.join("json", source_file)

    if not os.path.exists(file_path):
        raise HTTPException(
            status_code=404, detail=f"Arquivo {source_file} não encontrado."
        )

    with open(file_path, "r") as file:
        data = json.load(file)

    fixtures = data.get("response", [])
    if not fixtures:
        raise HTTPException(
            status_code=404, detail="Nenhuma partida encontrada no arquivo."
        )

    ids_list = [
        fixture["fixture"]["id"]
        for fixture in fixtures
        if isinstance(fixture.get("fixture", {}).get("id"), int)
    ]

    folder = "fetched"
    os.makedirs(folder, exist_ok=True)

    for fixture_id in ids_list:
        if is_rate_limit_reached():
            print("Limite atingido, parando o agendamento de tarefas.")
            break
        filename = f"fixture_{fixture_id}.json"
        filepath = os.path.join(folder, filename)
        background_task.add_task(
            fetch_and_save_to_json,
            "/fixtures",
            filepath,
            {"id": fixture_id},
        )

    return {
        "message": "Tarefas iniciadas para download de partidas a partir do JSON.",
        "arquivo_origem": source_file,
        "quantidade_ids": len(ids_list),
    }
