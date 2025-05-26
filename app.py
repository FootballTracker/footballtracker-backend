from fastapi import FastAPI, Request
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
    teams
)


app = FastAPI()

# ----- ADDING CONNECTION ERROR HANDLING -----
# @app.exception_handler(asyncpg.exceptions.CannotConnectNowError)
# async def db_connection_error_handler(request: Request, exc: asyncpg.exceptions.CannotConnectNowError):
#     return JSONResponse(
#         status_code=503,
#         content={"detail": "Conexão com o banco falhou."},
#     )


app.include_router(auth.router)
app.include_router(leagues.router)
app.include_router(fetch_countries.router)
app.include_router(fetch_venues.router)
app.include_router(fetch_leagues.router)
app.include_router(fetch_teams.router)
app.include_router(link_teams.router)
app.include_router(fetch_fixtures.router)
app.include_router(fetch_players.router)
app.include_router(fetch_classification_leagues.router)
app.include_router(teams.router)
