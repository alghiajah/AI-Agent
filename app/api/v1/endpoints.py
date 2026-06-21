from fastapi import APIRouter, Depends, HTTPException, status, Cookie
from typing import Optional
from app.schemas.chat import ChatRequest, ChatResponse
from app.services.orchestrator import AgentOrchestrator
from app.services.history import get_history, clear_history, get_user_by_session

router = APIRouter()

def get_orchestrator() -> AgentOrchestrator:
    """
    Dependency injection helper to retrieve the orchestrator service instance.
    """
    return AgentOrchestrator()

async def get_current_user(session_token: Optional[str] = Cookie(None)) -> str:
    """
    Dependency helper to check cookie session_token, verify session validity,
    and return the corresponding username.
    """
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak ditemukan. Silakan masuk terlebih dahulu."
        )
    username = get_user_by_session(session_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid atau telah kedaluwarsa. Silakan masuk kembali."
        )
    return username

@router.post("/agentic-chat", response_model=ChatResponse)
async def agentic_chat(
    payload: ChatRequest,
    username: str = Depends(get_current_user),
    orchestrator: AgentOrchestrator = Depends(get_orchestrator)
) -> ChatResponse:
    """
    Endpoint utama untuk interaksi Multi-Agent (LLM Chaining) secara sekuensial dan asinkron,
    atau mengeksekusi agen spesifik tunggal sesuai mode tugas yang dipilih.
    Mendukung database chat history yang terikat ke username pengguna.
    """
    return await orchestrator.run_chain(payload.message, payload.mode, payload.session_id, username=username)

@router.get("/history")
async def get_chat_history(username: str = Depends(get_current_user)):
    """
    Endpoint untuk mengambil seluruh riwayat percakapan unik milik user yang login.
    """
    return get_history(username)

@router.get("/history/{session_id}")
async def get_session_history(session_id: str, username: str = Depends(get_current_user)):
    """
    Endpoint untuk mengambil seluruh percakapan dalam satu sesi/room berdasarkan session_id milik user yang login.
    """
    from app.services.history import get_session_messages
    return get_session_messages(session_id, username)

@router.delete("/history")
async def clear_chat_history(username: str = Depends(get_current_user)):
    """
    Endpoint untuk menghapus seluruh riwayat percakapan milik user yang login.
    """
    clear_history(username)
    return {"status": "success", "message": "Riwayat percakapan berhasil dihapus."}

