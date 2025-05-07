from fastapi import FastAPI
from app.api.routes import patients
from app.db.init_db import init_db

app = FastAPI(
    title="Central Patient Profile API",
    description="API for managing patient profiles",
    version="1.0.0"
)

@app.on_event("startup")
async def startup_event():
    init_db()

# Root health check route
@app.get("/")
def read_root():
    return {"message": "Central Patient Profile Service is running"}

# Include patients router with prefix
app.include_router(patients.router, prefix="/patients", tags=["patients"])