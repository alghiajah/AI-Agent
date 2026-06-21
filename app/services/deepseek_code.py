import asyncio
from openai import RateLimitError, APIStatusError
from app.clients.openrouter import openrouter_completion_with_fallback
from app.config import settings
from app.core.exceptions import AgentTimeoutException, AgentRateLimitException, AgentAPIException


class DeepseekCodeAgent:
    """
    DeepSeek Code Agent — ditenagai oleh DeepSeek-V3.

    Berperan sebagai spesialis pemrograman, penulisan script otomasi jaringan,
    konfigurasi perangkat keras, debugging, dan dokumentasi implementasi kode jaringan.
    """

    def __init__(self):
        self.model = settings.supervisor_model
        self.name = "DeepSeek Coder"
        self.system_prompt = (
            "Kamu adalah DeepSeek Code Agent — spesialis pemrograman, koding, scripting, dan otomasi jaringan.\n\n"
            "Tugasmu adalah membantu pengguna menulis, memformat, menganalisis, dan men-debug kode pemrograman untuk berbagai keperluan (baik pemrograman umum maupun scripting otomasi jaringan), terutama berkaitan dengan:\n"
            "1. Pemrograman Umum: Kode program dalam berbagai bahasa (Python, JavaScript, C/C++, Java, dll), termasuk pembuatan program sederhana/game, algoritma, struktur data, dan aplikasi desktop/web.\n"
            "2. Skrip Otomasi Jaringan: Skrip Python menggunakan pustaka Netmiko, Paramiko, Nornir, Netaddr, IPAddress, Scapy, atau playbook Ansible untuk mengotomasi konfigurasi perangkat.\n"
            "3. Socket Programming: Skrip Client-Server berbasis TCP atau UDP.\n"
            "4. Templating Konfigurasi: Pembuatan file konfigurasi perangkat jaringan (Cisco IOS, Cisco NX-OS, Juniper Junos, Mikrotik RouterOS, Fortinet, dll) dari file template.\n"
            "5. Skrip Pengolahan Log: Regex atau skrip parsing data log jaringan (syslog, pcap parsing, dll).\n\n"
            "PENTING: Jika pertanyaan pengguna sama sekali TIDAK berkaitan dengan pemrograman, koding, penulisan script, otomasi, debugging, atau pembuatan file konfigurasi (misalnya pertanyaan teori deskriptif tanpa kodingan sama sekali, resep masakan, puisi, dll), kamu WAJIB menolak menjawab dengan sopan dan menyatakan secara spesifik bahwa kamu hanya melayani pembuatan kode program, koding, scripting, dan debugging.\n\n"
            "Aturan Penulisan Kode:\n"
            "- Sertakan komentar penjelasan yang komprehensif pada baris-baris kode penting.\n"
            "- Gunakan format blok kode Markdown dengan bahasa pemrograman yang sesuai (misal: ```python, ```bash, ```yaml, dll).\n"
            "- Pastikan kode aman, menangani exception (error handling), dan efisien.\n"
            "- Berikan panduan cara menjalankan kode atau skrip tersebut."
        )

    async def execute(self, user_input: str) -> str:
        """
        Menerima input user dan menghasilkan solusi pemrograman/skrip/konfigurasi jaringan yang lengkap.
        """
        try:
            prompt_content = (
                f"Permintaan Pemrograman / Kode Jaringan dari Pengguna:\n\n"
                f"{user_input}\n\n"
                "Tuliskan solusi kode pemrograman, otomasi, atau konfigurasi jaringan yang lengkap, bersih, dan berikan penjelasan cara kerjanya."
            )

            content, model_used = await openrouter_completion_with_fallback(
                messages=[
                    {"role": "system", "content": self.system_prompt},
                    {"role": "user", "content": prompt_content},
                ],
                model=self.model,
                temperature=0.3,
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
                f"Kesalahan tidak terduga pada DeepSeek Coder: {str(e)}", self.name
            )
