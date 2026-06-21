import asyncio
import httpx
import sys

# Set UTF-8 encoding for Windows command prompt to support printing unicode characters
if sys.platform == 'win32':
    sys.stdout.reconfigure(encoding='utf-8')

async def test_mode(mode: str, message: str):
    url = "http://127.0.0.1:8000/api/agentic-chat"
    payload = {
        "message": message,
        "mode": mode
    }
    
    print(f"\n==================================================")
    print(f"Menguji Mode: {mode}")
    print(f"Pesan: {message}")
    print(f"==================================================")
    
    async with httpx.AsyncClient(timeout=180.0) as client:
        try:
            response = await client.post(url, json=payload)
            print(f"Status Code: {response.status_code}")
            if response.status_code == 200:
                data = response.json()
                print("\n=== RESPON AKHIR ===")
                print(data["final_response"][:500] + ("..." if len(data["final_response"]) > 500 else ""))
                print("\n=== AUDIT LOG / TRACE STEPS ===")
                for step in data["steps"]:
                    print(f"Agent: {step['agent_name']}")
                    print(f"Model: {step['model_used']}")
                    print(f"Waktu Eksekusi: {step['execution_time_seconds']} detik")
                    print("-" * 50)
                print(f"Total Waktu Orkestrasi: {data['total_execution_time_seconds']} detik")
            else:
                print("Terjadi Kesalahan (Non-200 Response):")
                print(response.text)
        except Exception as e:
            print(f"Koneksi gagal atau terjadi error: {e}")

async def main():
    # Jalankan test untuk semua mode
    await test_mode(
        "chain", 
        "Jelaskan singkat perbedaan 4G dan 5G."
    )
    await test_mode(
        "gemini_network", 
        "Jelaskan apa itu protokol routing BGP."
    )
    await test_mode(
        "gpt_math", 
        "Hitung propagation delay untuk kabel serat optik 100 km jika kecepatan rambat v = 2 x 10^8 m/s."
    )
    await test_mode(
        "deepseek_code", 
        "Tulis kode python socket programming TCP server sederhana."
    )

if __name__ == "__main__":
    asyncio.run(main())
