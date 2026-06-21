from fastapi import APIRouter
from app.api.v1.endpoints import router as chat_router
from app.api.v1.auth import router as auth_router

api_router = APIRouter()

# Include under versioned /v1 prefix: /api/v1/agentic-chat
api_router.include_router(chat_router, prefix="/v1", tags=["Multi-Agent Chain (V1)"])
api_router.include_router(auth_router, prefix="/v1/auth", tags=["Authentication (V1)"])

# Also include directly under base /api prefix: /api/agentic-chat for convenience
api_router.include_router(chat_router, tags=["Multi-Agent Chain (Direct)"])
api_router.include_router(auth_router, prefix="/auth", tags=["Authentication (Direct)"])
