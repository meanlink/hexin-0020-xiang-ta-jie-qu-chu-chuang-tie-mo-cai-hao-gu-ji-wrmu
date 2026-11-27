import hashlib
import hmac
import secrets


def digest(password: str, salt: bytes) -> str:
    return hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 600_000).hex()


def encode_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    return f"{salt.hex()}:{digest(password, salt)}"


def verify_password(password: str, encoded: str) -> bool:
    salt, expected = encoded.split(":", 1)
    return hmac.compare_digest(digest(password, bytes.fromhex(salt)), expected)
