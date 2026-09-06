import os

from dotenv import load_dotenv
from pwdlib import PasswordHash

load_dotenv()
password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed: str) -> bool:
    return password_hash.verify(password, hashed)


def session_secret() -> str:
    return os.getenv("SECRET_KEY", "development-only-change-me")
