import re

def validate_phone_no(phone_no:str) -> bool:
    pattern = r"^\+91\d{10}$"
    return bool(re.match(pattern, phone_no))
