from pydantic import BaseModel, Field
from typing import List, Optional

class ChatRequest(BaseModel):
    message: str = Field(
        ..., 
        description="Pesan input dari user yang akan dianalisis dan diproses oleh multi-agent chain.",
        examples=["Bagaimana cara kerja teknologi 5G dan apa perbedaannya dengan 4G dalam hal latensi?"]
    )
    mode: str = Field(
        "chain",
        description="Mode eksekusi: 'chain' (multi-agent), 'gemini_network', 'gpt_math', 'deepseek_code'.",
        examples=["chain"]
    )
    session_id: Optional[str] = Field(
        None,
        description="ID Sesi percakapan (untuk mengelompokkan chat dalam satu room).",
        examples=["session-12345"]
    )

class AgentStep(BaseModel):
    agent_name: str = Field(..., description="Nama agen (Supervisor, Researcher, Writer).")
    model_used: str = Field(..., description="Model AI fisik yang digunakan oleh agen.")
    output: str = Field(..., description="Output teks mentah dari agen ini.")
    execution_time_seconds: float = Field(..., description="Durasi pemrosesan agen dalam hitungan detik.")

class ChatResponse(BaseModel):
    status: str = Field("success", description="Status eksekusi API.")
    session_id: Optional[str] = Field(None, description="ID Sesi percakapan yang diasosiasikan.")
    user_message: str = Field(..., description="Pesan asli dari user.")
    final_response: str = Field(..., description="Respons akhir yang natural, rapi, dan terformat (markdown) dari Writer Agent.")
    steps: List[AgentStep] = Field(..., description="Log audit/trace langkah demi langkah dari setiap agen.")
    total_execution_time_seconds: float = Field(..., description="Total durasi pemrosesan seluruh chain.")
