import asyncio
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from app.clients.gemini import get_gemini_model
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class AnalystAgent:
    """
    Analyst Agent — ditenagai oleh Gemini 2.5 Flash.

    Berperan sebagai analis teknis dan ilmiah yang sangat detail. Tugasnya adalah
    menerima 'Investigation Brief' dari Strategist Agent, lalu menggali setiap
    sudut pandang secara mendalam: mencari data faktual, membuat perbandingan,
    menemukan koneksi logis, dan menghasilkan analisis teknis yang kaya dan padat.
    """

    def __init__(self):
        self.model_name = settings.researcher_model
        self.name = "Analyst Agent"
        self.system_prompt = (
            "Kamu adalah Analyst Agent — seorang analis teknis dan ilmiah kelas dunia yang ditenagai oleh Gemini. "
            "Tugasmu adalah menerima 'Investigation Brief' dari Strategist Agent dan melakukan analisis mendalam.\n\n"
            "Cara kerja:\n"
            "1. Baca setiap sudut pandang investigasi dalam brief dengan seksama.\n"
            "2. Untuk SETIAP sudut pandang, gali informasi secara mendalam:\n"
            "   - Data kuantitatif, angka, statistik, spesifikasi teknis yang relevan.\n"
            "   - Perbandingan dan kontras antara konsep, teknologi, atau pendekatan.\n"
            "   - Mekanisme kerja internal dan alasan 'mengapa' sesuatu terjadi.\n"
            "   - Implikasi praktis, keunggulan, kelemahan, dan trade-off.\n"
            "3. Hasilkan 'Technical Analysis Report' yang padat, faktual, dan terstruktur per poin.\n\n"
            "Output WAJIB berupa laporan analisis teknis mentah yang kaya data — "
            "BUKAN tulisan percakapan. Ini adalah bahan baku untuk Communicator Agent."
        )

    async def execute(self, investigation_brief: str) -> str:
        """
        Menerima Investigation Brief dari Strategist dan menghasilkan
        Technical Analysis Report yang mendalam.
        """
        try:
            model_inst = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
            )

            response = await asyncio.wait_for(
                model_inst.generate_content_async(
                    contents=(
                        f"Investigation Brief dari Strategist Agent:\n\n"
                        f"{investigation_brief}\n\n"
                        "Lakukan analisis teknis mendalam berdasarkan setiap poin investigasi di atas. "
                        "Hasilkan Technical Analysis Report yang kaya data, faktual, dan terstruktur."
                    )
                ),
                timeout=settings.request_timeout,
            )

            if not response.text:
                raise AgentAPIException("Menerima respons kosong dari Gemini API.", self.name)

            return response.text.strip()

        except asyncio.TimeoutError:
            raise AgentTimeoutException(
                f"Panggilan API ke Gemini ({self.model_name}) mengalami timeout.", self.name
            )
        except google_exceptions.ResourceExhausted as e:
            # Fallback ke OpenRouter jika API direct Gemini kehabisan kuota (quota limit 429)
            try:
                # Menggunakan google/gemini-2.5-flash sebagai fallback utama di OpenRouter dengan fallback otomatis ke model gratis
                or_model = "google/gemini-2.5-flash"
                
                prompt_content = (
                    f"Investigation Brief dari Strategist Agent:\n\n"
                    f"{investigation_brief}\n\n"
                    "Lakukan analisis teknis mendalam berdasarkan setiap poin investigasi di atas. "
                    "Hasilkan Technical Analysis Report yang kaya data, faktual, dan terstruktur."
                )

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

            raise AgentRateLimitException(
                f"Batas rate-limit pada Gemini API terlampaui: {str(e)}", self.name
            )
        except google_exceptions.GoogleAPICallError as e:
            raise AgentAPIException(
                f"Kesalahan API Gemini: {str(e)}", self.name, status_code=getattr(e, "code", 500)
            )
        except Exception as e:
            raise AgentAPIException(
                f"Kesalahan tidak terduga pada Analyst Agent: {str(e)}", self.name
            )
