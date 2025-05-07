from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.api.routes import patients, hint
from app.db.test_db import init_test_db, get_db

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifespan events for the FastAPI application."""
    # Initialize database on startup
    await init_test_db()
    yield

app = FastAPI(
    title="Central Patient Profile API",
    description="API for managing patient profiles",
    version="1.0.0",
    lifespan=lifespan
)

# Root health check route
@app.get("/")
def read_root():
    return {"message": "Central Patient Profile Service is running"}

# Include routers with prefixes
app.include_router(patients.router, prefix="/patients", tags=["patients"])
app.include_router(hint.router, prefix="/api", tags=["hint"])