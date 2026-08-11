import hashlib
import secrets

from fastapi import Request
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify a plain password against a hashed one using Argon2."""
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    """Hash a plain password using Argon2."""
    return pwd_context.hash(password)

def generate_session_token() -> tuple[str, str]:
    """
    Generates a secure random session token.
    Returns:
        Tuple[str, str]: (raw_token, token_hash)
        - raw_token is to be sent to the client in an HttpOnly cookie.
        - token_hash is to be stored in the database.
    """
    raw_token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(raw_token.encode()).hexdigest()
    return raw_token, token_hash

def get_session_token_from_cookie(request: Request) -> str | None:
    """
    Extracts the session token from the secure HttpOnly cookie.
    Cookie name: 'session_token'
    """
    token = request.cookies.get("session_token")
    if not token:
        import os
        if os.getenv("ENVIRONMENT") == "test":
            auth = request.headers.get("Authorization")
            if auth and auth.startswith("Bearer "):
                return auth.split(" ")[1]
    return token

import os

from cryptography.fernet import Fernet


def get_fernet() -> Fernet:
    key = os.environ.get("ENCRYPTION_KEY")
    if not key:
        # Generate a dummy key for tests if not provided
        if os.getenv("ENVIRONMENT") == "test":
            key = Fernet.generate_key().decode()
            os.environ["ENCRYPTION_KEY"] = key
        else:
            raise RuntimeError("ENCRYPTION_KEY environment variable is not set")
    return Fernet(key.encode())

def encrypt_string(plain_text: str) -> str:
    if not plain_text:
        return plain_text
    f = get_fernet()
    return f.encrypt(plain_text.encode()).decode()

def decrypt_string(cipher_text: str) -> str:
    if not cipher_text:
        return cipher_text
    f = get_fernet()
    return f.decrypt(cipher_text.encode()).decode()
