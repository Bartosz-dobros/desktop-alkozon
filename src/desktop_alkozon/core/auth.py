import asyncio
import time

import bcrypt
import httpx
import jwt
import keyring
from pydantic import BaseModel, EmailStr, Field

from desktop_alkozon.core.database import get_db
from desktop_alkozon.models.api_models import TokenResponse
from desktop_alkozon.services.api_client import api_client


class LoginCredentials(BaseModel):
    email: EmailStr
    password: str
    device_id: str = "desktop-001"
    two_fa_code: str | None = None


class StaffLoginResponse(BaseModel):
    verification_required: bool = Field(alias="verificationRequired")
    challenge_id: str | None = Field(alias="challengeId", default=None)
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
        self._pending_password = None

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

            data = await api_client.post("/auth/staff/login", payload)
            if not isinstance(data, dict):
                print(f"Login failed: unexpected response type {type(data)}")
                return False
            response_data = StaffLoginResponse(**data)

            if response_data.verification_required:
                self._pending_challenge = response_data.challenge_id
                self._pending_password = password
                return False
            if not response_data.tokens:
                print("Login failed: API returned no tokens.")
                return False
            self._store_tokens(
                response_data.tokens.accessToken, response_data.tokens.refreshToken
            )

            claims = self._decode_jwt(response_data.tokens.accessToken)
            self._current_user = {
                "id": int(claims.get("sub", 0)),
                "email": claims.get("email", email),
                "role": claims.get("role", "EMPLOYEE"),
            }

            self.attempts = 0
            self.update_activity()
            self._api_unavailable = False
            self._pending_challenge = None
            self._store_local_user(email, password, self._current_user["role"])
            return True

        except httpx.HTTPStatusError as e:
            self._api_unavailable = False
            print(
                f"Login failed! The server rejected the request with this reason: {e.response.text}"
            )
            return False

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
            print(f"Login failed - System error: {e}")
            return False

    async def verify_staff_login(self, challenge_id: str, code: str) -> bool:
        try:
            payload = {
                "challengeId": challenge_id,
                "deviceId": self.DEVICE_ID,
                "code": code,
            }
            data = await api_client.post("/auth/staff/verify-device", payload)
            if not isinstance(data, dict):
                print(f"Verification failed: unexpected response type {type(data)}")
                return False
            response_data = StaffLoginResponse(**data)
            if not response_data.tokens:
                print("Verification failed: API returned no tokens.")
                return False
            self._store_tokens(
                response_data.tokens.accessToken, response_data.tokens.refreshToken
            )

            claims = self._decode_jwt(response_data.tokens.accessToken)
            self._current_user = {
                "id": int(claims.get("sub", 0)),
                "email": claims.get("email", ""),
                "role": claims.get("role", "EMPLOYEE"),
            }

            self.attempts = 0
            self.update_activity()
            self._api_unavailable = False
            self._pending_challenge = None
            password = getattr(self, "_pending_password", None)
            if password:
                self._store_local_user(
                    self._current_user["email"], password, self._current_user["role"]
                )
                self._pending_password = None
            return True

        except httpx.HTTPStatusError as e:
            try:
                error_data = e.response.json()
                if (
                    e.response.status_code == 401
                    and "Invalid verification code" in error_data.get("message", "")
                ):
                    print(
                        "2FA Failure: The user entered an incorrect verification code."
                    )
                    return False
                else:
                    print(
                        f"Verification rejected for a different reason! Status: {e.response.status_code}, Server says: {error_data}"
                    )
                    return False
            except ValueError:
                print(
                    f"Verification rejected! Status: {e.response.status_code}, Raw response: {e.response.text}"
                )
                return False

    async def request_password_reset(self, email: str) -> tuple[bool, str]:
        try:
            await api_client.post_no_content(
                "/auth/password-reset/request", {"email": email}
            )
            return True, "password_reset.sent"
        except httpx.RequestError:
            self._api_unavailable = True
            return False, "password_reset.offline"
        except Exception:
            return False, "password_reset.error"

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

    def _store_local_user(self, email: str, password: str, role: str):
        try:
            password_hash = bcrypt.hashpw(
                password.encode("utf-8"), bcrypt.gensalt()
            ).decode("utf-8")

            async def _store():
                async with get_db() as db:
                    await db.execute(
                        """INSERT OR REPLACE INTO local_user
                           (email, password_hash, role, device_id, last_login)
                           VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)""",
                        (email, password_hash, role, self.DEVICE_ID),
                    )

            task = asyncio.create_task(_store())
            self._background_tasks = getattr(self, "_background_tasks", set())
            self._background_tasks.add(task)
            task.add_done_callback(self._background_tasks.discard)
        except Exception as e:
            print(f"Failed to store local user: {e}")

    async def _verify_local_user(self, email: str, password: str) -> dict | None:
        try:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT * FROM local_user WHERE email = ?", (email,)
                )
                row = await cursor.fetchone()
            if row and bcrypt.checkpw(
                password.encode("utf-8"), row["password_hash"].encode("utf-8")
            ):
                return {
                    "id": 0,
                    "email": row["email"],
                    "role": row["role"],
                    "first_name": row["first_name"],
                    "last_name": row["last_name"],
                    "_offline": True,
                }
        except Exception as e:
            print(f"Failed to verify local user: {e}")
        return None

    async def has_local_user(self, email: str) -> bool:
        try:
            async with get_db() as db:
                cursor = await db.execute(
                    "SELECT 1 FROM local_user WHERE email = ?", (email,)
                )
                return await cursor.fetchone() is not None
        except Exception:
            return False

    async def login_offline(self, email: str, password: str) -> bool:
        if self.locked:
            return False
        user_data = await self._verify_local_user(email, password)
        if user_data:
            self._current_user = user_data
            self.attempts = 0
            self._demo_mode = False
            self._api_unavailable = True
            self.update_activity()
            print(f"Offline login successful for {email}")
            return True
        self.attempts += 1
        if self.attempts > self.MAX_ATTEMPTS:
            self.locked = True
        return False

    def is_offline_session(self) -> bool:
        if self._current_user:
            return self._current_user.get("_offline", False)
        return False

    def logout(self):
        self._clear_tokens()
        self._current_user = None
        self.attempts = 0
        self.locked = False
        self._pending_challenge = None
        self._demo_mode = False

    def is_authenticated(self) -> bool:
        token = self._get_stored_token()
        return token is not None and len(token) > 0

    async def refresh_token(self) -> bool:
        try:
            refresh = keyring.get_password(self.SERVICE_NAME, "refresh_token")
            if not refresh:
                return False

            data = await api_client.post("/auth/refresh", {"refreshToken": refresh})
            if not isinstance(data, dict):
                print(f"Token refresh failed: unexpected response type {type(data)}")
                return False
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
