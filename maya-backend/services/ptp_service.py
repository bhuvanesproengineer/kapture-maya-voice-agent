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


def log_promise_to_pay(account_id: str, amount: float, ptp_date: str, call_id: str = None):
    """
    Business logic to log a Promise to Pay (PTP).
    Stores account_id, amount, ptp_date, created_at in payment_promises table.
    """
    if not account_id or amount is None or not ptp_date:
        log_error("log-promise-to-pay", "Missing required fields", call_id)
        return {
            "success": False,
            "reason": "MISSING_REQUIRED_FIELDS"
        }, 400

    try:
        amount_val = float(amount)
        if amount_val <= 0:
            log_error("log-promise-to-pay", "Invalid amount <= 0", call_id)
            return {
                "success": False,
                "reason": "INVALID_AMOUNT"
            }, 400
    except (ValueError, TypeError):
        log_error("log-promise-to-pay", "Invalid amount format", call_id)
        return {
            "success": False,
            "reason": "INVALID_AMOUNT"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # Confirm account exists in loan_accounts, loans, or customers table
    cursor.execute('SELECT account_id FROM loan_accounts WHERE account_id = ?', (account_id,))
    loan = cursor.fetchone()
    if not loan:
        cursor.execute('SELECT account_id FROM customers WHERE account_id = ?', (account_id,))
        cust = cursor.fetchone()
        if not cust:
            conn.close()
            log_error("log-promise-to-pay", f"Account not found: {account_id}", call_id)
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
    
    log_api_call("log-promise-to-pay", 200, call_id, {
        "account_id": account_id,
        "amount": amount_val,
        "ptp_date": str(ptp_date),
        "reference": reference
    })

    return {
        "success": True,
        "reference": reference
    }, 200
