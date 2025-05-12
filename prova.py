from config import API_HOST, HEADERS
import requests


def get_rate_limit_status():
    url = f"https://{API_HOST}/status"
    try:
        response = requests.get(url, headers=HEADERS)
        response.raise_for_status()
        data = response.json()
        print(data)
        if "errors" in data and "requests" in data["errors"]:
            error_msg = data["errors"]["requests"]
            if "You have reached the request limit" in error_msg:
                print("Limite de requisições detectado pela mensagem de erro da API.")
                return 100
        return data["response"]["requests"]["current"]
    except Exception as e:
        print(f"Erro ao obter o status da API: {e}")
        return None


get_rate_limit_status()
