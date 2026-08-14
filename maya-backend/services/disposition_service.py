import sqlite3
import os
from datetime import datetime, timezone
from utils.logger import log_api_call, log_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def mark_disposition(account_id: str, intent: str, outcome: str, call_id: str = None):
    """
    Business logic to record call disposition in call_dispositions table.
    Stores account_id, intent, outcome, call_id, created_at.
    Handles intents/outcomes such as WILL_PAY, ALREADY_PAID, DISPUTE, HARDSHIP, DO_NOT_CALL, CALLBACK, ESCALATION.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_intent = str(intent).strip() if intent else ""
    clean_outcome = str(outcome).strip() if outcome else ""

    if not clean_account_id or not clean_intent or not clean_outcome:
        log_error("mark-disposition", "Missing required fields (account_id, intent, outcome)", call_id)
        return {
            "success": False,
            "reason": "MISSING_REQUIRED_FIELDS"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute('''
        INSERT INTO call_dispositions (account_id, intent, outcome, call_id, created_at)
        VALUES (?, ?, ?, ?, ?)
    ''', (clean_account_id, clean_intent, clean_outcome, call_id, now_iso))
    
    disp_id = cursor.lastrowid
    conn.commit()
    conn.close()

    disposition_id = f"DISP{disp_id:03d}"

    log_api_call("mark-disposition", 200, call_id, {
        "account_id": clean_account_id,
        "intent": clean_intent,
        "outcome": clean_outcome,
        "disposition_id": disposition_id
    })

    return {
        "success": True,
        "disposition_id": disposition_id
    }, 200
