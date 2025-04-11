import os
from dotenv import load_dotenv

load_dotenv()

API_HOST = "v3.football.api-sports.io"
API_KEY = os.getenv("API_KEY")

HEADERS = {"x-rapidapi-host": API_HOST, "x-rapidapi-key": API_KEY}
