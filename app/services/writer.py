import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException

class WriterAgent:
    def __init__(self):
        self.model = settings.writer_model
        self.name = "Writer Agent"
        self.system_prompt = (
            "Kamu adalah Writer Agent. Tugasmu adalah menerima data teknis mentah dari Research Agent "
            "dan menyusun respons akhir yang ramah, profesional, rapi, terstruktur, dan mudah dipahami oleh pengguna.\n"
            "Gunakan format markdown yang menarik (seperti bold, bullet points, numbering, atau tabel jika diperlukan). "
            "Pastikan respons akhir ini menjawab pertanyaan awal pengguna dengan lengkap dan jelas."
        )

    async def execute(self, user_original_message: str, research_data: str) -> str:
        """
        Executes the Writer Agent to compile raw research data into a polished final response.
        """
        try:
            prompt_content = (
                f"Pertanyaan Awal Pengguna: {user_original_message}\n\n"
                f"Data Teknis Mentah dari Research Agent:\n{research_data}\n\n"
                f"Susun respons akhir yang komprehensif, terstruktur, dan indah dalam format markdown berdasarkan informasi di atas."
            )
            
            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content}
                ],
                model=self.model,
                temperature=0.7,
                max_tokens=1500,
                timeout=settings.request_timeout
            )
            
            # Update nama model agar audit log / trace step menampilkan model yang sebenarnya digunakan
            self.model = model_used
            return content
            
        except asyncio.TimeoutError:
            raise AgentTimeoutException(f"Panggilan API ke OpenRouter ({self.model}) mengalami timeout.", self.name)
        except RateLimitError as e:
            raise AgentRateLimitException(f"Batas rate-limit pada OpenRouter terlampaui: {str(e)}", self.name)
        except APIStatusError as e:
            raise AgentAPIException(f"Kesalahan status API OpenRouter: {str(e)}", self.name, status_code=e.status_code)
        except Exception as e:
            raise AgentAPIException(f"Kesalahan tidak terduga pada Writer Agent: {str(e)}", self.name)
