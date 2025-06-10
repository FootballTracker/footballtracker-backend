from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes import (
    auth,
    fetch_countries,
    fetch_fixtures,
    fetch_leagues,
    fetch_teams,
    fetch_venues,
    link_teams,
    fetch_players,
    leagues,
    fetch_classification_leagues,
    teams,
    fetch_coaches,
    fixture_routes,
    user_image
)

origins = [
    "http://localhost:3000",
    "http://localhost:8080",
]


app = FastAPI()

app.add_middleware(
  CORSMiddleware,
  allow_origins=origins,
  allow_credentials=True,
  allow_methods=['*'],
  allow_headers=['*']
)

app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(teams.router)
app.include_router(user_image.router)
app.include_router(fetch_countries.router)
app.include_router(fetch_venues.router)
app.include_router(fetch_leagues.router)
app.include_router(fetch_teams.router)
app.include_router(link_teams.router)
app.include_router(fetch_fixtures.router)
app.include_router(fetch_players.router)
app.include_router(fetch_classification_leagues.router)
app.include_router(fetch_coaches.router)
app.include_router(fixture_routes.router)
