import sqlite3
from datetime import datetime

DB_PATH = "mannsaathi.db"

def get_conn():
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS journal_entries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, time TEXT, text TEXT, source TEXT,
            tier TEXT, valence REAL
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS checkins (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT, time TEXT,
            avg_valence REAL, avg_arousal REAL
        )
    """)
    conn.commit()
    return conn

def save_journal_entry(user_id, text, source, tier, valence):
    conn = get_conn()
    conn.execute(
        "INSERT INTO journal_entries (user_id, time, text, source, tier, valence) VALUES (?, ?, ?, ?, ?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), text, source, tier, valence)
    )
    conn.commit()
    conn.close()

def get_journal_entries(user_id, limit=10):
    conn = get_conn()
    rows = conn.execute(
        "SELECT time, text, tier, valence FROM journal_entries WHERE user_id=? ORDER BY id DESC LIMIT ?",
        (user_id, limit)
    ).fetchall()
    conn.close()
    return [{"time": r[0], "text": r[1], "tier": r[2], "valence": r[3]} for r in rows]

def get_valence_history(user_id):
    conn = get_conn()
    rows = conn.execute(
        "SELECT valence FROM journal_entries WHERE user_id=? ORDER BY id ASC", (user_id,)
    ).fetchall()
    conn.close()
    return [r[0] for r in rows]

def save_checkin(user_id, avg_valence, avg_arousal):
    conn = get_conn()
    conn.execute(
        "INSERT INTO checkins (user_id, time, avg_valence, avg_arousal) VALUES (?, ?, ?, ?)",
        (user_id, datetime.now().strftime("%Y-%m-%d %H:%M"), avg_valence, avg_arousal)
    )
    conn.commit()
    conn.close()
    return get_checkin_streak(user_id)

def get_checkin_streak(user_id):
    conn = get_conn()
    count = conn.execute("SELECT COUNT(*) FROM checkins WHERE user_id=?", (user_id,)).fetchone()[0]
    conn.close()
    return count