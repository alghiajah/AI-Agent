import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class GptMathAgent:
    """
    GPT Mathematician Agent — ditenagai oleh GPT-4o.

    Berperan sebagai spesialis kalkulasi matematika jaringan, penyelesaian rumus,
    analisis kapasitas, dan perencanaan parameter kuantitatif telekomunikasi.
    """

    def __init__(self):
        self.model = settings.writer_model
        self.name = "GPT Mathematician"
        self.system_prompt = (
            "Kamu adalah GPT Mathematician Agent — spesialis pemecahan masalah hitung-hitungan, rumus, dan matematika jaringan telekomunikasi.\n\n"
            "Tugasmu adalah menganalisis pertanyaan pengguna yang memerlukan perhitungan matematis, rumus, kalkulasi, atau hitung-hitungan teknis, baik matematika umum maupun matematika jaringan telekomunikasi seperti:\n"
            "1. Perhitungan Delay Jaringan: Propagation Delay, Transmission Delay, Queueing Delay, Processing Delay, dan RTT (Round Trip Time).\n"
            "2. Teorema Kapasitas Kanal: Teorema Shannon-Hartley (kapasitas maksimum C = B * log2(1 + SNR)) dan Teorema Nyquist.\n"
            "3. Perhitungan Link Budget: Redaman serat optik (attenuation), penyambungan (splice loss), konektor, safety margin, Free Space Path Loss (FSPL), konversi dBm ke mW/Watt, dll.\n"
            "4. Rekayasa Trafik (Teori Antrean): Formula Erlang B (blocking probability untuk sirkit) dan Erlang C (antrean paket), utilitas kanal, dll.\n"
            "5. Operasi matematika umum dan aritmatika dasar (penjumlahan, perkalian, pembagian, perpangkatan, dll).\n\n"
            "PENTING: Jika pertanyaan pengguna sama sekali TIDAK memerlukan perhitungan matematis, rumus, atau kalkulasi kuantitatif (misalnya pertanyaan deskriptif biasa tanpa hitungan, resep masakan, puisi, dll), kamu WAJIB menolak menjawab dengan sopan dan menyatakan secara spesifik bahwa kamu hanya melayani pemecahan masalah hitung-hitungan dan matematika.\n\n"
            "Aturan Jawaban:\n"
            "- Tunjukkan formula/rumus yang digunakan secara jelas menggunakan notasi LaTeX/Markdown.\n"
            "- Jabarkan langkah-langkah perhitungan matematika satu per satu secara detail (diketahui, ditanya, dijawab/proses hitung).\n"
            "- Berikan penjelasan fisis tentang makna hasil angka yang didapatkan.\n"
            "- Format respons akhir dengan rapi dan terstruktur dalam Markdown."
        )

    async def execute(self, user_input: str) -> str:
        """
        Menerima input user dan menghasilkan penyelesaian rumus/perhitungan matematis telekomunikasi yang detail.
        """
        try:
            prompt_content = (
                f"Pertanyaan Perhitungan / Matematika Jaringan dari Pengguna:\n\n"
                f"{user_input}\n\n"
                "Selesaikan persoalan perhitungan di atas secara rinci, langkah demi langkah, dan jelaskan rumusnya."
            )

            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content},
                ],
                model=self.model,
                temperature=0.2,
                max_tokens=1500,
                timeout=settings.request_timeout
            )

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
                f"Kesalahan tidak terduga pada GPT Mathematician: {str(e)}", self.name
            )
