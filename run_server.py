import os
import sys
import time
import subprocess
from pyngrok import ngrok
from dotenv import load_dotenv

def main():
    # Load environment variables
    load_dotenv()
    
    # Set ngrok authtoken if available in environment
    ngrok_authtoken = os.environ.get("NGROK_AUTHTOKEN")
    if ngrok_authtoken:
        try:
            ngrok.set_auth_token(ngrok_authtoken)
            print("[NGROK STATUS] Authtoken berhasil dikonfigurasi dari .env.")
        except Exception as e:
            print(f"[NGROK WARNING] Gagal mengatur authtoken: {e}")
            
    port = int(os.environ.get("PORT", 8000))
    host = os.environ.get("HOST", "127.0.0.1")
    
    # We should run uvicorn locally on 127.0.0.1 so ngrok can tunnel to it,
    # even if HOST is set to 0.0.0.0 in .env.
    uvicorn_host = "127.0.0.1" if host == "0.0.0.0" else host

    print("=" * 70)
    print("Multi-Agent AI Orchestrator - Web Server Startup")
    print("=" * 70)
    print("Membuka terowongan Ngrok...")
    
    public_url = None
    try:
        # Connect ngrok tunnel to the local port
        tunnel = ngrok.connect(port, "http")
        public_url = tunnel.public_url
        print(f"\n[NGROK STATUS] Terowongan berhasil dibuka!")
        print(f"-> URL Publik (Web): {public_url}")
        print("Anda dapat membagikan atau membuka URL ini di browser mana saja.\n")
    except Exception as e:
        print(f"\n[NGROK WARNING] Gagal membuka terowongan Ngrok: {e}")
        print("Catatan: Pastikan Anda telah mengatur authtoken Ngrok jika diperlukan:")
        print("  ngrok config add-authtoken <TOKEN_ANDA>")
        print("Server lokal akan tetap dijalankan, namun tidak dapat diakses dari luar jaringan lokal.\n")

    print(f"Memulai server FastAPI (Uvicorn) pada http://{uvicorn_host}:{port}...")
    print("=" * 70)

    # Launch uvicorn as a subprocess to keep the main process responsive
    cmd = [
        sys.executable, "-u", "-m", "uvicorn", "app.main:app",
        "--host", uvicorn_host,
        "--port", str(port)
    ]
    
    proc = subprocess.Popen(cmd)

    try:
        # Loop to keep the script running and check the server health
        while True:
            time.sleep(1)
            if proc.poll() is not None:
                print("Server Uvicorn terhenti secara tidak terduga.")
                break
    except KeyboardInterrupt:
        print("\nMenerima sinyal berhenti (Ctrl+C). Membersihkan proses...")
    finally:
        # Clean shutdown of uvicorn
        print("Menghentikan server Uvicorn...")
        proc.terminate()
        try:
            proc.wait(timeout=5)
        except subprocess.TimeoutExpired:
            print("Server Uvicorn tidak merespons, memaksa berhenti...")
            proc.kill()
            
        # Clean shutdown of ngrok
        if public_url:
            print("Menutup terowongan Ngrok...")
            try:
                ngrok.disconnect(public_url)
                ngrok.kill()
            except Exception as e:
                print(f"Gagal menutup ngrok secara bersih: {e}")
                
        print("Semua proses berhasil dihentikan. Sampai jumpa!")

if __name__ == "__main__":
    main()
