from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .config import settings
from .routers import games, scorers, teams


app = FastAPI(title="Baseball Scoring API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)
app.include_router(teams.router)
app.include_router(games.router)
app.include_router(scorers.router)
