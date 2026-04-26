import time
import keyring
from pydantic import BaseModel, EmailStr
from typing import Optional

from desktop_alkozon.services.api_client import api_client


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str
    two_fa_code: Optional[str] = None


class AuthService:
    MAX_ATTEMPTS = 5
    INACTIVITY_TIMEOUT = 1800
    SERVICE_NAME = "desktop_alkozon"

    MOCK_USERS = {
        "manager@example.com": {
            "password": "Manager123!",
            "user": {"email": "manager@example.com", "role": "MANAGER", "firstName": "Jan", "lastName": "Manager"}
        },
        "employee@example.com": {
            "password": "Employee123!",
            "user": {"email": "employee@example.com", "role": "EMPLOYEE", "firstName": "Anna", "lastName": "Pracownik"}
        },
        "demo@demo.com": {
            "password": "demo1234",
            "user": {"email": "demo@demo.com", "role": "MANAGER", "firstName": "Demo", "lastName": "User"}
        }
    }

    def __init__(self):
        self.attempts = 0
        self.locked = False
        self.last_activity = time.time()
        self._current_user = None
        self._mock_mode = False

    def _get_stored_token(self) -> str | None:
        return keyring.get_password(self.SERVICE_NAME, "access_token")

    def _store_tokens(self, access_token: str, refresh_token: str | None = None):
        keyring.set_password(self.SERVICE_NAME, "access_token", access_token)
        if refresh_token:
            keyring.set_password(self.SERVICE_NAME, "refresh_token", refresh_token)
        api_client.set_tokens(access_token, refresh_token)

    def _clear_tokens(self):
        try:
            keyring.delete_password(self.SERVICE_NAME, "access_token")
            keyring.delete_password(self.SERVICE_NAME, "refresh_token")
        except keyring.errors.KeyringError:
            pass
        api_client.clear_tokens()

    async def login(self, email: str, password: str, two_fa_code: str | None = None) -> bool:
        if self.locked:
            return False

        self.attempts += 1
        if self.attempts > self.MAX_ATTEMPTS:
            self.locked = True
            return False

        try:
            payload = {
                "email": email,
                "password": password
            }
            if two_fa_code:
                payload["twoFaCode"] = two_fa_code

            response = await api_client.post("/auth/login", payload)

            access_token = response.get("accessToken") or response.get("access_token", "")
            refresh_token = response.get("refreshToken") or response.get("refresh_token")
            
            if not access_token:
                raise ValueError("No access token in response")

            self._store_tokens(access_token, refresh_token)

            self._current_user = response.get("user") or {
                "email": email,
                "role": response.get("role", "EMPLOYEE")
            }

            self.attempts = 0
            self.update_activity()
            self._mock_mode = False
            return True

        except Exception:
            return self._mock_login(email, password)

    def _mock_login(self, email: str, password: str) -> bool:
        email_lower = email.lower()
        if email_lower in self.MOCK_USERS:
            mock_user = self.MOCK_USERS[email_lower]
            if mock_user["password"] == password:
                self._mock_mode = True
                self._current_user = mock_user["user"]
                self._store_tokens("mock_token_" + str(int(time.time())), None)
                self.attempts = 0
                self.update_activity()
                print("Logged in with mock mode (API unavailable)")
                return True
        
        print("Invalid credentials (mock mode)")
        return False

    def is_mock_mode(self) -> bool:
        return self._mock_mode

    def login_sync(self, email: str, password: str) -> bool:
        if self.locked:
            return False

        self.attempts += 1
        if self.attempts > self.MAX_ATTEMPTS:
            self.locked = True
            return False

        if email and password and len(password) >= 8:
            self.attempts = 0
            self.update_activity()
            return True

        return False

    def update_activity(self):
        self.last_activity = time.time()

    def is_locked(self) -> bool:
        return self.locked

    async def check_inactivity(self, page):
        if time.time() - self.last_activity > self.INACTIVITY_TIMEOUT:
            self._clear_tokens()
            return True
        return False

    def logout(self):
        self._clear_tokens()
        self._current_user = None
        self.attempts = 0
        self.locked = False

    def is_authenticated(self) -> bool:
        token = self._get_stored_token()
        return token is not None and len(token) > 0

    async def refresh_token(self) -> bool:
        try:
            refresh = keyring.get_password(self.SERVICE_NAME, "refresh_token")
            if not refresh:
                return False

            response = await api_client.post("/auth/refresh", {
                "refreshToken": refresh
            })

            self._store_tokens(
                response.get("accessToken", ""),
                response.get("refreshToken")
            )
            return True

        except Exception:
            return False

    def unlock(self):
        self.locked = False
        self.attempts = 0

    def get_current_user(self) -> dict | None:
        return self._current_user


auth_service = AuthService()
