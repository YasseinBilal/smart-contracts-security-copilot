from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import scans, analyze, explain, eval as eval_router


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield


app = FastAPI(
    title="Smart Contract Security Copilot",
    description="AI-powered smart contract vulnerability detection",
    version="0.1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(scans.router, prefix="/api", tags=["scans"])
app.include_router(analyze.router, prefix="/api", tags=["analyze"])
app.include_router(explain.router, prefix="/api", tags=["explain"])
app.include_router(eval_router.router, prefix="/api", tags=["eval"])


@app.get("/health")
async def health():
    return {"status": "ok"}
