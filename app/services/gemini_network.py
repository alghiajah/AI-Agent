import asyncio
import google.generativeai as genai
from google.api_core import exceptions as google_exceptions
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class GeminiNetworkAgent:
    """
    Gemini Network Analyst Agent — ditenagai oleh Gemini 2.5 Flash.

    Berperan sebagai spesialis pencarian, analisis, dan teori jaringan telekomunikasi.
    Tugasnya adalah memberikan analisis komprehensif mengenai arsitektur, protokol,
    dan performa jaringan telekomunikasi.
    """

    def __init__(self):
        self.model_name = settings.researcher_model
        self.name = "Gemini Network Analyst"
        self.system_prompt = (
            "Kamu adalah Gemini Network Analyst Agent — spesialis pencarian, analisis mendalam, "
            "dan teori jaringan telekomunikasi.\n\n"
            "Tugasmu adalah menganalisis pertanyaan pengguna terkait jaringan telekomunikasi dengan fokus pada:\n"
            "1. Protokol jaringan (seperti TCP/IP, BGP, OSPF, SIP, MPLS, HTTP/HTTPS, dll).\n"
            "2. Arsitektur jaringan telekomunikasi (seperti 5G, 4G LTE, FTTH/Serat Optik, SD-WAN, Cloud Networking, IoT, dll).\n"
            "3. Indikator performa jaringan (seperti latency, jitter, throughput, packet loss, bandwidth, QoS/QoE).\n"
            "4. Perbandingan antar teknologi (kelebihan, kekurangan, trade-off, dan use case).\n\n"
            "PENTING: Jika pertanyaan pengguna sama sekali TIDAK berkaitan dengan jaringan telekomunikasi, protokol, arsitektur, atau performa jaringan (misalnya resep makanan, matematika murni di luar jaringan, kodingan umum di luar konfigurasi jaringan, puisi, dll), kamu WAJIB menolak menjawab dengan sopan dan menyatakan secara spesifik bahwa kamu hanya melayani pertanyaan seputar analisis dan teori jaringan telekomunikasi.\n\n"
            "Berikan jawaban yang analitis, faktual, mendalam, kaya data, dan terstruktur rapi menggunakan format Markdown. "
            "Gunakan tabel, diagram alur teks, atau analogi jika mempermudah penjelasan konsep."
        )

    async def execute(self, user_input: str) -> str:
        """
        Menerima input user dan menghasilkan analisis jaringan yang mendalam.
        """
        try:
            model_inst = genai.GenerativeModel(
                model_name=self.model_name,
                system_instruction=self.system_prompt,
            )

            response = await asyncio.wait_for(
                model_inst.generate_content_async(
                    contents=(
                        f"Pertanyaan Jaringan Telekomunikasi dari Pengguna:\n\n"
                        f"{user_input}\n\n"
                        "Lakukan analisis jaringan mendalam sesuai keahlianmu berdasarkan prompt di atas."
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
                or_model = "google/gemini-2.5-flash"
                prompt_content = (
                    f"Pertanyaan Jaringan Telekomunikasi dari Pengguna:\n\n"
                    f"{user_input}\n\n"
                    "Lakukan analisis jaringan mendalam sesuai keahlianmu berdasarkan prompt di atas."
                )

                content, model_used = await openrouter_completion_with_fallback(
                    messages=[
                        {"role": "system", "content": self.system_prompt},
                        {"role": "user", "content": prompt_content},
                    ],
                    model=or_model,
                    temperature=0.3,
                    max_tokens=1500,
                    timeout=settings.request_timeout,
                )
                return content
            except Exception as or_err:
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
                f"Kesalahan tidak terduga pada Gemini Network Analyst: {str(e)}", self.name
            )
