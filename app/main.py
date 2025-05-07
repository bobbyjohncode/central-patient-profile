from fastapi import FastAPI
from app.api.routes import patients
from app.db.init_db import init_db
from app.db.test_db import get_test_db
import os

app = FastAPI(
    title="Central Patient Profile API",
    description="API for managing patient profiles",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    # Only initialize the real database if we're not in test mode
    if not os.getenv("TESTING"):
        init_db()

# Root health check route
@app.get("/")
def read_root():
    return {"message": "Central Patient Profile Service is running"}

# Include patients router with prefix
app.include_router(patients.router, prefix="/patients", tags=["patients"])