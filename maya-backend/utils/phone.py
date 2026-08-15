import re

def normalize_phone_number(phone_raw) -> str | None:
    """
    Clean and normalize phone number input.
    Removes country code (e.g., +91 or 91), trunk prefix (0), whitespace, dashes, and non-digit characters,
    returning a clean 10-digit phone number string for database lookup and storage.

    Examples:
        - "+918500197653" -> "8500197653"
        - "918500197653"  -> "8500197653"
        - "+91 85001-97653" -> "8500197653"
        - "08500197653"   -> "8500197653"
        - "8500197653"    -> "8500197653"
        - 8500197653      -> "8500197653"

    Returns:
        10-digit string if valid, or None if invalid.
    """
    if phone_raw is None:
        return None
    if not isinstance(phone_raw, (str, int)):
        return None

    phone_str = str(phone_raw).strip()
    if not phone_str:
        return None

    # Extract digits only
    digits = re.sub(r'\D', '', phone_str)

    # If 12 digits starting with country code '91', strip '91'
    if len(digits) == 12 and digits.startswith('91'):
        digits = digits[2:]
    # If 11 digits starting with trunk prefix '0', strip '0'
    elif len(digits) == 11 and digits.startswith('0'):
        digits = digits[1:]

    if len(digits) == 10 and digits.isdigit():
        return digits

    return None

def format_phone_for_calling(phone_raw, country_code: str = "91") -> str | None:
    """
    Format phone number into +12 digit calling/SMS format (+<country_code><10_digits>).

    Examples:
        - "8500197653"     -> "+918500197653"
        - "+918500197653"  -> "+918500197653"
        - "918500197653"   -> "+918500197653"

    Returns:
        Formatted string "+91XXXXXXXXXX" if valid, or None if invalid.
    """
    clean_phone = normalize_phone_number(phone_raw)
    if clean_phone:
        return f"+{country_code}{clean_phone}"
    return None
