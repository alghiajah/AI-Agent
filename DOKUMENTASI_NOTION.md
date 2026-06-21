# PANDUAN LENGKAP: Membangun Aplikasi Multi-Agent AI Orchestrator untuk Jaringan Telekomunikasi & TI

Selamat datang di panduan pembuatan **MADOKSEP (Multi-Agent AI Orchestrator)**! Dokumen ini dirancang khusus untuk memandu khalayak umum, mahasiswa, atau developer pemula dalam membangun sistem kecerdasan buatan multi-agent berbasis web menggunakan **FastAPI** (Backend) dan **HTML/CSS/JS Vanilla** (Frontend).

Sistem ini mengintegrasikan tiga model AI terkemuka (**DeepSeek-V3, Gemini 2.0/2.5 Flash, dan GPT-4o**) untuk berkolaborasi secara sekuensial (LLM Chaining) guna memecahkan masalah kompleks seputar Jaringan Telekomunikasi dan Teknologi Informasi. Dokumen ini dapat langsung Anda salin ke **Notion** sebagai dokumentasi proyek Anda.

---

## 📌 DAFTAR ISI
1. [Konsep & Arsitektur Sistem](#-1-konsep--arsitektur-sistem)
2. [Struktur Direktori Proyek](#-2-struktur-direktori-proyek)
3. [Langkah 1: Setup File Dependensi (`requirements.txt`)](#-langkah-1-setup-file-dependensi-requirementstxt)
4. [Langkah 2: Konfigurasi Variabel Lingkungan (`.env`)](#-langkah-2-konfigurasi-variabel-lingkungan-env)
5. [Langkah 3: File Konfigurasi Pydantic (`app/config.py`)](#-langkah-3-file-konfigurasi-pydantic-appconfigpy)
6. [Langkah 4: Penanganan Eror Kustom (`app/core/exceptions.py`)](#-langkah-4-penanganan-eror-kustom-appcoreexceptionspy)
7. [Langkah 5: Definisikan Skema Data (`app/schemas/chat.py`)](#-langkah-5-definisikan-skema-data-appschemaschatpy)
8. [Langkah 6: Database & Manajemen Sesi SQLite (`app/services/history.py`)](#-langkah-6-database--manajemen-sesi-sqlite-appserviceshistorypy)
9. [Langkah 7: Integrasi Klien API AI (`app/clients`)](#-langkah-7-integrasi-klien-api-ai-appclients)
10. [Langkah 8: Implementasi Agen AI & Spesialis (`app/services`)](#-langkah-8-implementasi-agen-ai--spesialis-appservices)
11. [Langkah 9: Engine Orkestrator AI (`app/services/orchestrator.py`)](#-langkah-9-engine-orkestrator-ai-appservicesorchestratorpy)
12. [Langkah 10: Routing & Controller API (`app/api`)](#-langkah-10-routing--controller-api-appapi)
13. [Langkah 11: Aplikasi Utama FastAPI (`app/main.py`)](#-langkah-11-aplikasi-utama-fastapi-appmainpy)
14. [Langkah 12: Halaman Frontend (Dashboard & Autentikasi)](#-langkah-12-halaman-frontend-dashboard--autentikasi)
15. [Langkah 13: Runner Script dengan Tunneling Ngrok (`run_server.py`)](#-langkah-13-runner-script-dengan-tunneling-ngrok-run_serverpy)
16. [Cara Menjalankan & Menggunakan Aplikasi](#-cara-menjalankan--menggunakan-aplikasi)

---

## 🧠 1. KONSEP & ARSITEKTUR SISTEM

Aplikasi ini menggunakan metode **LLM Chaining**, di mana output dari satu agen AI menjadi input bagi agen AI berikutnya. Alur kerja orkestrasi multi-agent ini adalah:

- **Strategist Agent (DeepSeek-V3 via OpenRouter)**: Bertugas menganalisis input user, memecahnya menjadi sudut pandang investigasi (teknis, praktis, historis), mendeteksi apakah pertanyaan keluar topik (*off-topic*), dan memformulasikan *Investigation Brief*.
- **Analyst Agent (Gemini 2.0/2.5 Flash Direct)**: Melakukan riset teknis yang sangat mendalam dan padat data berdasarkan panduan dari *Investigation Brief*. Jika kuota direct API habis, agent ini memiliki sistem resiliensi berupa *fallback* otomatis ke OpenRouter.
- **Communicator Agent (GPT-4o via OpenRouter)**: Mengemas laporan teknis mentah menjadi artikel penjelasan yang ramah dibaca pengguna, menggunakan analogi, tabel, dan format Markdown yang indah.

---

## 📁 2. STRUKTUR DIREKTORI PROYEK

Buat struktur folder berikut di komputer Anda sebelum memulai pengerjaan kode:

```text
TubesJartel2/
│
├── .env
├── requirements.txt
├── history.db (Akan terbuat otomatis)
├── run_server.py
│
└── app/
    ├── __init__.py
    ├── main.py
    ├── config.py
    │
    ├── api/
    │   ├── __init__.py
    │   ├── router.py
    │   └── v1/
    │       ├── __init__.py
    │       ├── auth.py
    │       └── endpoints.py
    │
    ├── clients/
    │   ├── __init__.py
    │   ├── gemini.py
    │   └── openrouter.py
    │
    ├── core/
    │   ├── __init__.py
    │   └── exceptions.py
    │
    ├── schemas/
    │   ├── __init__.py
    │   └── chat.py
    │
    ├── services/
    │   ├── __init__.py
    │   ├── history.py
    │   ├── orchestrator.py
    │   ├── strategist.py
    │   ├── analyst.py
    │   ├── communicator.py
    │   ├── deepseek_code.py
    │   ├── gemini_network.py
    │   └── gpt_math.py
    │
    └── templates/
        ├── auth.html
        └── index.html
```

---

## 📦 LANGKAH 1: Setup File Dependensi (`requirements.txt`)

Buat file bernama `requirements.txt` di root direktori proyek. File ini berisi daftar library Python yang dibutuhkan.

```text
fastapi>=0.110.0
uvicorn>=0.28.0
pydantic>=2.6.0
pydantic-settings>=2.2.0
openai>=1.14.0
google-generativeai>=0.4.0
python-dotenv>=1.0.1
httpx>=0.27.0
pyngrok>=7.1.0
```

---

## 🔑 LANGKAH 2: Konfigurasi Variabel Lingkungan (`.env`)

Buat file `.env` di root direktori untuk menyimpan konfigurasi server dan API key secara aman. **Ganti nilai API Key dengan kunci Anda sendiri**.

```env
# Environment Configurations
OPENROUTER_API_KEY=MASUKKAN_API_KEY_OPENROUTER_ANDA
GEMINI_API_KEY=MASUKKAN_API_KEY_GEMINI_ANDA
NGROK_AUTHTOKEN=MASUKKAN_AUTHTOKEN_NGROK_ANDA

# Model Names
SUPERVISOR_MODEL=deepseek/deepseek-chat
RESEARCHER_MODEL=gemini-2.0-flash
WRITER_MODEL=deepseek/deepseek-chat

# Server Configurations
HOST=0.0.0.0
PORT=8000
DEBUG=True
```

---

## ⚙️ LANGKAH 3: File Konfigurasi Pydantic (`app/config.py`)

File ini bertugas memuat variabel lingkungan dari file `.env` ke dalam object Python yang aman menggunakan library `pydantic-settings`.

```python
# app/config.py
import os
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field

class Settings(BaseSettings):
    openrouter_api_key: str = Field(..., alias="OPENROUTER_API_KEY")
    gemini_api_key: str = Field(..., alias="GEMINI_API_KEY")
    
    supervisor_model: str = Field("deepseek/deepseek-chat", alias="SUPERVISOR_MODEL")
    researcher_model: str = Field("gemini-2.0-flash", alias="RESEARCHER_MODEL")
    writer_model: str = Field("deepseek/deepseek-chat", alias="WRITER_MODEL")
    
    host: str = Field("0.0.0.0", alias="HOST")
    port: int = Field(8000, alias="PORT")
    debug: bool = Field(True, alias="DEBUG")
    
    # Global settings
    request_timeout: float = 120.0  # Timeouts untuk panggilan API eksternal (detik)

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

# Buat instansiasi settings sebagai singleton
settings = Settings()
```

---

## 🛡️ LANGKAH 4: Penanganan Eror Kustom (`app/core/exceptions.py`)

Aplikasi ini menggunakan API eksternal (Google Gemini & OpenRouter). File ini menangani resiliensi jika terjadi eror jaringan, timeout, atau kuota API habis.

```python
# app/core/exceptions.py
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("agent_orchestrator")

class AgentException(Exception):
    """Base exception untuk semua kegagalan pada agent."""
    def __init__(self, message: str, agent_name: str = "Unknown"):
        self.message = message
        self.agent_name = agent_name
        super().__init__(self.message)

class AgentTimeoutException(AgentException):
    """Dipicu ketika API model eksternal mengalami timeout."""
    pass

class AgentRateLimitException(AgentException):
    """Dipicu ketika API model eksternal membatasi request (HTTP 429)."""
    pass

class AgentAPIException(AgentException):
    """Dipicu untuk eror umum API eksternal."""
    def __init__(self, message: str, agent_name: str = "Unknown", status_code: int = 500):
        self.status_code = status_code
        super().__init__(message, agent_name)

def register_exception_handlers(app: FastAPI):
    """Mendaftarkan exception handler agar mengembalikan respon JSON yang rapi ke frontend."""
    @app.exception_handler(AgentTimeoutException)
    async def agent_timeout_handler(request: Request, exc: AgentTimeoutException):
        logger.error(f"Timeout exception pada {exc.agent_name} agent: {exc.message}")
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
        logger.error(f"Rate limit exception pada {exc.agent_name} agent: {exc.message}")
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
        logger.error(f"API exception pada {exc.agent_name} agent (status {exc.status_code}): {exc.message}")
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
        logger.error(f"Generic agent exception pada {exc.agent_name} agent: {exc.message}")
        return JSONResponse(
            status_code=500,
            content={
                "error": "Internal Agent Error",
                "message": f"Terjadi kesalahan internal pada pemrosesan '{exc.agent_name}' Agent.",
                "details": exc.message,
                "agent": exc.agent_name
            }
        )
```

---

## 📄 LANGKAH 5: Definisikan Skema Data (`app/schemas/chat.py`)

File ini mendefinisikan struktur request dan response menggunakan **Pydantic** untuk validasi tipe data otomatis pada endpoint API FastAPI.

```python
# app/schemas/chat.py
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(
        ..., 
        description="Pesan input dari user yang akan diproses.",
        examples=["Bagaimana cara kerja teknologi 5G?"]
    )
    mode: str = Field(
        "chain",
        description="Mode eksekusi: 'chain' (multi-agent), 'gemini_network', 'gpt_math', 'deepseek_code'."
    )
    session_id: Optional[str] = Field(
        None,
        description="ID Sesi percakapan untuk mengelompokkan chat dalam satu room."
    )

class AgentStep(BaseModel):
    agent_name: str = Field(..., description="Nama agen (Strategist, Analyst, Communicator).")
    model_used: str = Field(..., description="Model AI fisik yang digunakan.")
    output: str = Field(..., description="Output teks mentah dari agen ini.")
    execution_time_seconds: float = Field(..., description="Durasi pemrosesan agen (detik).")

class ChatResponse(BaseModel):
    status: str = Field("success", description="Status eksekusi API.")
    session_id: Optional[str] = Field(None, description="ID Sesi percakapan.")
    user_message: str = Field(..., description="Pesan asli dari user.")
    final_response: str = Field(..., description="Respons akhir yang telah dikemas indah.")
    steps: List[AgentStep] = Field(..., description="Log audit langkah demi langkah dari setiap agen.")
    total_execution_time_seconds: float = Field(..., description="Total durasi pemrosesan seluruh chain.")
```

---

## 🗄️ LANGKAH 6: Database & Manajemen Sesi SQLite (`app/services/history.py`)

Aplikasi ini menggunakan database **SQLite** lokal untuk menyimpan registrasi akun pengguna, sesi aktif (*cookie session*), dan riwayat chat yang dikelompokkan berdasarkan `session_id`.

*(Kode lengkap history.py telah diimplementasikan di folder app/services/history.py)*

---

## 🔌 LANGKAH 7: Integrasi Klien API AI (`app/clients`)

Langkah ini membuat interface komunikasi asinkron ke API Google Generative AI (Gemini) dan OpenRouter.

### A. Klien Gemini Direct SDK (`app/clients/gemini.py`)
```python
# app/clients/gemini.py
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.gemini_api_key)

def get_gemini_model(model_name: str = None) -> genai.GenerativeModel:
    name = model_name or settings.researcher_model
    return genai.GenerativeModel(name)
```

### B. Klien OpenRouter dengan Fallback Resilience (`app/clients/openrouter.py`)
*(Kode lengkap openrouter.py dengan fallback telah diimplementasikan di folder app/clients/openrouter.py)*

---

## 🤖 LANGKAH 8: Implementasi Agen AI & Spesialis (`app/services`)

### A. Strategist Agent (`app/services/strategist.py`)
*(StrategistAgent menggunakan model DeepSeek-V3 di OpenRouter)*

### B. Analyst Agent (`app/services/analyst.py`)
*(AnalystAgent menggunakan model Gemini 2.0/2.5 Flash Direct dengan fallback ke OpenRouter)*

### C. Communicator Agent (`app/services/communicator.py`)
*(CommunicatorAgent menggunakan model GPT-4o di OpenRouter)*

### D. Agen Spesialis Lainnya:
* **Gemini Network Analyst** (`app/services/gemini_network.py`)
* **GPT Mathematician** (`app/services/gpt_math.py`)
* **DeepSeek Coder** (`app/services/deepseek_code.py`)

---

## 🎛️ LANGKAH 9: Engine Orkestrator AI (`app/services/orchestrator.py`)

File ini bertugas mengoordinasikan eksekusi berantai (*chaining*) dari Strategist -> Analyst -> Communicator atau memanggil agen spesialis tunggal secara asinkron.

*(Kode lengkap orchestrator.py telah diimplementasikan di folder app/services/orchestrator.py)*

---

## 🛣️ LANGKAH 10: Routing & Controller API (`app/api`)

* **Router Utama** (`app/api/router.py`)
* **Controller Autentikasi** (`app/api/v1/auth.py`)
* **Endpoints Chat & History** (`app/api/v1/endpoints.py`)

---

## 🚀 LANGKAH 11: Aplikasi Utama FastAPI (`app/main.py`)

*(Konfigurasi CORS Middleware, routing, exception handling, dan web template hosting)*

---

## 🎨 LANGKAH 12: Halaman Frontend (Dashboard & Autentikasi)

* **Halaman Login/Register** (`app/templates/auth.html`)
* **Halaman Dashboard Chat Utama** (`app/templates/index.html`)

---

## 🌐 LANGKAH 13: Runner Script dengan Tunneling Ngrok (`run_server.py`)

*(Script runner otomatis menggunakan pyngrok untuk mempublikasikan server lokal ke internet)*

---

## 🛠️ CARA MENJALANKAN & MENGGUNAKAN APLIKASI

1. Aktifkan virtual environment:
   ```bash
   venv\Scripts\activate
   ```
2. Instal dependensi:
   ```bash
   pip install -r requirements.txt
   ```
3. Pastikan API key sudah dimasukkan di `.env`.
4. Jalankan script:
   ```bash
   python run_server.py
   ```
