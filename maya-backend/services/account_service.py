import sqlite3
import os
from utils.logger import log_api_call, log_error

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    """
    Establish and return a SQLite database connection with row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn


def get_account_details_by_verification(verification_id_raw, call_id: str = None):
    """
    Business logic for CUSTOMER ACCOUNT DETAILS module.
    
    1. Validates presence of verification_id.
    2. Searches otp_sessions for verification_id.
    3. Enforces security check: verified MUST equal 1.
    4. Retrieves customer name from customers table and loan details from loan_accounts table.
    5. Returns customer name, loan account details, and payment_status upon successful verification.
    """
    if verification_id_raw is None:
        log_error("get-account-details", "Missing verification_id", call_id)
        return {
            "success": False,
            "reason": "VERIFICATION_ID_REQUIRED"
        }, 400

    clean_ver_id = str(verification_id_raw).strip()

    if not clean_ver_id:
        log_error("get-account-details", "Empty verification_id string", call_id)
        return {
            "success": False,
            "reason": "VERIFICATION_ID_REQUIRED"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    # 1. Verification session security lookup
    cursor.execute('''
        SELECT verification_id, customer_id, verified
        FROM otp_sessions
        WHERE verification_id = ?
    ''', (clean_ver_id,))
    
    session = cursor.fetchone()

    if not session:
        conn.close()
        log_api_call("get-account-details", 404, call_id, {"verification_id": clean_ver_id, "success": False, "reason": "VERIFICATION_SESSION_NOT_FOUND"})
        return {
            "success": False,
            "reason": "VERIFICATION_SESSION_NOT_FOUND"
        }, 404

    # 2. Strict Security Check: Must be verified (verified = 1)
    if session['verified'] != 1:
        conn.close()
        log_api_call("get-account-details", 403, call_id, {"verification_id": clean_ver_id, "success": False, "reason": "CUSTOMER_NOT_VERIFIED"})
        return {
            "success": False,
            "reason": "CUSTOMER_NOT_VERIFIED"
        }, 403

    customer_id = session['customer_id']

    # 3. Retrieve Customer Name from customers table
    cursor.execute('''
        SELECT name
        FROM customers
        WHERE customer_id = ?
    ''', (customer_id,))
    
    cust_row = cursor.fetchone()
    customer_name = cust_row['name'] if cust_row else ""

    # 4. Retrieve Loan Account Details & Payment Status from loan_accounts table using verified customer_id
    cursor.execute('''
        SELECT account_id, loan_type, overdue_amount, days_past_due, payment_status
        FROM loan_accounts
        WHERE customer_id = ?
    ''', (customer_id,))
    
    account_row = cursor.fetchone()
    conn.close()

    if not account_row:
        log_api_call("get-account-details", 404, call_id, {"customer_id": customer_id, "success": False, "reason": "ACCOUNT_NOT_FOUND"})
        return {
            "success": False,
            "reason": "ACCOUNT_NOT_FOUND"
        }, 404

    payment_status = account_row['payment_status'] if 'payment_status' in account_row.keys() else 'PENDING'

    log_api_call("get-account-details", 200, call_id, {
        "customer_id": customer_id,
        "account_id": account_row['account_id'],
        "payment_status": payment_status,
        "success": True
    })

    return {
        "success": True,
        "customer": {
            "name": customer_name
        },
        "account": {
            "account_id": account_row['account_id'],
            "loan_type": account_row['loan_type'],
            "overdue_amount": account_row['overdue_amount'],
            "days_past_due": account_row['days_past_due'],
            "payment_status": payment_status
        }
    }, 200
