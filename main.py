from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path

from models.database import init_db
from api import routes


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(
    title="StonxBuddy API",
    description="The Deliberately Biased Stock Analyst",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(routes.router, prefix="/api", tags=["api"])
app.mount("/static", StaticFiles(directory="web"), name="static")


@app.get("/")
async def root():
    return FileResponse("web/index.html")


@app.get("/health")
async def health():
    return {"status": "healthy"}
