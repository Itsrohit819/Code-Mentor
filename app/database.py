import sqlite3
from datetime import datetime

DB_FILE = "app/code_logs.db"

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT,
            error TEXT,
            concept TEXT,
            suggestion TEXT,
            timestamp TEXT
        )
    ''')
    conn.commit()
    conn.close()

def log_submission(code, error, concept, suggestion):
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    cursor.execute('''
        INSERT INTO submissions (code, error, concept, suggestion, timestamp)
        VALUES (?, ?, ?, ?, ?)
    ''', (code, error, concept, suggestion, timestamp))
    conn.commit()
    conn.close()
