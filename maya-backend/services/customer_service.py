import sqlite3
import os
from utils.logger import log_api_call, log_error
from utils.phone import normalize_phone_number, format_phone_for_calling

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


def check_customer_by_phone(phone_raw, call_id: str = None):
    """
    Business logic for customer lookup by phone number.
    Normalizes phone input (stripping country code like +91/91) and checks database.
    """
    if phone_raw is None:
        log_error("check-customer", "Missing phone number", call_id)
        return {
            "customer_found": False,
            "reason": "PHONE_REQUIRED"
        }, 400

    clean_phone = normalize_phone_number(phone_raw)

    if not clean_phone:
        log_error("check-customer", f"Invalid phone length/format: {phone_raw}", call_id)
        return {
            "customer_found": False,
            "reason": "INVALID_PHONE"
        }, 400

    # Parameterized database search
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT customer_id, name 
        FROM customers 
        WHERE phone = ?
    ''', (clean_phone,))
    
    customer = cursor.fetchone()
    conn.close()

    if not customer:
        log_api_call("check-customer", 404, call_id, {"phone": clean_phone, "customer_found": False})
        return {
            "customer_found": False,
            "reason": "CUSTOMER_NOT_FOUND"
        }, 404

    calling_phone = format_phone_for_calling(clean_phone)
    log_api_call("check-customer", 200, call_id, {
        "customer_found": True,
        "customer_id": customer['customer_id'],
        "customer_name": customer['name'],
        "phone": clean_phone,
        "calling_phone": calling_phone
    })

    return {
        "customer_found": True,
        "customer_id": customer['customer_id'],
        "customer_name": customer['name'],
        "phone": clean_phone,
        "calling_phone": calling_phone
    }, 200
