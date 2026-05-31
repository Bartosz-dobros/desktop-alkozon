import os

import keyring
from cryptography.fernet import Fernet, InvalidToken

SERVICE_NAME = "desktop_alkozon_db"
KEY_ENTRY = "db_encryption_key"


def _get_key() -> bytes:
    key = keyring.get_password(SERVICE_NAME, KEY_ENTRY)
    if key:
        return key.encode("utf-8")
    key = Fernet.generate_key()
    keyring.set_password(SERVICE_NAME, KEY_ENTRY, key.decode("utf-8"))
    return key


async def encrypt_file(source_path: str, dest_path: str):
    key = _get_key()
    f = Fernet(key)
    with open(source_path, "rb") as src:
        data = src.read()
    encrypted = f.encrypt(data)
    with open(dest_path, "wb") as dst:
        dst.write(encrypted)


async def decrypt_file(source_path: str, dest_path: str):
    key = _get_key()
    f = Fernet(key)
    with open(source_path, "rb") as src:
        encrypted = src.read()
    try:
        data = f.decrypt(encrypted)
    except InvalidToken:
        raise ValueError("Database encryption key mismatch or corrupted file") from None
    with open(dest_path, "wb") as dst:
        dst.write(data)


def encrypted_path_for(plain_path: str) -> str:
    return plain_path + ".encrypted"


def clear_plain_file(path: str):
    if os.path.exists(path):
        os.remove(path)
