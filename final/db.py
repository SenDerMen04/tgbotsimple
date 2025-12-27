import sqlite3
from contextlib import closing

DB_FILE = "bandfinder.db"

def _connect():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row  # Чтобы возвращать словари
    return conn

def init_db():
    with _connect() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS musicians (
                telegram_id INTEGER PRIMARY KEY,
                instrument TEXT,
                experience INTEGER,
                genres TEXT,
                location_text TEXT,
                about TEXT
            )
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS band_requests (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                band_id INTEGER,
                instrument TEXT,
                genre TEXT,
                description TEXT,
                location_text TEXT,
                min_experience INTEGER,
                accepted_by INTEGER
            )
        """)
        conn.commit()

# ===== MUSICIAN =====
def register_musician(tid, instrument, experience, genres, location_text, about):
    with _connect() as conn:
        conn.execute("""
            INSERT OR REPLACE INTO musicians
            (telegram_id, instrument, experience, genres, location_text, about)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (tid, instrument, experience, genres, location_text, about))
        conn.commit()

def get_musician_profile(tid):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM musicians WHERE telegram_id=?", (tid,)).fetchone()
        return dict(row) if row else None

def find_musicians_by_text_location(instrument, location_text, min_exp=0):
    with _connect() as conn:
        rows = conn.execute("""
            SELECT * FROM musicians
            WHERE instrument LIKE ? AND experience >= ?
        """, (f"%{instrument}%", min_exp)).fetchall()
        return [dict(r) for r in rows]

# ===== BAND REQUESTS =====
def create_band_request(band_id, instrument, genre, description, location_text, min_exp):
    with _connect() as conn:
        cur = conn.execute("""
            INSERT INTO band_requests
            (band_id, instrument, genre, description, location_text, min_experience)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (band_id, instrument, genre, description, location_text, min_exp))
        conn.commit()
        return cur.lastrowid

def get_band_requests(band_id):
    with _connect() as conn:
        rows = conn.execute("SELECT * FROM band_requests WHERE band_id=?", (band_id,)).fetchall()
        return [dict(r) for r in rows]

def get_band_request(req_id):
    with _connect() as conn:
        row = conn.execute("SELECT * FROM band_requests WHERE id=?", (req_id,)).fetchone()
        return dict(row) if row else None

def assign_musician(req_id, musician_id):
    with _connect() as conn:
        row = conn.execute("SELECT accepted_by FROM band_requests WHERE id=?", (req_id,)).fetchone()
        if not row or row["accepted_by"]:
            return False
        conn.execute("UPDATE band_requests SET accepted_by=? WHERE id=?", (musician_id, req_id))
        conn.commit()
        return True
