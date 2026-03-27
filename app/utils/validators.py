import re

def validate_phone_number_format(phone: str) -> bool:
    """Checks if phone number matches E.164 format."""
    pattern = r'^\+[1-9]\d{1,14}$'
    return bool(re.match(pattern, phone))

def validate_months(months: int) -> bool:
    return 1 <= months <= 12
