import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def escalate_to_agent(account_id: str, reason: str):
    """
    Business logic to record an escalation ticket.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_reason = str(reason).strip() if reason else ""

    if not clean_account_id or not clean_reason:
        return {
            "success": False,
            "reason": "MISSING_ACCOUNT_ID_OR_REASON"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Determine next ticket count
    cursor.execute('SELECT COUNT(*) as count FROM escalations')
    row = cursor.fetchone()
    count = (row['count'] if row else 0) + 1
    ticket_id = f"ESC{count:03d}"

    now_iso = datetime.now(timezone.utc).isoformat()

    cursor.execute('''
        INSERT INTO escalations (account_id, reason, ticket_id, created_at)
        VALUES (?, ?, ?, ?)
    ''', (clean_account_id, clean_reason, ticket_id, now_iso))

    conn.commit()
    conn.close()

    return {
        "success": True,
        "ticket_id": ticket_id
    }, 200
