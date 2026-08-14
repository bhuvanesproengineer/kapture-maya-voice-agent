import secrets
import string
import uuid

def generate_otp() -> str:
    """
    Generate a secure 4-digit numeric OTP code.
    Uses secrets module for cryptographically safe randomness.
    """
    digits = string.digits
    return ''.join(secrets.choice(digits) for _ in range(4))

def generate_verification_id(counter: int = None) -> str:
    """
    Generate a verification ID.
    If counter is provided, formats as VER001, VER002, etc.
    Otherwise uses a short random hex suffix.
    """
    if counter is not None:
        return f"VER{counter:03d}"
    return f"VER{uuid.uuid4().hex[:6].upper()}"

def validate_otp_format(otp: str) -> bool:
    """
    Validate that the input is a valid 4-digit numeric string.
    """
    if not isinstance(otp, str):
        return False
    return len(otp) == 4 and otp.isdigit()
