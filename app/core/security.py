import bcrypt


def hash_password(password: str) -> str:
    """Hache un mot de passe avec bcrypt et retourne la version string."""
    password_bytes = password.encode("utf-8")
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password_bytes, salt).decode("utf-8")


def verify_password(password: str, hashed: str) -> bool:
    """Vérifie qu'un mot de passe en clair correspond à un hash bcrypt."""
    try:
        return bcrypt.checkpw(password.encode("utf-8"), hashed.encode("utf-8"))
    except (ValueError, TypeError):
        return False