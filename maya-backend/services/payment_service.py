import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_payment_link(account_id: str, phone: str):
    """
    Business logic to generate a mock payment link.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_phone = str(phone).strip() if phone else ""

    if not clean_account_id or not clean_phone:
        return {
            "success": False,
            "reason": "MISSING_ACCOUNT_ID_OR_PHONE"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT c.account_id 
        FROM customers c
        LEFT JOIN loans l ON c.account_id = l.account_id
        WHERE (c.account_id = ? OR l.account_id = ?) AND c.phone = ?
    ''', (clean_account_id, clean_account_id, clean_phone))
    
    match = cursor.fetchone()
    conn.close()

    if not match:
        return {
            "success": False,
            "reason": "ACCOUNT_OR_PHONE_NOT_FOUND"
        }, 404

    payment_link = f"https://payment.example/pay/{clean_account_id}"

    return {
        "success": True,
        "link": payment_link
    }, 200
