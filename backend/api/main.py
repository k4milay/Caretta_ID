from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from core.logging import configure_logging, get_logger
from api.routes import health, identify, turtles

configure_logging()
log = get_logger("api")


@asynccontextmanager
async def lifespan(_: FastAPI):
    log.info("CarettaID API starting")
    yield
    log.info("CarettaID API stopping")


app = FastAPI(
    title="CarettaID API",
    version="0.1.0",
    description="AI-powered Caretta caretta individual identification system.",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(identify.router)
app.include_router(turtles.router)
