import sqlite3
import os
from datetime import datetime, timedelta, timezone
from utils.otp import generate_otp, generate_verification_id, validate_otp_format
from utils.phone import normalize_phone_number, format_phone_for_calling

# Resolve absolute path to database file inside database/ directory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

MAX_ATTEMPTS = 3
OTP_EXPIRY_MINUTES = 5

def get_db_connection():
    """
    Establish and return a SQLite database connection with row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def find_customer_by_phone(phone: str):
    """
    Query the database for a customer matching the specified phone.
    Normalizes input phone number before querying.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    clean_phone = normalize_phone_number(phone)
    if not clean_phone:
        return None
    
    cursor.execute('''
        SELECT customer_id, name, phone, account_id 
        FROM customers 
        WHERE phone = ?
    ''', (clean_phone,))
    
    customer = cursor.fetchone()
    conn.close()
    return customer

def create_otp_session(customer_id: str, phone: str) -> tuple[str, str]:
    """
    Generate a 4-digit OTP and verification_id, compute expiry timestamp, 
    and store it in otp_sessions.
    Returns (verification_id, otp).
    """
    otp = generate_otp()
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Generate sequential verification_id like VER001
    cursor.execute('SELECT COUNT(*) as count FROM otp_sessions')
    row = cursor.fetchone()
    count = (row['count'] if row else 0) + 1
    verification_id = generate_verification_id(count)
    
    # Calculate expiry ISO timestamp in UTC
    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()
    
    cursor.execute('''
        INSERT INTO otp_sessions (verification_id, customer_id, phone, otp, attempts, expires_at, verified)
        VALUES (?, ?, ?, ?, 0, ?, 0)
    ''', (verification_id, customer_id, phone, otp, expires_at))
    
    conn.commit()
    conn.close()
    return verification_id, otp

def start_verification(phone: str):
    """
    Stage 1: Validate phone and initiate customer verification.
    """
    clean_phone = normalize_phone_number(phone)
    if not clean_phone:
        return {
            "verified": False,
            "reason": "INVALID_PHONE"
        }, 400

    customer = find_customer_by_phone(clean_phone)
    if not customer:
        return {
            "verified": False,
            "reason": "CUSTOMER_NOT_FOUND"
        }, 200

    customer_id = customer['customer_id']
    customer_name = customer['name']
    
    verification_id, generated_otp = create_otp_session(customer_id, clean_phone)
    calling_phone = format_phone_for_calling(clean_phone)
    
    # MOCKED OTP DELIVERY: Print OTP only to server console
    print("\n" + "="*60)
    print(f"[MOCK OTP DELIVERY CONSOLE LOG]")
    print(f"Verification ID : {verification_id}")
    print(f"Customer Name   : {customer_name}")
    print(f"Customer ID     : {customer_id}")
    print(f"Phone Number    : {clean_phone}")
    print(f"Calling Phone   : {calling_phone}")
    print(f"Generated OTP   : {generated_otp}")
    print(f"Expires In      : {OTP_EXPIRY_MINUTES} minutes")
    print("="*60 + "\n")
    
    return {
        "customer_found": True,
        "verification_id": verification_id,
        "otp_required": True
    }, 200

def verify_otp_session(verification_id: str, otp: str):
    """
    Stage 2: Validate submitted OTP against active session for verification_id.
    """
    clean_ver_id = str(verification_id).strip() if verification_id else ""
    otp_str = str(otp).strip() if otp else ""

    if not clean_ver_id or not otp_str:
        return {
            "verified": False,
            "reason": "MISSING_VERIFICATION_ID_OR_OTP"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT s.id, s.verification_id, s.customer_id, s.otp, s.attempts, s.expires_at, s.verified, c.account_id
        FROM otp_sessions s
        JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.verification_id = ?
    ''', (clean_ver_id,))
    
    session = cursor.fetchone()

    if not session:
        conn.close()
        return {
            "verified": False,
            "reason": "INVALID_OTP",
            "attempts_remaining": 0
        }, 200

    session_id = session['id']
    customer_id = session['customer_id']
    account_id = session['account_id']
    correct_otp = session['otp']
    attempts = session['attempts']
    expires_at_str = session['expires_at']
    already_verified = session['verified']

    # Check maximum attempt limit prior to matching
    if attempts >= MAX_ATTEMPTS:
        conn.close()
        return {
            "verified": False,
            "reason": "INVALID_OTP",
            "attempts_remaining": 0
        }, 200

    # Check expiration
    expires_at = datetime.fromisoformat(expires_at_str)
    now_utc = datetime.now(timezone.utc)

    if now_utc > expires_at:
        conn.close()
        return {
            "verified": False,
            "reason": "OTP_EXPIRED"
        }, 200

    # Verify OTP string match
    if otp_str != correct_otp:
        new_attempts = attempts + 1
        cursor.execute('''
            UPDATE otp_sessions
            SET attempts = ?
            WHERE id = ?
        ''', (new_attempts, session_id))
        conn.commit()
        conn.close()
        
        attempts_remaining = max(0, MAX_ATTEMPTS - new_attempts)
        return {
            "verified": False,
            "reason": "INVALID_OTP",
            "attempts_remaining": attempts_remaining
        }, 200

    # Successful OTP match: Mark session as verified
    cursor.execute('''
        UPDATE otp_sessions
        SET verified = 1
        WHERE id = ?
    ''', (session_id,))
    conn.commit()
    conn.close()

    return {
        "verified": True,
        "customer_id": customer_id,
        "account_id": account_id
    }, 200
