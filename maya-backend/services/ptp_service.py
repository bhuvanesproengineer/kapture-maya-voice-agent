import sqlite3
import os
from datetime import datetime, timezone

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def log_promise_to_pay(account_id: str, amount: float, ptp_date: str):
    """
    Business logic to log a Promise to Pay (PTP).
    """
    if not account_id or amount is None or not ptp_date:
        return {
            "success": False,
            "reason": "MISSING_REQUIRED_FIELDS"
        }, 400

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            return {
                "success": False,
                "reason": "INVALID_AMOUNT"
            }, 400
    except (ValueError, TypeError):
        return {
            "success": False,
            "reason": "INVALID_AMOUNT"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Confirm account exists in loans or customers table
    cursor.execute('SELECT account_id FROM loans WHERE account_id = ?', (account_id,))
    loan = cursor.fetchone()
    if not loan:
        cursor.execute('SELECT account_id FROM customers WHERE account_id = ?', (account_id,))
        cust = cursor.fetchone()
        if not cust:
            conn.close()
            return {
                "success": False,
                "reason": "ACCOUNT_NOT_FOUND"
            }, 404

    now_iso = datetime.now(timezone.utc).isoformat()
    
    cursor.execute('''
        INSERT INTO payment_promises (account_id, amount, ptp_date, created_at)
        VALUES (?, ?, ?, ?)
    ''', (account_id, amount_val, str(ptp_date), now_iso))
    
    promise_id = cursor.lastrowid
    conn.commit()
    conn.close()

    reference = f"PTP{promise_id:03d}"
    
    return {
        "success": True,
        "reference": reference
    }, 200
