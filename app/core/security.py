import bcrypt


def hash_password(password: str) -> str:
    """Hash a password with bcrypt. Store only the resulting hash."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt(rounds=12)
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")
