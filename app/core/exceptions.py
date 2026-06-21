from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("agent_orchestrator")

class AgentException(Exception):
    """Base exception for all agent-related failures."""
    def __init__(self, message: str, agent_name: str = "Unknown"):
        self.message = message
        self.agent_name = agent_name
        super().__init__(self.message)

class AgentTimeoutException(AgentException):
    """Raised when an external AI API call times out."""
    pass

class AgentRateLimitException(AgentException):
    """Raised when an external AI API call returns a rate limit error (HTTP 429)."""
    pass

class AgentAPIException(AgentException):
    """Raised when an external AI API returns a generic error."""
    def __init__(self, message: str, agent_name: str = "Unknown", status_code: int = 500):
        self.status_code = status_code
        super().__init__(message, agent_name)

def register_exception_handlers(app: FastAPI):
    """
    Registers exception handlers to map custom agent exceptions to clean HTTP responses.
    """
    @app.exception_handler(AgentTimeoutException)
    async def agent_timeout_handler(request: Request, exc: AgentTimeoutException):
        logger.error(f"Timeout exception in {exc.agent_name} agent: {exc.message}")
        return JSONResponse(
            status_code=504,
            content={
                "error": "Gateway Timeout",
                "message": f"Koneksi ke API model pada '{exc.agent_name}' Agent mengalami timeout.",
                "details": exc.message,
                "agent": exc.agent_name
            }
        )

    @app.exception_handler(AgentRateLimitException)
    async def agent_rate_limit_handler(request: Request, exc: AgentRateLimitException):
        logger.error(f"Rate limit exception in {exc.agent_name} agent: {exc.message}")
        return JSONResponse(
            status_code=429,
            content={
                "error": "Too Many Requests",
                "message": f"Batas pemanggilan API (Rate Limit) terlampaui pada '{exc.agent_name}' Agent. Silakan coba beberapa saat lagi.",
                "details": exc.message,
                "agent": exc.agent_name
            }
        )

    @app.exception_handler(AgentAPIException)
    async def agent_api_handler(request: Request, exc: AgentAPIException):
        logger.error(f"API exception in {exc.agent_name} agent (status {exc.status_code}): {exc.message}")
        return JSONResponse(
            status_code=502,
            content={
                "error": "Bad Gateway",
                "message": f"Terjadi kesalahan komunikasi dengan model AI pihak ketiga pada '{exc.agent_name}' Agent.",
                "details": exc.message,
                "agent": exc.agent_name
            }
        )

    @app.exception_handler(AgentException)
    async def agent_generic_handler(request: Request, exc: AgentException):
        logger.error(f"Generic agent exception in {exc.agent_name} agent: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Agent Error",
                "message": f"Terjadi kesalahan internal pada pemrosesan '{exc.agent_name}' Agent.",
                "details": exc.message,
                "agent": exc.agent_name
            }
        )
