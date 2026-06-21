import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException

class SupervisorAgent:
    def __init__(self):
        self.model = settings.supervisor_model
        self.name = "Supervisor Agent"
        self.system_prompt = (
            "Kamu adalah Supervisor Agent. Tugasmu adalah menganalisis input pengguna, "
            "mengidentifikasi intent utama, memecah masalah menjadi sub-bagian logis, "
            "dan merumuskan rencana penelitian terperinci untuk Research Agent.\n"
            "Output yang kamu hasilkan harus terstruktur, logis, fokus pada poin-poin penting penelitian, "
            "dan langsung ke inti permasalahan tanpa basa-basi percakapan."
        )

    async def execute(self, user_input: str) -> str:
        """
        Executes the Supervisor Agent to analyze the user input and produce a research plan.
        """
        try:
            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": f"User Input: {user_input}\n\nBuatkan rencana penelitian terperinci untuk Research Agent berdasarkan input di atas."}
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1000,
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
            raise AgentAPIException(f"Kesalahan tidak terduga pada Supervisor Agent: {str(e)}", self.name)
