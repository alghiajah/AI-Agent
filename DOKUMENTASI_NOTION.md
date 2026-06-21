# PANDUAN PEMBUATAN: MULTI-AGENT AI ORCHESTRATOR (MADOKSEP)

Dokumen ini berisi panduan cara membuat **MADOKSEP (Multi-Agent AI Orchestrator)**. Kita akan membangun sistem asisten AI untuk Jaringan Telekomunikasi & TI menggunakan **FastAPI** di backend dan **HTML/CSS/JS Vanilla** di frontend.

Sistem ini mengintegrasikan tiga model AI yaitu **DeepSeek-V3, Gemini 2.0/2.5 Flash, dan GPT-4o** untuk bekerja secara berantai (LLM Chaining) guna memecahkan masalah kompleks seputar telekomunikasi.

---

## DAFTAR ISI
1. [Konsep & Cara Kerja Sistem](#konsep--cara-kerja-sistem)
2. [Struktur Folder Project](#struktur-folder-project)
3. [Langkah 1: Setup Dependensi (requirements.txt)](#langkah-1-setup-dependensi-requirementstxt)
4. [Langkah 2: Konfigurasi Environment (.env)](#langkah-2-konfigurasi-environment-env)
5. [Langkah 3: Konfigurasi App (app/config.py)](#langkah-3-konfigurasi-app-appconfigpy)
6. [Langkah 4: Penanganan Eror Kustom (app/core/exceptions.py)](#langkah-4-penanganan-eror-kustom-appcoreexceptionspy)
7. [Langkah 5: Definisikan Schema Data (app/schemas/chat.py)](#langkah-5-definisikan-schema-data-appschemaschatpy)
8. [Langkah 6: Database & Manajemen Sesi (app/services/history.py)](#langkah-6-database--manajemen-sesi-appserviceshistorypy)
9. [Langkah 7: Integrasi Klien API AI (app/clients)](#langkah-7-integrasi-klien-api-ai-appclients)
10. [Langkah 8: Implementasi Logic Agent (app/services)](#langkah-8-implementasi-logic-agent-appservices)
11. [Langkah 9: Engine Orkestrator (app/services/orchestrator.py)](#langkah-9-engine-orkestrator-appservicesorchestratorpy)
12. [Langkah 10: Routing & Controller API (app/api)](#langkah-10-routing--controller-api-appapi)
13. [Langkah 11: Main Application (app/main.py)](#langkah-11-aplikasi-utama-appmainpy)
14. [Langkah 12: Antarmuka Web (app/templates)](#langkah-12-antarmuka-web-apptemplates)
15. [Langkah 13: Script Runner Server (run_server.py)](#langkah-13-script-runner-server-run_serverpy)
16. [Cara Menjalankan Aplikasi](#cara-menjalankan-aplikasi)

---

## 1. KONSEP & CARA KERJA SISTEM

Aplikasi ini menggunakan konsep **LLM Chaining**, di mana output dari satu agent akan menjadi input untuk agent berikutnya. Alur kerja orkestrasi ini adalah:

* **Strategist Agent** (DeepSeek-V3 via OpenRouter): Menerima pertanyaan awal dari user, memecahnya menjadi beberapa poin riset (Investigation Brief), dan menyaring pertanyaan yang tidak sesuai dengan topik jaringan (off-topic).
* **Analyst Agent** (Gemini 2.0/2.5 Flash Direct): Mengambil brief dari Strategist Agent lalu melakukan riset teknis yang mendalam secara otomatis. Dilengkapi dengan fallback ke OpenRouter jika kuota direct API habis.
* **Communicator Agent** (GPT-4o via OpenRouter): Menyederhanakan laporan riset teknis kaku menjadi penjelasan yang mudah dipahami oleh pengguna umum, lengkap dengan format Markdown, tabel, atau analogi.

---

## 2. STRUKTUR FOLDER PROJECT

Gunakan struktur folder berikut untuk project Anda:

```text
TubesJartel2/
|-- .env
|-- requirements.txt
|-- history.db (Akan terbuat otomatis)
|-- run_server.py
|
|-- app/
    |-- __init__.py
    |-- main.py
    |-- config.py
    |
    |-- api/
    |   |-- __init__.py
    |   |-- router.py
    |   |-- v1/
    |       |-- __init__.py
    |       |-- auth.py
    |       |-- endpoints.py
    |
    |-- clients/
    |   |-- __init__.py
    |   |-- gemini.py
    |   |-- openrouter.py
    |
    |-- core/
    |   |-- __init__.py
    |   |-- exceptions.py
    |
    |-- schemas/
    |   |-- __init__.py
    |   |-- chat.py
    |
    |-- services/
        |-- __init__.py
        |-- history.py
        |-- orchestrator.py
        |-- strategist.py
        |-- analyst.py
        |-- communicator.py
        |-- deepseek_code.py
        |-- gemini_network.py
        |-- gpt_math.py
    |
    |-- templates/
        |-- auth.html
        |-- index.html
```

---

## 3. LANGKAH 1: SETUP DEPENDENSI (requirements.txt)

File `requirements.txt` berisi daftar library Python yang harus diinstal untuk menjalankan backend FastAPI dan integrasi model AI:

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

## 4. LANGKAH 2: KONFIGURASI ENVIRONMENT (.env)

Buat file `.env` di root folder project untuk menyimpan API key dan parameter konfigurasi dasar server secara aman:

```env
# API Key
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

## 5. LANGKAH 3: KONFIGURASI APP (app/config.py)

Buat file `app/config.py` untuk membaca variabel lingkungan dari file `.env` ke dalam object Python menggunakan Pydantic Settings:

```python
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
    request_timeout: float = 120.0

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()
```

---

## 6. LANGKAH 4: PENANGANAN EROR KUSTOM (app/core/exceptions.py)

File ini berisi exception kustom untuk menangani gangguan pada API eksternal (seperti timeout, rate limit, atau koneksi terputus) agar backend tidak crash dan tetap memberikan respon JSON yang jelas ke frontend:

```python
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import logging

logger = logging.getLogger("agent_orchestrator")

class AgentException(Exception):
    def __init__(self, message: str, agent_name: str = "Unknown"):
        self.message = message
        self.agent_name = agent_name
        super().__init__(self.message)

class AgentTimeoutException(AgentException):
    pass

class AgentRateLimitException(AgentException):
    pass

class AgentAPIException(AgentException):
    def __init__(self, message: str, agent_name: str = "Unknown", status_code: int = 500):
        self.status_code = status_code
        super().__init__(message, agent_name)

def register_exception_handlers(app: FastAPI):
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

## 7. LANGKAH 5: DEFINISIKAN SCHEMA DATA (app/schemas/chat.py)

Gunakan Pydantic untuk memvalidasi data request dan format response API:

```python
from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(..., description="Pesan dari user yang akan diproses.")
    mode: str = Field("chain", description="Mode eksekusi: 'chain' (multi-agent), 'gemini_network', 'gpt_math', 'deepseek_code'.")
    session_id: Optional[str] = Field(None, description="ID Sesi percakapan.")

class AgentStep(BaseModel):
    agent_name: str = Field(..., description="Nama agent.")
    model_used: str = Field(..., description="Model AI fisik yang digunakan.")
    output: str = Field(..., description="Output teks mentah dari agent.")
    execution_time_seconds: float = Field(..., description="Durasi pemrosesan agent (detik).")

class ChatResponse(BaseModel):
    status: str = Field("success", description="Status eksekusi API.")
    session_id: Optional[str] = Field(None, description="ID Sesi percakapan.")
    user_message: str = Field(..., description="Pesan asli dari user.")
    final_response: str = Field(..., description="Respons akhir dari Writer Agent.")
    steps: List[AgentStep] = Field(..., description="Audit logs dari setiap agent.")
    total_execution_time_seconds: float = Field(..., description="Total durasi pemrosesan.")
```

---

## 8. LANGKAH 6: DATABASE & MANAJEMEN SESI (app/services/history.py)

Gunakan SQLite untuk menyimpan data registrasi akun user, sesi aktif, dan riwayat obrolan:

*(Kode history.py lengkap dapat dilihat pada file proyek di `app/services/history.py`. File ini memproses database SQLite, fungsi password hashing menggunakan salt acak, dan pengelolaan history)*

---

## 9. LANGKAH 7: INTEGRASI KLIEN API AI (app/clients)

### A. Klien Gemini SDK (`app/clients/gemini.py`)
```python
import google.generativeai as genai
from app.config import settings

genai.configure(api_key=settings.gemini_api_key)

def get_gemini_model(model_name: str = None) -> genai.GenerativeModel:
    name = model_name or settings.researcher_model
    return genai.GenerativeModel(name)
```

### B. Klien OpenRouter (`app/clients/openrouter.py`)
*(Kode openrouter.py memproses integrasi ke OpenRouter menggunakan AsyncOpenAI dan memiliki mekanisme fallback otomatis ke model gratis dan API Gemini direct jika terjadi kegagalan sistem)*

---

## 10. LANGKAH 8: IMPLEMENTASI LOGIC AGENT (app/services)

Buat masing-masing kelas agent di folder `app/services/` dengan prompt dan target model yang berbeda:

* **Strategist Agent** (`app/services/strategist.py`): Bertugas membuat brief investigasi dan menyaring input non-telekomunikasi (`[OFFTOPIC]`).
* **Analyst Agent** (`app/services/analyst.py`): Bertugas melakukan analisis teknis secara asinkron.
* **Communicator Agent** (`app/services/communicator.py`): Mengubah teks riset mentah menjadi respon akhir Markdown.
* **Specialist Agent**:
  * `gemini_network.py` (Membahas teori jaringan)
  * `gpt_math.py` (Menangani kalkulasi rumus)
  * `deepseek_code.py` (Membuat skrip otomasi & koding)

---

## 11. LANGKAH 9: ENGINE ORKESTRATOR (app/services/orchestrator.py)

File ini bertugas memanggil agent secara berurutan sesuai mode yang dipilih oleh user:

*(Kode orchestrator.py lengkap mengoordinasikan pemrosesan dari Strategist ke Analyst ke Communicator, menghitung execution time per agent, dan menyimpan hasilnya ke database history)*

---

## 12. LANGKAH 10: ROUTING & CONTROLLER API (app/api)

Tulis router untuk backend agar dapat melayani request dari frontend:
* **Router Utama** (`app/api/router.py`)
* **Endpoint Autentikasi** (`app/api/v1/auth.py`): Menangani proses register, login, set session token cookie, dan get profil user.
* **Endpoint Obrolan** (`app/api/v1/endpoints.py`): Menangani endpoint `/agentic-chat` untuk orkestrasi dan manipulasi data history.

---

## 13. LANGKAH 11: MAIN APPLICATION (app/main.py)

File `app/main.py` mengintegrasikan API router, mengaktifkan CORS Middleware, meregistrasi handler eror kustom, dan menyajikan halaman web dari folder template:

*(Kode main.py lengkap mendaftarkan rute utama, melayani halaman dashboard jika cookie session_token valid, dan memproses logout)*

---

## 14. LANGKAH 12: ANTARMUKA WEB (app/templates)

* **auth.html**: Halaman minimalis untuk login dan registrasi dengan gradasi warna gelap modern.
* **index.html**: Halaman dashboard utama yang menampilkan ruang chat, menu dropdown spesialis, riwayat chat di sidebar, dan panel transparansi *Audit Trace* proses multi-agent.

---

## 15. LANGKAH 13: SCRIPT RUNNER SERVER (run_server.py)

Script ini digunakan untuk menyederhanakan proses startup dengan menjalankan server Uvicorn dan membuka tunnel Ngrok secara otomatis:

*(Kode run_server.py menggunakan pyngrok untuk membuat public URL secara otomatis saat server dimulai)*

---

## 16. CARA MENJALANKAN APLIKASI

1. **Buat Virtual Environment**:
   ```bash
   python -m venv venv
   ```
2. **Aktifkan Virtual Environment**:
   * Windows: `.\venv\Scripts\activate`
   * Linux/macOS: `source venv/bin/activate`
3. **Instal Library**:
   ```bash
   pip install -r requirements.txt
   ```
4. **Isi API Key**: Konfigurasi file `.env` dengan token API Anda.
5. **Jalankan Program**:
   ```bash
   python run_server.py
   ```
6. **Akses Aplikasi**: Buka browser Anda dan masukkan alamat local `http://127.0.0.1:8000` atau gunakan URL publik Ngrok yang tercantum pada terminal log.
