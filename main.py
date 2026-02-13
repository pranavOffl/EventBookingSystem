from fastapi import FastAPI
from app.api.v1.routers import api_router

app = FastAPI(
    title="Event Booking API",
    description="Event Booking API for managing events and bookings.",
    version="1.0.0",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc"
)

app.include_router(api_router, prefix="/api/v1")

@app.get("/")
async def root():
    return {"message": "Backend is up and running!"}
