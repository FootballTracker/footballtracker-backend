from fastapi import FastAPI
from routes import (
    auth,
    fetch_countries,
    fetch_fixtures,
    fetch_leagues,
    fetch_teams,
    fetch_venues,
    link_teams,
    fetch_players,
)


app = FastAPI()


app.include_router(auth.router)
app.include_router(fetch_countries.router)
app.include_router(fetch_venues.router)
app.include_router(fetch_leagues.router)
app.include_router(fetch_teams.router)
app.include_router(link_teams.router)
app.include_router(fetch_fixtures.router)
app.include_router(fetch_players.router)
