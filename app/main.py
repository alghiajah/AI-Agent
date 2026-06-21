from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.api.router import api_router
from app.core.exceptions import register_exception_handlers

app = FastAPI(
    title="REST API Multi-Model Artificial Intelligence Terintegrasi",
    description=(
        "FastAPI Backend Orchestrator untuk Multi-Agent AI (LLM Chaining) "
        "yang menghubungkan DeepSeek (Supervisor), Gemini 1.5 Pro (Researcher), "
        "dan GPT-4o (Writer) secara asinkron dan sekuensial."
    ),
    version="1.0.0",
    debug=settings.debug
)

# Configure CORS Middleware (crucial for REST APIs used by frontend apps)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register custom exception handlers for external AI API error resilience
register_exception_handlers(app)

# Include core API router under '/api' prefix
app.include_router(api_router, prefix="/api")

from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi import Cookie
from typing import Optional
import os
from app.services.history import get_user_by_session, delete_session

@app.get("/", response_class=HTMLResponse, tags=["System"])
async def root(session_token: Optional[str] = Cookie(None)):
    """
    Serves the beautiful interactive Multi-Agent Orchestrator Web Dashboard.
    Redirects to /auth if the session token is missing or invalid.
    """
    if not session_token:
        return RedirectResponse(url="/auth", status_code=303)
    username = get_user_by_session(session_token)
    if not username:
        return RedirectResponse(url="/auth", status_code=303)
        
    template_path = os.path.join(os.path.dirname(__file__), "templates", "index.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Template index.html not found!</h1>", status_code=404)

@app.get("/auth", response_class=HTMLResponse, tags=["System"])
async def auth_page(session_token: Optional[str] = Cookie(None)):
    """
    Serves the Login & Register interface.
    Redirects to / if the user is already logged in.
    """
    if session_token:
        username = get_user_by_session(session_token)
        if username:
            return RedirectResponse(url="/", status_code=303)
            
    template_path = os.path.join(os.path.dirname(__file__), "templates", "auth.html")
    if os.path.exists(template_path):
        with open(template_path, "r", encoding="utf-8") as f:
            return HTMLResponse(content=f.read())
    return HTMLResponse(content="<h1>Template auth.html not found!</h1>", status_code=404)

@app.get("/logout", tags=["System"])
async def logout(session_token: Optional[str] = Cookie(None)):
    """
    Logs out the user by deleting the session from the DB and clearing the session cookie.
    """
    if session_token:
        delete_session(session_token)
    
    response = RedirectResponse(url="/auth", status_code=303)
    response.delete_cookie(key="session_token", path="/")
    return response

@app.get("/health", tags=["System"])
async def health():
    """
    Health check endpoint.
    """
    return {
        "status": "online",
        "models": {
            "supervisor": settings.supervisor_model,
            "researcher": settings.researcher_model,
            "writer": settings.writer_model
        }
    }
