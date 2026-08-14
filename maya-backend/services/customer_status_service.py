import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def get_customer_status(account_id_raw: str):
    """
    Read-only status service for admin/demo/testing.
    Returns aggregated customer, account, and latest interaction records.
    """
    clean_account_id = str(account_id_raw).strip() if account_id_raw else ""

    if not clean_account_id:
        return {
            "success": False,
            "error": "ACCOUNT_NOT_FOUND"
        }, 404

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Fetch Customer and Account details
    cursor.execute('''
        SELECT l.account_id, l.customer_id, l.loan_type, l.overdue_amount, l.days_past_due, l.payment_status,
               c.name as customer_name, c.phone as customer_phone
        FROM loan_accounts l
        JOIN customers c ON l.customer_id = c.customer_id
        WHERE l.account_id = ?
    ''', (clean_account_id,))
    
    account_row = cursor.fetchone()

    if not account_row:
        conn.close()
        return {
            "success": False,
            "error": "ACCOUNT_NOT_FOUND"
        }, 404

    # 2. Fetch Latest PTP
    cursor.execute('''
        SELECT id, account_id, amount, ptp_date, created_at
        FROM payment_promises
        WHERE account_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (clean_account_id,))
    ptp_row = cursor.fetchone()
    latest_ptp = dict(ptp_row) if ptp_row else None

    # 3. Fetch Latest Payment
    cursor.execute('''
        SELECT id, account_id, amount, status, payment_method, paid_at
        FROM payments
        WHERE account_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (clean_account_id,))
    payment_row = cursor.fetchone()
    latest_payment = dict(payment_row) if payment_row else None

    # 4. Fetch Latest Disposition
    cursor.execute('''
        SELECT id, account_id, intent, outcome, call_id, created_at
        FROM call_dispositions
        WHERE account_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (clean_account_id,))
    disp_row = cursor.fetchone()
    latest_disposition = dict(disp_row) if disp_row else None

    # 5. Fetch Latest Escalation
    cursor.execute('''
        SELECT id, account_id, reason, ticket_id, call_id, created_at
        FROM escalations
        WHERE account_id = ?
        ORDER BY id DESC LIMIT 1
    ''', (clean_account_id,))
    esc_row = cursor.fetchone()
    latest_escalation = dict(esc_row) if esc_row else None

    conn.close()

    return {
        "success": True,
        "customer": {
            "customer_id": account_row['customer_id'],
            "name": account_row['customer_name'],
            "phone": account_row['customer_phone']
        },
        "account": {
            "account_id": account_row['account_id'],
            "loan_type": account_row['loan_type'],
            "overdue_amount": float(account_row['overdue_amount']),
            "days_past_due": int(account_row['days_past_due']),
            "payment_status": account_row['payment_status']
        },
        "latest_ptp": latest_ptp,
        "latest_payment": latest_payment,
        "latest_disposition": latest_disposition,
        "latest_escalation": latest_escalation
    }, 200
