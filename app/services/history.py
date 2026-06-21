import sqlite3
import json
import os
import hashlib
from datetime import datetime, timedelta
from typing import Optional

# Simpan database history.db di root directory proyek
DB_PATH = os.path.abspath(
    os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
        "history.db"
    )
)


def hash_password(password: str) -> str:
    """
    Menghasilkan password hash aman dengan sha256 + salt acak.
    """
    salt = os.urandom(16).hex()
    hash_val = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return f"{salt}:{hash_val}"


def verify_password(password: str, hashed_password: str) -> bool:
    """
    Memverifikasi password plain dengan password hash tersimpan.
    """
    if not hashed_password or ":" not in hashed_password:
        return False
    salt, hash_val = hashed_password.split(":")
    calc_hash = hashlib.sha256((password + salt).encode("utf-8")).hexdigest()
    return calc_hash == hash_val


def init_db():
    """
    Menginisialisasi tabel database SQLite jika belum ada.
    """
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # 1. Tabel users untuk registrasi & login
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL
        )
        """
    )
    
    # 2. Tabel sessions untuk menyimpan session_token login
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS sessions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            token TEXT UNIQUE NOT NULL,
            username TEXT NOT NULL,
            expires_at TEXT NOT NULL
        )
        """
    )
    
    # 3. Tabel chat_history untuk menyimpan log percakapan per user
    cursor.execute(
        """
        CREATE TABLE IF NOT EXISTS chat_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL DEFAULT '',
            session_id TEXT NOT NULL DEFAULT '',
            timestamp TEXT NOT NULL,
            mode TEXT NOT NULL,
            user_message TEXT NOT NULL,
            final_response TEXT NOT NULL,
            steps TEXT NOT NULL
        )
        """
    )
    conn.commit()
    
    # Cek dan jalankan auto-migrasi kolom session_id & username jika tabel sudah ada sebelumnya
    cursor.execute("PRAGMA table_info(chat_history)")
    columns = [col[1] for col in cursor.fetchall()]
    
    if "session_id" not in columns:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN session_id TEXT NOT NULL DEFAULT ''")
        conn.commit()
        
    if "username" not in columns:
        cursor.execute("ALTER TABLE chat_history ADD COLUMN username TEXT NOT NULL DEFAULT ''")
        conn.commit()
        
    conn.close()


def register_user(username: str, password_plain: str) -> bool:
    """
    Mendaftarkan user baru ke database. Mengembalikan False jika username sudah ada.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Cek apakah username sudah dipakai
        cursor.execute("SELECT id FROM users WHERE username = ?", (username.lower().strip(),))
        if cursor.fetchone():
            conn.close()
            return False
            
        hashed = hash_password(password_plain)
        cursor.execute(
            "INSERT INTO users (username, password_hash) VALUES (?, ?)",
            (username.lower().strip(), hashed)
        )
        conn.commit()
        conn.close()
        return True
    except Exception as e:
        print(f"[DB Error] Gagal meregistrasi user: {e}")
        return False


def verify_user_credentials(username: str, password_plain: str) -> bool:
    """
    Memverifikasi apakah username & password benar.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT password_hash FROM users WHERE username = ?", (username.lower().strip(),))
        row = cursor.fetchone()
        conn.close()
        if not row:
            return False
        return verify_password(password_plain, row[0])
    except Exception as e:
        print(f"[DB Error] Gagal memverifikasi user: {e}")
        return False


def create_session(username: str) -> str:
    """
    Membuat token sesi login baru dan menyimpannya di DB (berlaku 7 hari).
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        token = os.urandom(24).hex()
        expires_at = (datetime.now() + timedelta(days=7)).isoformat()
        
        cursor.execute(
            "INSERT INTO sessions (token, username, expires_at) VALUES (?, ?, ?)",
            (token, username.lower().strip(), expires_at)
        )
        conn.commit()
        conn.close()
        return token
    except Exception as e:
        print(f"[DB Error] Gagal membuat sesi: {e}")
        raise e


def get_user_by_session(token: str) -> Optional[str]:
    """
    Memeriksa validitas token sesi dan mengembalikan username pemilik sesi.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT username, expires_at FROM sessions WHERE token = ?", (token,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            expires = datetime.fromisoformat(row[1])
            if expires > datetime.now():
                return row[0]
        return None
    except Exception as e:
        print(f"[DB Error] Gagal memeriksa token sesi: {e}")
        return None


def delete_session(token: str):
    """
    Menghapus sesi login dari database (logout).
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM sessions WHERE token = ?", (token,))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Error] Gagal menghapus sesi: {e}")


def add_chat(username: str, session_id: str, mode: str, user_message: str, final_response: str, steps: list):
    """
    Menambahkan entri percakapan baru milik user tertentu ke dalam riwayat.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        timestamp = datetime.now().isoformat()
        
        # Konversi steps (list of Pydantic models atau dict) ke serialisasi JSON string
        steps_list = []
        for step in steps:
            if hasattr(step, 'agent_name'):
                steps_list.append({
                    "agent_name": step.agent_name,
                    "model_used": step.model_used,
                    "output": step.output,
                    "execution_time_seconds": step.execution_time_seconds
                })
            else:
                steps_list.append(step)
            
        steps_json = json.dumps(steps_list)
        
        cursor.execute(
            "INSERT INTO chat_history (username, session_id, timestamp, mode, user_message, final_response, steps) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (username.lower().strip(), session_id, timestamp, mode, user_message, final_response, steps_json)
        )
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Error] Gagal menyimpan riwayat chat: {e}")


def get_history(username: str):
    """
    Mengambil daftar percakapan unik milik user tertentu dikelompokkan per session_id (pesan pertama per sesi),
    diurutkan dari yang terbaru.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        cursor.execute(
            """
            SELECT id, session_id, timestamp, mode, user_message, final_response, steps 
            FROM chat_history 
            WHERE username = ? AND id IN (
                SELECT MIN(id) 
                FROM chat_history 
                GROUP BY session_id
            )
            ORDER BY id DESC
            """,
            (username.lower().strip(),)
        )
        rows = cursor.fetchall()
        conn.close()
        
        history = []
        for row in rows:
            sess_id = row["session_id"] if row["session_id"] else f"session-{row['id']}"
            history.append({
                "id": row["id"],
                "session_id": sess_id,
                "timestamp": row["timestamp"],
                "mode": row["mode"],
                "user_message": row["user_message"],
                "final_response": row["final_response"],
                "steps": json.loads(row["steps"])
            })
        return history
    except Exception as e:
        print(f"[DB Error] Gagal mengambil riwayat chat: {e}")
        return []


def get_session_messages(session_id: str, username: str):
    """
    Mengambil seluruh pesan dalam satu sesi/roomchat milik user tertentu berdasarkan session_id.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, session_id, timestamp, mode, user_message, final_response, steps FROM chat_history WHERE session_id = ? AND username = ? ORDER BY id ASC",
            (session_id, username.lower().strip())
        )
        rows = cursor.fetchall()
        conn.close()
        
        messages = []
        for row in rows:
            messages.append({
                "id": row["id"],
                "session_id": row["session_id"],
                "timestamp": row["timestamp"],
                "mode": row["mode"],
                "user_message": row["user_message"],
                "final_response": row["final_response"],
                "steps": json.loads(row["steps"])
            })
        return messages
    except Exception as e:
        print(f"[DB Error] Gagal mengambil pesan sesi: {e}")
        return []


def clear_history(username: str):
    """
    Menghapus seluruh isi riwayat percakapan milik user tertentu.
    """
    try:
        init_db()
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("DELETE FROM chat_history WHERE username = ?", (username.lower().strip(),))
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"[DB Error] Gagal menghapus riwayat chat: {e}")
