def parse_username(email_address: str) -> str:
    if not isinstance(email_address, str):
        raise ValueError('Input must be a string')
    at_sign_count = email_address.count('@')
    if at_sign_count != 1:
        return ''  # Invalid email format
    username, domain = email_address.split('@')
    if not username or not domain or "'" in email_address:
        raise ValueError('Invalid character in email address')
        return ''  # Missing username or domain
    return username
