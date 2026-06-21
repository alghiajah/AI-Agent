import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class CommunicatorAgent:
    """
    Communicator Agent — ditenagai oleh GPT-4o.

    Berperan sebagai penulis konten profesional dan komunikator handal. Tugasnya
    adalah menerima 'Technical Analysis Report' dari Analyst Agent beserta pertanyaan
    asli user, lalu mengubah data teknis mentah tersebut menjadi sebuah narasi yang
    mengalir, mudah dipahami, menarik secara visual (Markdown), dan benar-benar
    menjawab apa yang user tanyakan.
    """

    def __init__(self):
        self.model = settings.writer_model
        self.name = "Communicator Agent"
        self.system_prompt = (
            "Kamu adalah Communicator Agent — seorang penulis konten profesional dan komunikator ahli yang ditenagai oleh GPT-4o. "
            "Tugasmu adalah mengambil laporan analisis teknis mentah dari Analyst Agent dan "
            "mengubahnya menjadi konten yang luar biasa bagi pengguna akhir.\n\n"
            "Cara kerja:\n"
            "1. Pahami pertanyaan asli pengguna — inilah yang HARUS dijawab.\n"
            "2. Gunakan data dari Technical Analysis Report sebagai sumber fakta.\n"
            "3. Susun respons dengan struktur narasi yang mengalir dan logis:\n"
            "   - Mulai dengan penjelasan konsep utama yang mudah dipahami.\n"
            "   - Sertakan detail teknis penting namun dalam bahasa yang accessible.\n"
            "   - Gunakan analogi, contoh nyata, atau perbandingan untuk memperjelas.\n"
            "   - Akhiri dengan insight atau takeaway yang bermakna bagi user.\n"
            "4. Format dengan Markdown yang indah: gunakan heading, bold, bullet points, "
            "numbered list, dan tabel jika diperlukan.\n\n"
            "Output ADALAH respons akhir yang langsung dibaca oleh pengguna — "
            "buat semenarik, sejelah, dan seprofesional mungkin."
        )

    async def execute(self, user_original_message: str, analysis_report: str) -> str:
        """
        Menerima pertanyaan asli user dan Technical Analysis Report dari Analyst,
        lalu menghasilkan respons akhir yang menarik dan mudah dipahami.
        """
        try:
            prompt_content = (
                f"Pertanyaan Asli Pengguna:\n{user_original_message}\n\n"
                f"Technical Analysis Report dari Analyst Agent:\n{analysis_report}\n\n"
                "Susun respons akhir yang komprehensif, menarik, dan mudah dipahami "
                "untuk menjawab pertanyaan pengguna berdasarkan data analisis di atas. "
                "Gunakan format Markdown yang indah dan profesional."
            )

            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content},
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=1500,
                timeout=settings.request_timeout
            )
            
            # Update nama model agar audit log / trace step menampilkan model yang sebenarnya digunakan
            self.model = model_used
            return content
        except Exception as e:
            raise AgentAPIException(
                f"Kesalahan tidak terduga pada Communicator Agent: {str(e)}", self.name
            )
