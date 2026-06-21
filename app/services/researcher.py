import asyncio
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from app.clients.gemini import get_gemini_model
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException

class ResearchAgent:
    def __init__(self):
        self.model_name = settings.researcher_model
        self.name = "Research Agent"
        self.system_prompt = (
            "Kamu adalah Research Agent. Tugasmu adalah menerima rencana penelitian dari Supervisor Agent, "
            "memproses informasi tersebut secara logis, dan menghasilkan data teknis mentah, fakta, dan argumen berbasis logika yang solid.\n"
            "Jangan bertele-tele atau membuat format percakapan. Hasilkan data teknis sedalam mungkin dan sekomprehensif mungkin."
        )

    async def execute(self, research_plan: str) -> str:
        """
        Executes the Research Agent using Google Generative AI API based on the supervisor's research plan.
        """
        try:
            # Re-initialize the model to supply system instruction specifically for Research Agent
            model_inst = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt
            )
            
            # Execute async call to generate content with custom timeout
            response = await asyncio.wait_for(
                model_inst.generate_content_async(
                    contents=f"Rencana Penelitian:\n{research_plan}\n\nLakukan analisis riset teknis mendalam sesuai dengan rencana di atas."
                ),
                timeout=settings.request_timeout
            )
            
            if not response.text:
                raise AgentAPIException("Menerima respons kosong dari Gemini API.", self.name)
                
            return response.text.strip()
            
        except asyncio.TimeoutError:
            raise AgentTimeoutException(f"Panggilan API ke Gemini ({self.model_name}) mengalami timeout.", self.name)
        except google_exceptions.ResourceExhausted as e:
            # Fallback ke OpenRouter jika API direct Gemini kehabisan kuota (quota limit 429)
            try:
                # Menggunakan google/gemini-2.5-flash sebagai fallback utama di OpenRouter dengan fallback otomatis ke model gratis
                or_model = "google/gemini-2.5-flash"
                
                prompt_content = f"Rencana Penelitian:\n{research_plan}\n\nLakukan analisis riset teknis mendalam sesuai dengan rencana di atas."

                content, model_used = await openrouter_completion_with_fallback(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt_content},
                    ],
                    model=or_model,
                    temperature=0.2,
                    max_tokens=1500,
                    timeout=settings.request_timeout,
                )
                return content
            except Exception as or_err:
                # Jika OpenRouter juga gagal, biarkan melempar error asli rate limit
                pass

            raise AgentRateLimitException(f"Batas rate-limit pada Gemini API terlampaui: {str(e)}", self.name)
        except google_exceptions.GoogleAPICallError as e:
            raise AgentAPIException(f"Kesalahan API Gemini: {str(e)}", self.name, status_code=getattr(e, 'code', 500))
        except Exception as e:
            raise AgentAPIException(f"Kesalahan tidak terduga pada Research Agent: {str(e)}", self.name)
