import sqlite3
import os
import secrets

from datetime import datetime, timedelta, timezone
from twilio.rest import Client
from utils.otp import generate_otp, generate_verification_id, validate_otp_format

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

OTP_EXPIRY_MINUTES = 5
MAX_ATTEMPTS = 3

def get_db_connection():
    """
    Establish and return a SQLite database connection with row factory enabled.
    """
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def send_otp_to_customer(phone_raw):
    """
    Business logic for MODULE 2 — SEND OTP.
    
    1. Validates phone input.
    2. Verifies customer exists in SQLite DB.
    3. Generates 4-digit OTP & unique verification_id.
    4. Creates an OTP session in otp_sessions (5-minute expiry).
    5. Delivers OTP via Twilio SMS.
    6. If Twilio delivery fails, removes the created OTP session and returns HTTP 500.
    """
    if phone_raw is None:
        return {
            "otp_sent": False,
            "reason": "PHONE_REQUIRED"
        }, 400

    if not isinstance(phone_raw, (str, int)):
        return {
            "otp_sent": False,
            "reason": "INVALID_PHONE"
        }, 400

    clean_phone = str(phone_raw).strip()

    if not clean_phone:
        return {
            "otp_sent": False,
            "reason": "PHONE_REQUIRED"
        }, 400

    if len(clean_phone) != 10 or not clean_phone.isdigit():
        return {
            "otp_sent": False,
            "reason": "INVALID_PHONE"
        }, 400

    # 1. Customer Lookup in database
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT customer_id, name 
        FROM customers 
        WHERE phone = ?
    ''', (clean_phone,))
    
    customer = cursor.fetchone()

    if not customer:
        conn.close()
        return {
            "otp_sent": False,
            "reason": "CUSTOMER_NOT_FOUND"
        }, 404

    customer_id = customer['customer_id']

    # 2. OTP Generation & Verification ID creation
    otp = generate_otp()
    
    cursor.execute('SELECT COUNT(*) as count FROM otp_sessions')
    row = cursor.fetchone()
    count = (row['count'] if row else 0) + 1
    verification_id = generate_verification_id(count)

    now_utc = datetime.now(timezone.utc)
    expires_at = (now_utc + timedelta(minutes=OTP_EXPIRY_MINUTES)).isoformat()

    # 3. Insert OTP session into SQLite
    cursor.execute('''
        INSERT INTO otp_sessions (verification_id, customer_id, phone, otp, attempts, expires_at, verified)
        VALUES (?, ?, ?, ?, 0, ?, 0)
    ''', (verification_id, customer_id, clean_phone, otp, expires_at))
    
    session_row_id = cursor.lastrowid
    conn.commit()

    # 4. Twilio SMS Dispatch
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

    # Format recipient (outgoing SMS destination) with +91 country code for Indian mobile numbers
    if clean_phone.startswith('+'):
        formatted_recipient = clean_phone
    elif clean_phone.startswith('91') and len(clean_phone) == 12:
        formatted_recipient = f"+{clean_phone}"
    else:
        formatted_recipient = f"+91{clean_phone}"

    message_body = f"Kapture Finance verification code: {otp}. This code expires in 5 minutes. Do not share this code with anyone."

    sms_success = False
    
    if account_sid and auth_token and twilio_phone and account_sid != 'your_twilio_account_sid':
        try:
            client = Client(account_sid, auth_token)
            client.messages.create(
                body=message_body,
                from_=twilio_phone,        # Twilio sender number from .env (unmodified)
                to=formatted_recipient     # Outgoing customer destination (+91XXXXXXXXXX)
            )
            sms_success = True
        except Exception as err:
            # Safe server-side log without credentials or sensitive data
            print(f"[OTP Service] Twilio SMS dispatch error: {err}")
            sms_success = False
    else:
        print("[OTP Service] Twilio credentials missing or unconfigured in .env file.")
        sms_success = False

    # 5. Handle SMS Failure -> Cleanup session and return HTTP 500
    if not sms_success:
        cursor.execute('DELETE FROM otp_sessions WHERE id = ?', (session_row_id,))
        conn.commit()
        conn.close()

        return {
            "otp_sent": False,
            "reason": "OTP_DELIVERY_FAILED"
        }, 500

    conn.close()

    return {
        "otp_sent": True,
        "verification_id": verification_id
    }, 200

def verify_otp_session(verification_id_raw: str, otp_raw: str):
    """
    Business logic for MODULE 3 — VERIFY OTP.
    
    1. Look up session using verification_id in otp_sessions table.
    2. Check if already verified (verified = 1).
    3. Check attempt limit (attempts >= 3).
    4. Check expiration timestamp.
    5. Secure constant-time OTP comparison (secrets.compare_digest).
    6. Returns customer_id and account_id upon success.
    """
    clean_ver_id = str(verification_id_raw).strip() if verification_id_raw is not None else ""
    clean_otp = str(otp_raw).strip() if otp_raw is not None else ""

    conn = get_db_connection()
    cursor = conn.cursor()

    # Parameterized search for verification session & joined customer account_id
    cursor.execute('''
        SELECT s.id, s.verification_id, s.customer_id, s.phone, s.otp, s.attempts, s.expires_at, s.verified, c.account_id
        FROM otp_sessions s
        LEFT JOIN customers c ON s.customer_id = c.customer_id
        WHERE s.verification_id = ?
    ''', (clean_ver_id,))
    
    session = cursor.fetchone()

    if not session:
        conn.close()
        return {
            "verified": False,
            "reason": "VERIFICATION_SESSION_NOT_FOUND"
        }, 404

    session_id = session['id']
    customer_id = session['customer_id']
    account_id = session['account_id']
    stored_otp = session['otp']
    attempts = session['attempts']
    expires_at_str = session['expires_at']
    already_verified = session['verified']

    # 1. Check if session is already verified
    if already_verified == 1:
        conn.close()
        return {
            "verified": True,
            "customer_id": customer_id,
            "account_id": account_id
        }, 200

    # 2. Check maximum attempt limit prior to matching
    if attempts >= MAX_ATTEMPTS:
        conn.close()
        return {
            "verified": False,
            "reason": "MAX_ATTEMPTS_EXCEEDED",
            "attempts_remaining": 0
        }, 400

    # 3. Check session expiration
    expires_at = datetime.fromisoformat(expires_at_str)
    now_utc = datetime.now(timezone.utc)

    if now_utc > expires_at:
        conn.close()
        return {
            "verified": False,
            "reason": "OTP_EXPIRED"
        }, 400

    # 4. Constant-time secure OTP comparison
    if not secrets.compare_digest(clean_otp, stored_otp):
        new_attempts = attempts + 1
        cursor.execute('''
            UPDATE otp_sessions
            SET attempts = ?
            WHERE id = ?
        ''', (new_attempts, session_id))
        conn.commit()
        conn.close()
        
        attempts_remaining = max(0, MAX_ATTEMPTS - new_attempts)
        
        if new_attempts >= MAX_ATTEMPTS:
            return {
                "verified": False,
                "reason": "MAX_ATTEMPTS_EXCEEDED",
                "attempts_remaining": 0
            }, 400

        return {
            "verified": False,
            "reason": "INVALID_OTP",
            "attempts_remaining": attempts_remaining
        }, 400

    # 5. OTP matches! Mark session as verified = 1
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
