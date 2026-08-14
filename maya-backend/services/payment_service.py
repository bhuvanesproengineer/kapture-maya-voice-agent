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


def send_payment_link(account_id: str, phone: str, call_id: str = None):
    """
    Business logic to generate a working demo payment URL.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_phone = str(phone).strip() if phone else ""

    if not clean_account_id or not clean_phone:
        log_error("send-payment-link", "Missing account_id or phone", call_id)
        return {
            "success": False,
            "reason": "MISSING_ACCOUNT_ID_OR_PHONE"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.account_id 
        FROM customers c
        LEFT JOIN loan_accounts l ON c.account_id = l.account_id
        WHERE (c.account_id = ? OR l.account_id = ?) AND c.phone = ?
    ''', (clean_account_id, clean_account_id, clean_phone))
    
    match = cursor.fetchone()
    conn.close()

    if not match:
        log_error("send-payment-link", f"Account or phone not found for account {clean_account_id}", call_id)
        return {
            "success": False,
            "reason": "ACCOUNT_OR_PHONE_NOT_FOUND"
        }, 404

    # Demo Payment URL matching required Render domain
    payment_link = f"https://kapture-maya-voice-agent.onrender.com/payment/{clean_account_id}"

    log_api_call("send-payment-link", 200, call_id, {"account_id": clean_account_id, "link": payment_link})

    return {
        "success": True,
        "link": payment_link
    }, 200

def get_payment_page_data(account_id: str):
    """
    Fetch loan account & customer data for rendering the payment page.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT l.account_id, l.customer_id, l.loan_type, l.overdue_amount, l.days_past_due, l.payment_status, c.name as customer_name
        FROM loan_accounts l
        JOIN customers c ON l.customer_id = c.customer_id
        WHERE l.account_id = ?
    ''', (clean_account_id,))
    
    data = cursor.fetchone()
    conn.close()
    return data

def process_demo_payment(account_id: str):
    """
    Process mock payment: update SQLite DB payment_status to 'PAID' and record in payments table.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT account_id, overdue_amount, payment_status
        FROM loan_accounts
        WHERE account_id = ?
    ''', (clean_account_id,))
    
    account = cursor.fetchone()
    if not account:
        conn.close()
        return False, "Account not found"

    amount = account['overdue_amount'] if account['overdue_amount'] > 0 else 8499.0
    now_iso = datetime.now(timezone.utc).isoformat()

    # Record payment transaction
    cursor.execute('''
        INSERT INTO payments (account_id, amount, status, payment_method, paid_at)
        VALUES (?, ?, 'SUCCESSFUL', 'DEMO_PAYMENT', ?)
    ''', (clean_account_id, amount, now_iso))

    # Update loan account status
    cursor.execute('''
        UPDATE loan_accounts
        SET overdue_amount = 0.0, payment_status = 'PAID'
        WHERE account_id = ?
    ''', (clean_account_id,))

    conn.commit()
    conn.close()

    log_api_call("process-demo-payment", 200, None, {"account_id": clean_account_id, "amount": amount, "status": "SUCCESSFUL"})
    return True, "Payment Successful"
