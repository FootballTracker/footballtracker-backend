import time
import requests
import json
import os
from datetime import datetime
from config import API_HOST, HEADERS
from typing import Optional


JSON_DIR = "json"
RATE_LIMIT_FILE = os.path.join(JSON_DIR, "rate_limit.json")


def is_rate_limit_reached():
    if not os.path.exists(RATE_LIMIT_FILE):
        return False
    with open(RATE_LIMIT_FILE, "r") as f:
        data = json.load(f)
        return data.get("current_requests") == 100


def get_rate_limit_status():
    url = f"https://{API_HOST}/status"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        if "errors" in data and "requests" in data["errors"]:
            error_msg = data["errors"]["requests"]
            if "You have reached the request limit" in error_msg:
                print("Limite de requisições detectado pela mensagem de erro da API.")
                return 100
        return data["response"]["requests"]["current"]
    except Exception as e:
        print(f"Erro ao obter o status da API: {e}")
        return None


def load_rate_limit_data():
    if os.path.exists(RATE_LIMIT_FILE):
        with open(RATE_LIMIT_FILE, "r") as f:
            return json.load(f)
    return {"last_id": None, "current_requests": 0}


def save_rate_limit_data(last_id, current_requests):
    with open(RATE_LIMIT_FILE, "w") as f:
        json.dump(
            {
                "last_id": last_id,
                "current_requests": current_requests,
                "timestamp": datetime.now().isoformat(),
            },
            f,
            indent=4,
        )


def fetch_and_save_to_json(endpoint: str, filename: str, params: Optional[dict] = None):
    url = f"https://{API_HOST}{endpoint}"

    if not os.path.exists(JSON_DIR):
        os.makedirs(JSON_DIR)

    file_path = os.path.join(JSON_DIR, filename)

    if os.path.exists(file_path):
        print(f"Arquivo {file_path} já existe. Pulando chamada da API para {endpoint}.")
        return

    current_requests = get_rate_limit_status()
    if current_requests is not None and current_requests >= 100:
        print("Limite de requisições atingido. Processo interrompido")
        save_rate_limit_data(params.get("id", None), current_requests)
        return

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json()

        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Dados salvos com sucesso de {endpoint} em: {file_path}")

        current_requests += 1
        save_rate_limit_data(params.get("id", None), current_requests)

        time.sleep(30)

    except requests.exceptions.RequestException as e:
        print(f"Erro na solicitação para {endpoint} com parâmetros {params}: {e}")
        save_rate_limit_data(params.get("id", None), current_requests)
    except Exception as e:
        print(f"Erro ao processar os dados de {endpoint}: {e}")
        save_rate_limit_data(params.get("id", None), current_requests)
