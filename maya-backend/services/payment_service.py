import sqlite3
import os
from datetime import datetime, timezone
from twilio.rest import Client
from utils.logger import log_api_call, log_error
from utils.phone import normalize_phone_number, format_phone_for_calling

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'database', 'database.db')

def get_db_connection():
    conn = sqlite3.connect(DB_PATH, timeout=30.0)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA busy_timeout=30000")
    return conn

def send_payment_link(account_id: str = None, phone: str = None, call_id: str = None, host_url: str = None):
    """
    Business logic to generate payment URL and dispatch it via Twilio SMS.
    Flexible lookup: resolves account_id and phone if either or both are provided.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    clean_phone = normalize_phone_number(phone) if phone else None

    if not clean_account_id and not clean_phone:
        log_error("send-payment-link", "Missing account_id and phone", call_id)
        return {
            "success": False,
            "reason": "MISSING_ACCOUNT_ID_OR_PHONE"
        }, 400

    conn = get_db_connection()
    cursor = conn.cursor()

    match = None
    if clean_account_id and clean_phone:
        cursor.execute('''
            SELECT c.account_id, c.phone, c.customer_id
            FROM customers c
            LEFT JOIN loan_accounts l ON c.account_id = l.account_id
            WHERE (c.account_id = ? OR c.customer_id = ? OR l.account_id = ?) AND c.phone = ?
        ''', (clean_account_id, clean_account_id, clean_account_id, clean_phone))
        match = cursor.fetchone()

    if not match and clean_account_id:
        cursor.execute('''
            SELECT c.account_id, c.phone, c.customer_id
            FROM customers c
            LEFT JOIN loan_accounts l ON c.account_id = l.account_id
            WHERE c.account_id = ? OR c.customer_id = ? OR l.account_id = ?
        ''', (clean_account_id, clean_account_id, clean_account_id))
        match = cursor.fetchone()

    if not match and clean_phone:
        cursor.execute('''
            SELECT c.account_id, c.phone, c.customer_id
            FROM customers c
            WHERE c.phone = ?
        ''', (clean_phone,))
        match = cursor.fetchone()

    conn.close()

    if not match:
        log_error("send-payment-link", f"Account or phone not found (account: {clean_account_id}, phone: {clean_phone})", call_id)
        return {
            "success": False,
            "reason": "ACCOUNT_OR_PHONE_NOT_FOUND"
        }, 404

    target_account_id = match['account_id']
    target_phone = match['phone']
    clean_phone = normalize_phone_number(target_phone)

    # Base URL resolution: env variable > host_url > fallback Render domain
    env_base_url = os.getenv('PAYMENT_BASE_URL') or os.getenv('BASE_URL')
    if env_base_url:
        base_url = env_base_url.rstrip('/')
    elif host_url:
        base_url = host_url.rstrip('/')
    else:
        base_url = "https://kapture-maya-voice-agent.onrender.com"

    payment_link = f"{base_url}/payment/{target_account_id}"

    # Format recipient with +12 digit calling format (+91XXXXXXXXXX)
    formatted_recipient = format_phone_for_calling(clean_phone)

    # Dispatch SMS via Twilio
    account_sid = os.getenv('TWILIO_ACCOUNT_SID')
    auth_token = os.getenv('TWILIO_AUTH_TOKEN')
    twilio_phone = os.getenv('TWILIO_PHONE_NUMBER')

    message_body = f"Kapture Finance: Dear customer, please use this link to complete your payment for account {target_account_id}: {payment_link}"

    sms_sent = False
    sms_error = None
    if account_sid and auth_token and twilio_phone and account_sid != 'your_twilio_account_sid':
        try:
            client = Client(account_sid, auth_token)
            msg_res = client.messages.create(
                body=message_body,
                from_=twilio_phone,
                to=formatted_recipient
            )
            sms_sent = True
            log_api_call("send-payment-link-sms", 200, call_id, {"to": formatted_recipient, "link": payment_link, "sid": getattr(msg_res, 'sid', None)})
        except Exception as err:
            sms_error = str(err)
            log_error("send-payment-link-sms", f"Twilio SMS dispatch error: {err}", call_id)
            sms_sent = False
    else:
        sms_error = "Twilio credentials missing or unconfigured in .env"
        log_error("send-payment-link-sms", sms_error, call_id)

    log_api_call("send-payment-link", 200, call_id, {"account_id": target_account_id, "link": payment_link, "sms_sent": sms_sent})

    res_body = {
        "success": True,
        "account_id": target_account_id,
        "link": payment_link,
        "sms_sent": sms_sent
    }
    if sms_error:
        res_body["sms_error"] = sms_error

    return res_body, 200

def get_payment_page_data(account_id: str):
    """
    Fetch loan account & customer data for rendering the payment page.
    Matches account_id, customer_id, or phone number.
    """
    clean_identifier = str(account_id).strip() if account_id else ""
    norm_phone = normalize_phone_number(clean_identifier)

    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT l.account_id, l.customer_id, l.loan_type, l.overdue_amount, l.days_past_due, l.payment_status, c.name as customer_name
        FROM loan_accounts l
        JOIN customers c ON l.customer_id = c.customer_id
        WHERE l.account_id = ? OR l.customer_id = ? OR c.phone = ? OR (c.phone = ? AND ? IS NOT NULL)
    ''', (clean_identifier, clean_identifier, clean_identifier, norm_phone, norm_phone))
    
    data = cursor.fetchone()
    conn.close()
    return data

def process_demo_payment(account_id: str):
    """
    Process mock payment: update SQLite DB payment_status to 'PAID' and record in payments table.
    Updates both loan_accounts and loans tables.
    """
    clean_account_id = str(account_id).strip() if account_id else ""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute('''
        SELECT account_id, overdue_amount, payment_status
        FROM loan_accounts
        WHERE account_id = ? OR customer_id = ?
    ''', (clean_account_id, clean_account_id))
    
    account = cursor.fetchone()
    if not account:
        conn.close()
        return False, "Account not found"

    real_account_id = account['account_id']
    amount = account['overdue_amount'] if account['overdue_amount'] > 0 else 8499.0
    now_iso = datetime.now(timezone.utc).isoformat()

    # Record payment transaction
    cursor.execute('''
        INSERT INTO payments (account_id, amount, status, payment_method, paid_at)
        VALUES (?, ?, 'SUCCESSFUL', 'DEMO_PAYMENT', ?)
    ''', (real_account_id, amount, now_iso))

    # Update loan_accounts table status
    cursor.execute('''
        UPDATE loan_accounts
        SET overdue_amount = 0.0, payment_status = 'PAID'
        WHERE account_id = ?
    ''', (real_account_id,))

    # Update loans table status
    cursor.execute('''
        UPDATE loans
        SET overdue_amount = 0.0
        WHERE account_id = ?
    ''', (real_account_id,))

    conn.commit()
    conn.close()

    log_api_call("process-demo-payment", 200, None, {"account_id": real_account_id, "amount": amount, "status": "SUCCESSFUL"})
    return True, "Payment Successful"
