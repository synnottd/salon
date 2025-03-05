from fastapi import APIRouter
from app.api.api_v1.endpoints import voice, appointments, auth

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(voice.router, prefix="/voice", tags=["voice"])
api_router.include_router(appointments.router, prefix="/appointments", tags=["appointments"]) 