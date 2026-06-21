from fastapi import APIRouter, Response, HTTPException, status, Cookie
from pydantic import BaseModel, Field
from app.services.history import register_user, verify_user_credentials, create_session

router = APIRouter()

class UserAuthPayload(BaseModel):
    username: str = Field(..., min_length=3, max_length=50)
    password: str = Field(..., min_length=4)

@router.post("/register")
async def register(payload: UserAuthPayload):
    username = payload.username.lower().strip()
    if not username.isalnum():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username hanya boleh berisi huruf dan angka saja."
        )
    success = register_user(username, payload.password)
    if not success:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username sudah terdaftar atau terjadi kesalahan."
        )
    return {"status": "success", "message": "Registrasi berhasil! Silakan masuk."}

@router.post("/login")
async def login(payload: UserAuthPayload, response: Response):
    username = payload.username.lower().strip()
    valid = verify_user_credentials(username, payload.password)
    if not valid:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Username atau password salah."
        )
    try:
        token = create_session(username)
        response.set_cookie(
            key="session_token",
            value=token,
            httponly=True,
            max_age=604800,  # 7 hari
            path="/",
            samesite="lax",
            secure=False
        )
        return {"status": "success", "message": "Login berhasil!"}
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Terjadi kesalahan saat membuat sesi: {str(e)}"
        )

@router.get("/me")
async def get_me(session_token: str = Cookie(None)):
    if not session_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak ditemukan."
        )
    from app.services.history import get_user_by_session
    username = get_user_by_session(session_token)
    if not username:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Sesi tidak valid."
        )
    return {"status": "success", "username": username}
