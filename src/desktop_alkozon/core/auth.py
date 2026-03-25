import time
import keyring
from cryptography.fernet import Fernet
from pydantic import BaseModel

class LoginCredentials(BaseModel):
    username: str
    password: str
    two_fa_code: str | None = None

auth_service = None

class AuthService:
    MAX_ATTEMPTS = 5
    INACTIVITY_TIMEOUT = 100

    MOCK_USER = "admin"
    MOCK_PASS = "password123"

    def __init__(self):
        self.attempts = 0
        self.locked = False
        self.last_activity = time.time()
        self.fernet = self._get_encryption_key()

    def _get_encryption_key(self) -> Fernet:
        key = keyring.get_password("desktop_alkozon", "encryption_key")
        if not key:
            key = Fernet.generate_key().decode()
            keyring.set_password("desktop_alkozon", "encryption_key", key)
        return Fernet(key.encode())

    def login(self, username: str, password: str, two_fa_code: str | None = None) -> bool:
        if self.locked:
            return False
        self.attempts += 1
        if self.attempts > self.MAX_ATTEMPTS:
            self.locked = True
            return False

        encrypted_pass = self.fernet.encrypt(password.encode()).decode()

        if (username == self.MOCK_USER and 
            password == self.MOCK_PASS and 
            (two_fa_code is None or len(two_fa_code) == 6)):
            
            self.attempts = 0
            self.update_activity()
            keyring.set_password("desktop_alkozon", "auth_token", "mock_token_123")
            return True
        return False

    def update_activity(self):
        self.last_activity = time.time()

    def is_locked(self) -> bool:
        return self.locked

    def check_inactivity(self, page):
        if time.time() - self.last_activity > self.INACTIVITY_TIMEOUT:
            keyring.delete_password("desktop_alkozon", "auth_token")
            return True
        return False

auth_service = AuthService()