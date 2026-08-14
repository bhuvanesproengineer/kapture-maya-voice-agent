import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def mark_disposition(account_id: str, intent: str, outcome: str):
    """
    Business logic to record call disposition.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_intent = str(intent).strip() if intent else ""
    clean_outcome = str(outcome).strip() if outcome else ""

    if not clean_account_id or not clean_intent or not clean_outcome:
        return {
            "success": False,
            "reason": "MISSING_REQUIRED_FIELDS"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute('''
        INSERT INTO call_dispositions (account_id, intent, outcome, created_at)
        VALUES (?, ?, ?, ?)
    ''', (clean_account_id, clean_intent, clean_outcome, now_iso))
    
    disp_id = cursor.lastrowid
    conn.commit()
    conn.close()

    disposition_id = f"DISP{disp_id:03d}"

    return {
        "success": True,
        "disposition_id": disposition_id
    }, 200
