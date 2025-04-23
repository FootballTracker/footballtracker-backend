import requests
import json
import os
from config import API_HOST, HEADERS
from typing import Optional


def fetch_and_save_to_json(endpoint: str, filename: str, params: Optional[dict] = None):
    url = f"https://{API_HOST}{endpoint}"
    json_dir = "json"

    if not os.path.exists(json_dir):
        os.makedirs(json_dir)

    file_path = os.path.join(json_dir, filename)

    if os.path.exists(file_path):
        print(f"Arquivo {file_path} já existe. Pulando chamada da API para {endpoint}.")
        return

    try:
        response = requests.get(url, headers=HEADERS, params=params)
        response.raise_for_status()

        data = response.json()

        with open(file_path, "w") as json_file:
            json.dump(data, json_file, indent=4)

        print(f"Dados salvos com sucesso de {endpoint} em: {file_path}")
    except requests.exceptions.RequestException as e:
        print(f"Erro na solicitação para {endpoint} com parâmetros {params}: {e}")
    except Exception as e:
        print(f"Erro ao processar os dados de {endpoint}: {e}")
