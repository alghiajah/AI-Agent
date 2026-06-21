import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class StrategistAgent:
    """
    Strategist Agent — ditenagai oleh DeepSeek-V3.

    Berperan sebagai konsultan strategi yang handal. Tugasnya adalah menerima
    pertanyaan dari user, memecahnya menjadi beberapa sudut pandang investigasi
    yang komprehensif (teknis, praktis, komparatif, kontekstual), dan menghasilkan
    'brief' terstruktur yang akan menjadi panduan mendalam bagi Analyst Agent.
    """

    def __init__(self):
        self.model = settings.supervisor_model
        self.name = "Strategist Agent"
        self.system_prompt = (
            "Kamu adalah Strategist Agent — seorang konsultan strategi berpengalaman yang ditenagai oleh DeepSeek. "
            "Tugasmu adalah menerima pertanyaan dari pengguna dan merancang sebuah 'Investigation Brief' yang komprehensif.\n\n"
            "Cara kerja:\n"
            "1. Identifikasi intent utama dan subtopik kunci dari pertanyaan user.\n"
            "2. Pecah pertanyaan menjadi 3-5 sudut pandang investigasi yang berbeda dan saling melengkapi "
            "(misalnya: sudut teknis, sudut perbandingan, sudut dampak praktis, sudut sejarah/konteks, sudut masa depan).\n"
            "3. Untuk setiap sudut pandang, tuliskan secara spesifik apa yang perlu digali dan dianalisis.\n"
            "4. Tetapkan prioritas dan fokus investigasi utama.\n\n"
            "PENTING: Jika pertanyaan pengguna sama sekali TIDAK berkaitan dengan Jaringan Telekomunikasi, Jaringan Komputer, atau Teknologi Informasi/Komunikasi (misalnya resep masakan, puisi, olahraga, geografi umum, dll), kamu WAJIB mengembalikan output teks berisi satu kata saja yaitu: [OFFTOPIC]. Jangan menulis penjelasan apa pun selain itu.\n\n"
            "Output WAJIB berupa 'Investigation Brief' yang terstruktur dan langsung ke poin — "
            "BUKAN percakapan atau respons kepada user. Ini adalah instruksi internal untuk Analyst Agent."
        )

    async def execute(self, user_input: str) -> str:
        """
        Menerima input user dan menghasilkan Investigation Brief terstruktur
        untuk diteruskan ke Analyst Agent.
        """
        try:
            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {
                        "role": "user",
                        "content": (
                            f"Pertanyaan User: {user_input}\n\n"
                            "Buatkan Investigation Brief yang komprehensif dan terstruktur "
                            "untuk memandu Analyst Agent dalam menggali topik ini secara mendalam."
                        ),
                    },
                ],
                model=self.model,
                temperature=0.3,
                max_tokens=1000,
                timeout=settings.request_timeout
            )

            # Update nama model agar audit log / trace step menampilkan model yang sebenarnya digunakan
            self.model = model_used
            return content

        except asyncio.TimeoutError:
            raise AgentTimeoutException(
                f"Panggilan API ke OpenRouter ({self.model}) mengalami timeout.", self.name
            )
        except RateLimitError as e:
            raise AgentRateLimitException(
                f"Batas rate-limit pada OpenRouter terlampaui: {str(e)}", self.name
            )
        except APIStatusError as e:
            raise AgentAPIException(
                f"Kesalahan status API OpenRouter: {str(e)}", self.name, status_code=e.status_code
            )
        except Exception as e:
            raise AgentAPIException(
                f"Kesalahan tidak terduga pada Strategist Agent: {str(e)}", self.name
            )
