import logging
import os

# Configure basic logging format
logging.basicConfig(
    level=logging.INFO,
    format='[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)

logger = logging.getLogger("maya-backend")

def log_api_call(api_name: str, status_code: int, call_id: str = None, details: dict = None):
    """
    Log API tool call information safely without logging OTPs or secrets.
    """
    msg_parts = [f"API: {api_name}", f"Status: {status_code}"]
    if call_id:
        msg_parts.append(f"CallID: {call_id}")
    if details:
        # Sanitize details dict to ensure no 'otp' or 'secret' is logged
        safe_details = {k: v for k, v in details.items() if k.lower() not in ('otp', 'auth_token', 'password', 'secret')}
        msg_parts.append(f"Details: {safe_details}")
    
    logger.info(" | ".join(msg_parts))

def log_error(api_name: str, error_msg: str, call_id: str = None):
    """
    Log backend error safely.
    """
    msg = f"API Error [{api_name}]"
    if call_id:
        msg += f" (CallID: {call_id})"
    msg += f": {error_msg}"
    logger.error(msg)
