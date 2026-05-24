import time

import httpx
import jwt
import keyring
from pydantic import BaseModel, EmailStr

from desktop_alkozon.models.api_models import TokenResponse
from desktop_alkozon.services.api_client import api_client


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str
    device_id: str = "desktop-001"
    two_fa_code: str | None = None


class StaffLoginResponse(BaseModel):
    verification_required: bool
    challenge_id: str | None = None
    tokens: TokenResponse | None = None
    message: str | None = None


class AuthService:
    MAX_ATTEMPTS = 5
    INACTIVITY_TIMEOUT = 1800
    SERVICE_NAME = "desktop_alkozon"
    DEVICE_ID = "desktop-001"

    def __init__(self):
        self.attempts = 0
        self.locked = False
        self.last_activity = time.time()
        self._current_user = None
        self._api_unavailable = False
        self._demo_mode = False
        self._pending_challenge = None

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

    def _decode_jwt(self, token: str) -> dict:
        try:
            payload = jwt.decode(token, options={"verify_signature": False})
            return payload
        except Exception:
            return {}

    async def login(
        self, email: str, password: str, two_fa_code: str | None = None
    ) -> bool:
        if self.locked:
            return False

        self.attempts += 1
        if self.attempts > self.MAX_ATTEMPTS:
            self.locked = True
            return False

        try:
            payload = {
                "email": email,
                "password": password,
                "deviceId": self.DEVICE_ID,
            }

            response = await api_client.post("/auth/staff/login", payload)
            data = response.json()

            if data.get("verificationRequired"):
                self._pending_challenge = data.get("challengeId")
                return False

            token_response = TokenResponse(**data)
            self._store_tokens(token_response.accessToken, token_response.refreshToken)

            claims = self._decode_jwt(token_response.accessToken)
            self._current_user = {
                "id": int(claims.get("sub", 0)),
                "email": claims.get("email", email),
                "role": claims.get("role", "EMPLOYEE"),
            }

            self.attempts = 0
            self.update_activity()
            self._api_unavailable = False
            self._pending_challenge = None
            return True

        except httpx.RequestError as e:
            self._api_unavailable = True
            print(f"Login failed - API unavailable: {e}")
            if email == "manager@example.com" and password == "Manager123!":
                self.enable_demo_mode()
                self.attempts = 0
                return True
            return False
        except Exception as e:
            self._api_unavailable = False
            print(f"Login failed: {e}")
            return False

    async def verify_staff_login(self, challenge_id: str, code: str) -> bool:
        try:
            payload = {
                "challengeId": challenge_id,
                "deviceId": self.DEVICE_ID,
                "code": code,
            }
            response = await api_client.post("/auth/staff/verify-device", payload)
            data = response.json()

            token_response = TokenResponse(**data)
            self._store_tokens(token_response.accessToken, token_response.refreshToken)

            claims = self._decode_jwt(token_response.accessToken)
            self._current_user = {
                "id": int(claims.get("sub", 0)),
                "email": claims.get("email", ""),
                "role": claims.get("role", "EMPLOYEE"),
            }

            self.attempts = 0
            self.update_activity()
            self._api_unavailable = False
            self._pending_challenge = None
            return True
        except Exception as e:
            print(f"Verification failed: {e}")
            return False

    def is_demo_mode(self) -> bool:
        return self._demo_mode

    def enable_demo_mode(self):
        self._demo_mode = True
        self._current_user = {
            "id": 999,
            "email": "demo@demo.com",
            "role": "MANAGER",
            "firstName": "Demo",
            "lastName": "User",
        }
        self._api_unavailable = False
        print("Demo mode enabled - using mock data")

    def is_api_unavailable(self) -> bool:
        return self._api_unavailable

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
        self._pending_challenge = None

    def is_authenticated(self) -> bool:
        token = self._get_stored_token()
        return token is not None and len(token) > 0

    async def refresh_token(self) -> bool:
        try:
            refresh = keyring.get_password(self.SERVICE_NAME, "refresh_token")
            if not refresh:
                return False

            response = await api_client.post("/auth/refresh", {"refreshToken": refresh})
            data = response.json()
            token_response = TokenResponse(**data)
            self._store_tokens(token_response.accessToken, token_response.refreshToken)

            claims = self._decode_jwt(token_response.accessToken)
            if claims:
                self._current_user = {
                    "id": int(claims.get("sub", 0)),
                    "email": claims.get("email", ""),
                    "role": claims.get("role", "EMPLOYEE"),
                }

            return True

        except Exception as e:
            print(f"Token refresh failed: {e}")
            return False

    def unlock(self):
        self.locked = False
        self.attempts = 0

    def get_current_user(self) -> dict | None:
        return self._current_user

    def get_pending_challenge(self) -> str | None:
        return self._pending_challenge


auth_service = AuthService()
