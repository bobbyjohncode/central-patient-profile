from contextlib import asynccontextmanager
from fastapi import FastAPI
from app.api.routes import patients
from app.db.init_db import init_db
from app.db.test_db import get_test_db
import os

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    if not os.getenv("TESTING"):
        init_db()
    yield
    # Shutdown
    pass

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

# Include patients router with prefix
app.include_router(patients.router, prefix="/patients", tags=["patients"])