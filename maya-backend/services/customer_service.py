import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    """
    Establish and return a SQLite database connection with row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def check_customer_by_phone(phone_raw):
    """
    Business logic for customer lookup by phone number.
    Validates phone format (must be 10 digits) and checks database.
    """
    if phone_raw is None:
        return {
            "customer_found": False,
            "reason": "PHONE_REQUIRED"
        }, 400

    if not isinstance(phone_raw, (str, int)):
        return {
            "customer_found": False,
            "reason": "INVALID_PHONE"
        }, 400

    clean_phone = str(phone_raw).strip()

    if not clean_phone:
        return {
            "customer_found": False,
            "reason": "PHONE_REQUIRED"
        }, 400

    # Validate exact 10 digits requirement
    if len(clean_phone) != 10 or not clean_phone.isdigit():
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
        return {
            "customer_found": False,
            "reason": "CUSTOMER_NOT_FOUND"
        }, 404

    return {
        "customer_found": True,
        "customer_id": customer['customer_id'],
        "customer_name": customer['name']
    }, 200
