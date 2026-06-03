import hashlib
from unittest.mock import AsyncMock, MagicMock

import bcrypt
import pytest

from desktop_alkozon.core.auth import AuthService, LoginCredentials


@pytest.fixture
def auth_service(mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
    mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
    mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
    mocker.patch.object(
        AuthService, "_load_two_fa_code", new=AsyncMock(return_value=None)
    )
    return AuthService()


def test_login_sync_success(auth_service):
    result = auth_service.login_sync("admin@example.com", "password123")
    assert result is True


def test_login_sync_failure_short_password(auth_service):
    result = auth_service.login_sync("admin@example.com", "short")
    assert result is False


def test_login_sync_failure_empty_credentials(auth_service):
    result = auth_service.login_sync("", "")
    assert result is False


def test_login_sync_failure_short_password(auth_service):
    result = auth_service.login_sync("wrong@example.com", "short")
    assert result is False


def test_account_lockout_after_max_attempts(auth_service):
    auth_service.attempts = 0
    auth_service.locked = False

    for _ in range(AuthService.MAX_ATTEMPTS + 1):
        auth_service.login_sync("wrong@example.com", "wrong")

    assert auth_service.is_locked() is True


def test_login_sync_updates_activity(auth_service):
    initial_activity = auth_service.last_activity
    auth_service.login_sync("admin@example.com", "password123")

    assert auth_service.last_activity >= initial_activity


@pytest.mark.asyncio
async def test_check_inactivity_within_timeout(auth_service):
    auth_service.last_activity = auth_service.last_activity
    result = await auth_service.check_inactivity(None)
    assert result is False


@pytest.mark.asyncio
async def test_check_inactivity_expired(auth_service, mocker):
    auth_service.last_activity = 0
    result = await auth_service.check_inactivity(None)
    assert result is True


def test_credentials_model_validation():
    creds = LoginCredentials(email="test@example.com", password="pass123")
    assert creds.email == "test@example.com"
    assert creds.password == "pass123"
    assert creds.two_fa_code is None

    creds_with_2fa = LoginCredentials(
        email="test@example.com", password="pass123", two_fa_code="123456"
    )
    assert creds_with_2fa.two_fa_code == "123456"


def test_logout_clears_token(auth_service):
    auth_service.login_sync("admin@example.com", "password123")
    auth_service.logout()

    assert auth_service._current_user is None


def test_is_authenticated_with_valid_token(auth_service, mocker):
    mocker.patch(
        "desktop_alkozon.core.auth.AuthService._get_stored_token",
        return_value="mock_token_123",
    )

    assert auth_service.is_authenticated() is True


def test_is_authenticated_without_token(auth_service, mocker):
    mocker.patch(
        "desktop_alkozon.core.auth.AuthService._get_stored_token", return_value=None
    )

    assert auth_service.is_authenticated() is False


def test_unlock_resets_attempts(auth_service, mocker):
    auth_service.locked = True
    auth_service.attempts = AuthService.MAX_ATTEMPTS

    auth_service.unlock()

    assert auth_service.locked is False
    assert auth_service.attempts == 0


def test_get_current_user_after_login(auth_service):
    auth_service.login_sync("admin@example.com", "password123")
    assert auth_service._current_user is None


def test_locked_account_blocks_login(auth_service):
    auth_service.locked = True

    result = auth_service.login_sync("admin@example.com", "password123")

    assert result is False


class TestAuthOffline:
    def test_offline_session_flag(self, auth_service):
        auth_service._current_user = None
        assert auth_service.is_offline_session() is False
        auth_service._current_user = {"_offline": True, "email": "test@test.com"}
        assert auth_service.is_offline_session() is True

    @pytest.mark.asyncio
    async def test_has_local_user_no_db(self, auth_service, mocker):
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            side_effect=Exception("DB error"),
        )
        result = await auth_service.has_local_user("test@test.com")
        assert result is False

    @pytest.mark.asyncio
    async def test_has_local_user_found(self, auth_service, mocker):
        fake_cursor = MagicMock()
        fake_cursor.fetchone = AsyncMock(return_value=MagicMock())
        fake_db = AsyncMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=None)
        fake_db.execute = AsyncMock(return_value=fake_cursor)
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            return_value=fake_db,
        )
        assert await auth_service.has_local_user("test@test.com") is True

    @pytest.mark.asyncio
    async def test_verify_local_user_bad_hash(self, auth_service, mocker):
        fake_row = MagicMock()
        fake_row.__getitem__.side_effect = lambda k: {
            "password_hash": "$2b$12$badhash",
            "email": "test@test.com",
            "role": "MANAGER",
            "first_name": None,
            "last_name": None,
            "device_id": "desktop-001",
        }.get(k, "")
        fake_cursor = MagicMock()
        fake_cursor.fetchone = AsyncMock(return_value=fake_row)
        fake_db = AsyncMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=None)
        fake_db.execute = AsyncMock(return_value=fake_cursor)
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            return_value=fake_db,
        )
        result = await auth_service._verify_local_user("test@test.com", "wrongpass")
        assert result is None

    @pytest.mark.asyncio
    async def test_login_offline_failure(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_verify_local_user", return_value=None)
        result = await auth_service.login_offline("test@test.com", "pass")
        assert result is False

    @pytest.mark.asyncio
    async def test_login_offline_success(self, auth_service, mocker):
        mocker.patch.object(
            auth_service,
            "_verify_local_user",
            return_value={
                "email": "test@test.com",
                "role": "MANAGER",
                "_offline": True,
            },
        )
        result = await auth_service.login_offline("test@test.com", "pass")
        assert result is True
        assert auth_service.is_offline_session() is True
        assert auth_service._current_user["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_login_offline_locked(self, auth_service):
        auth_service.locked = True
        result = await auth_service.login_offline("test@test.com", "pass")
        assert result is False

    @pytest.mark.asyncio
    async def test_login_calls_store_local_user(self, auth_service, mocker):
        store_mock = mocker.patch.object(auth_service, "_store_local_user")
        mocker.patch.object(
            auth_service,
            "_decode_jwt",
            return_value={"sub": "1", "email": "a@b.com", "role": "MANAGER"},
        )
        token_response = MagicMock()
        token_response.accessToken = "tok"
        token_response.refreshToken = "ref"
        response_data = MagicMock(spec=["verification_required", "tokens"])
        response_data.verification_required = False
        response_data.tokens = token_response
        mocker.patch(
            "desktop_alkozon.core.auth.StaffLoginResponse",
            return_value=response_data,
        )
        api_client_mock = mocker.patch("desktop_alkozon.core.auth.api_client")
        api_client_mock.post = AsyncMock(
            return_value={"accessToken": "tok", "refreshToken": "ref"}
        )
        result = await auth_service.login("a@b.com", "pass")
        assert result is True
        store_mock.assert_called_once_with("a@b.com", "pass", "MANAGER")
        assert auth_service.is_offline_session() is True
        assert auth_service._current_user["email"] == "test@test.com"

    @pytest.mark.asyncio
    async def test_login_offline_locked(self, auth_service):
        auth_service.locked = True
        result = await auth_service.login_offline("test@test.com", "pass")
        assert result is False

    def test_login_calls_store_local_user(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_store_local_user")
        mocker.patch.object(
            auth_service,
            "_decode_jwt",
            return_value={"sub": "1", "email": "a@b.com", "role": "MANAGER"},
        )
        mocker.patch(
            "desktop_alkozon.core.auth.keyring.set_password",
        )
        mocker.patch("desktop_alkozon.core.auth.api_client")

        token_response = MagicMock()
        token_response.accessToken = "tok"
        token_response.refreshToken = "ref"
        response_data = MagicMock()
        response_data.verification_required = False
        response_data.tokens = token_response
        mocker.patch(
            "desktop_alkozon.core.auth.StaffLoginResponse", return_value=response_data
        )
        api_client_mock = mocker.patch("desktop_alkozon.core.auth.api_client")
        api_client_mock.post = AsyncMock(
            return_value={"accessToken": "tok", "refreshToken": "ref"}
        )

        import asyncio

        result = asyncio.run(auth_service.login("a@b.com", "pass"))
        assert result is True


class TestTwoFA:
    def test_has_two_fa_no_code(self, auth_service):
        assert auth_service.has_two_fa() is False

    def test_has_two_fa_with_code(self, auth_service):
        auth_service._two_fa_code = "$2b$12$somehash"
        assert auth_service.has_two_fa() is True

    def test_is_two_fa_required_below_threshold(self, auth_service):
        auth_service._two_fa_code = "$2b$12$somehash"
        auth_service.attempts = 1
        assert auth_service.is_two_fa_required() is False
        auth_service.attempts = 2
        assert auth_service.is_two_fa_required() is True

    def test_is_two_fa_required_above_threshold(self, auth_service):
        auth_service._two_fa_code = "$2b$12$somehash"
        auth_service.attempts = 3
        assert auth_service.is_two_fa_required() is True
        auth_service.attempts = 5
        assert auth_service.is_two_fa_required() is True

    def test_is_two_fa_required_no_code(self, auth_service):
        auth_service.attempts = 3
        assert auth_service.is_two_fa_required() is False

    def test_is_two_fa_invalid_default(self, auth_service):
        assert auth_service.is_two_fa_invalid() is False

    def test_is_two_fa_invalid_set(self, auth_service):
        auth_service._two_fa_invalid = True
        assert auth_service.is_two_fa_invalid() is True

    def test_logout_clears_two_fa(self, auth_service):
        auth_service._two_fa_code = "$2b$12$somehash"
        auth_service._two_fa_invalid = True
        auth_service.logout()
        assert auth_service._two_fa_code is None
        assert auth_service._two_fa_invalid is False

    def test_unlock_clears_two_fa_invalid(self, auth_service):
        auth_service._two_fa_invalid = True
        auth_service.unlock()
        assert auth_service._two_fa_invalid is False

    def test_verify_two_fa_code_correct(self, auth_service):
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        assert auth_service._verify_two_fa_code(code) is True

    def test_verify_two_fa_code_wrong(self, auth_service):
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        assert auth_service._verify_two_fa_code("5678") is False

    def test_verify_two_fa_code_no_code(self, auth_service):
        assert auth_service._verify_two_fa_code("1234") is False

    @pytest.mark.asyncio
    async def test_login_with_two_fa_required_and_correct(self, auth_service, mocker):
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        auth_service.attempts = auth_service.TWO_FA_AFTER_ATTEMPTS + 1

        mocker.patch.object(auth_service, "_store_local_user")
        mocker.patch.object(
            auth_service,
            "_decode_jwt",
            return_value={"sub": "1", "email": "a@b.com", "role": "MANAGER"},
        )
        token_response = MagicMock()
        token_response.accessToken = "tok"
        token_response.refreshToken = "ref"
        response_data = MagicMock(spec=["verification_required", "tokens"])
        response_data.verification_required = False
        response_data.tokens = token_response
        mocker.patch(
            "desktop_alkozon.core.auth.StaffLoginResponse", return_value=response_data
        )
        api_client_mock = mocker.patch("desktop_alkozon.core.auth.api_client")
        api_client_mock.post = AsyncMock(
            return_value={"accessToken": "tok", "refreshToken": "ref"}
        )

        result = await auth_service.login("a@b.com", "pass", two_fa_code=code)
        assert result is True
        assert auth_service.attempts == 0
        assert auth_service._two_fa_invalid is False

    @pytest.mark.asyncio
    async def test_login_with_two_fa_required_and_wrong(self, auth_service, mocker):
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        auth_service.attempts = auth_service.TWO_FA_AFTER_ATTEMPTS + 1

        mocker.patch.object(
            auth_service,
            "_decode_jwt",
            return_value={"sub": "1", "email": "a@b.com", "role": "MANAGER"},
        )
        token_response = MagicMock()
        token_response.accessToken = "tok"
        token_response.refreshToken = "ref"
        response_data = MagicMock(spec=["verification_required", "tokens"])
        response_data.verification_required = False
        response_data.tokens = token_response
        mocker.patch(
            "desktop_alkozon.core.auth.StaffLoginResponse", return_value=response_data
        )
        api_client_mock = mocker.patch("desktop_alkozon.core.auth.api_client")
        api_client_mock.post = AsyncMock(
            return_value={"accessToken": "tok", "refreshToken": "ref"}
        )

        result = await auth_service.login("a@b.com", "pass", two_fa_code="wrong")
        assert result is False
        assert auth_service.is_two_fa_invalid() is True

    @pytest.mark.asyncio
    async def test_login_two_fa_not_required_below_threshold(
        self, auth_service, mocker
    ):
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        auth_service.attempts = 1

        mocker.patch.object(auth_service, "_store_local_user")
        mocker.patch.object(
            auth_service,
            "_decode_jwt",
            return_value={"sub": "1", "email": "a@b.com", "role": "MANAGER"},
        )
        token_response = MagicMock()
        token_response.accessToken = "tok"
        token_response.refreshToken = "ref"
        response_data = MagicMock(spec=["verification_required", "tokens"])
        response_data.verification_required = False
        response_data.tokens = token_response
        mocker.patch(
            "desktop_alkozon.core.auth.StaffLoginResponse", return_value=response_data
        )
        api_client_mock = mocker.patch("desktop_alkozon.core.auth.api_client")
        api_client_mock.post = AsyncMock(
            return_value={"accessToken": "tok", "refreshToken": "ref"}
        )

        result = await auth_service.login("a@b.com", "pass", two_fa_code="wrong")
        assert result is True
        assert auth_service.is_two_fa_invalid() is False

    @pytest.mark.asyncio
    async def test_login_offline_with_two_fa_required_and_correct(
        self, auth_service, mocker
    ):
        mocker.patch.object(
            auth_service,
            "_verify_local_user",
            return_value={
                "email": "test@test.com",
                "role": "MANAGER",
                "_offline": True,
            },
        )
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        auth_service.attempts = 3

        result = await auth_service.login_offline(
            "test@test.com", "pass", two_fa_code=code
        )
        assert result is True
        assert auth_service.attempts == 0
        assert auth_service._two_fa_invalid is False

    @pytest.mark.asyncio
    async def test_login_offline_with_two_fa_required_and_wrong(
        self, auth_service, mocker
    ):
        mocker.patch.object(
            auth_service,
            "_verify_local_user",
            return_value={
                "email": "test@test.com",
                "role": "MANAGER",
                "_offline": True,
            },
        )
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        code = "1234"
        code_hash = bcrypt.hashpw(code.encode("utf-8"), bcrypt.gensalt()).decode(
            "utf-8"
        )
        auth_service._two_fa_code = code_hash
        auth_service.attempts = 3

        result = await auth_service.login_offline(
            "test@test.com", "pass", two_fa_code="wrong"
        )
        assert result is False
        assert auth_service.is_two_fa_invalid() is True

    @pytest.mark.asyncio
    async def test_login_offline_two_fa_not_required_below_threshold(
        self, auth_service, mocker
    ):
        mocker.patch.object(
            auth_service,
            "_verify_local_user",
            return_value={
                "email": "test@test.com",
                "role": "MANAGER",
                "_offline": True,
            },
        )
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        auth_service._two_fa_code = "$2b$12$somehash"
        auth_service.attempts = 1

        result = await auth_service.login_offline("test@test.com", "pass")
        assert result is True
        assert auth_service.is_two_fa_invalid() is False


class TestHardLockout:
    _TEST_CODE_HASH = hashlib.sha256(b"1595").hexdigest()

    @pytest.mark.asyncio
    async def test_attempt_hard_unlock_not_configured(self, auth_service, mocker):
        auth_service.LOCKOUT_SECURITY_CODE_HASH = None
        auth_service.locked = True
        auth_service.attempts = 5
        success = await auth_service.attempt_hard_unlock("1595")
        assert success is False
        assert auth_service.locked is True

    @pytest.mark.asyncio
    async def test_attempt_hard_unlock_correct_code(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_set_hard_lock", new=AsyncMock())
        auth_service.LOCKOUT_SECURITY_CODE_HASH = self._TEST_CODE_HASH
        auth_service.locked = True
        auth_service.attempts = 5

        success = await auth_service.attempt_hard_unlock("1595")
        assert success is True
        assert auth_service.locked is False
        assert auth_service.attempts == 0

    @pytest.mark.asyncio
    async def test_attempt_hard_unlock_wrong_code(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_set_hard_lock", new=AsyncMock())
        auth_service.LOCKOUT_SECURITY_CODE_HASH = self._TEST_CODE_HASH
        auth_service.locked = True
        auth_service.attempts = 5

        success = await auth_service.attempt_hard_unlock("0000")
        assert success is False
        assert auth_service.locked is True
        assert auth_service.attempts == 5

    @pytest.mark.asyncio
    async def test_attempt_hard_unlock_empty_code(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_set_hard_lock", new=AsyncMock())
        auth_service.LOCKOUT_SECURITY_CODE_HASH = self._TEST_CODE_HASH
        success = await auth_service.attempt_hard_unlock("")
        assert success is False

    @pytest.mark.asyncio
    async def test_is_hard_locked_no_db(self, auth_service, mocker):
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            side_effect=Exception("DB error"),
        )
        result = await auth_service._is_hard_locked()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_hard_locked_false(self, auth_service, mocker):
        fake_cursor = MagicMock()
        fake_cursor.fetchone = AsyncMock(return_value=None)
        fake_db = AsyncMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=None)
        fake_db.execute = AsyncMock(return_value=fake_cursor)
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            return_value=fake_db,
        )
        result = await auth_service._is_hard_locked()
        assert result is False

    @pytest.mark.asyncio
    async def test_is_hard_locked_true(self, auth_service, mocker):
        fake_row = MagicMock()
        fake_row.__getitem__.return_value = "1"
        fake_cursor = MagicMock()
        fake_cursor.fetchone = AsyncMock(return_value=fake_row)
        fake_db = AsyncMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=None)
        fake_db.execute = AsyncMock(return_value=fake_cursor)
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            return_value=fake_db,
        )
        result = await auth_service._is_hard_locked()
        assert result is True

    @pytest.mark.asyncio
    async def test_set_hard_lock_writes_db(self, auth_service, mocker):
        fake_db = AsyncMock()
        fake_db.__aenter__ = AsyncMock(return_value=fake_db)
        fake_db.__aexit__ = AsyncMock(return_value=None)
        fake_db.execute = AsyncMock()
        mocker.patch(
            "desktop_alkozon.core.auth.get_db",
            return_value=fake_db,
        )
        await auth_service._set_hard_lock(True)
        fake_db.execute.assert_called_once_with(
            "INSERT OR REPLACE INTO app_config (key, value) VALUES ('hard_locked', ?)",
            ("1",),
        )

    @pytest.mark.asyncio
    async def test_login_triggers_hard_lockout_after_max_attempts(
        self, auth_service, mocker
    ):
        set_hard_lock_mock = mocker.patch.object(
            auth_service, "_set_hard_lock", new=AsyncMock()
        )
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        mocker.patch(
            "desktop_alkozon.core.auth.api_client.post",
            AsyncMock(side_effect=Exception("API error")),
        )

        auth_service.attempts = 0
        auth_service.locked = False

        for _ in range(AuthService.MAX_ATTEMPTS + 1):
            await auth_service.login("test@test.com", "wrong")

        assert auth_service.locked is True
        set_hard_lock_mock.assert_called_once_with(True)

    @pytest.mark.asyncio
    async def test_hard_unlock_clears_db_lock(self, auth_service, mocker):
        set_hard_lock_mock = mocker.patch.object(
            auth_service, "_set_hard_lock", new=AsyncMock()
        )
        auth_service.LOCKOUT_SECURITY_CODE_HASH = self._TEST_CODE_HASH
        auth_service.locked = True
        auth_service.attempts = 5

        success = await auth_service.attempt_hard_unlock("1595")
        assert success is True
        set_hard_lock_mock.assert_called_once_with(False)

    @pytest.mark.asyncio
    async def test_hard_lock_persists_after_logout(self, auth_service, mocker):
        mocker.patch.object(auth_service, "_set_hard_lock", new=AsyncMock())
        mocker.patch.object(auth_service, "_clear_tokens")
        auth_service.locked = True
        auth_service.attempts = 5
        auth_service._current_user = {"email": "test@test.com"}

        auth_service.logout()
        assert auth_service.locked is False
        assert auth_service.attempts == 0
        auth_service._set_hard_lock.assert_not_called()

    @pytest.mark.asyncio
    async def test_login_offline_respects_lockout(self, auth_service, mocker):
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        mocker.patch.object(auth_service, "_verify_local_user", return_value=None)
        auth_service.locked = True

        result = await auth_service.login_offline("test@test.com", "wrong")
        assert result is False
        assert auth_service.locked is True

    @pytest.mark.asyncio
    async def test_login_offline_does_not_track_attempts(self, auth_service, mocker):
        mocker.patch.object(
            auth_service, "_load_two_fa_code", new=AsyncMock(return_value=None)
        )
        mocker.patch.object(auth_service, "_verify_local_user", return_value=None)
        auth_service.attempts = 0
        auth_service.locked = False

        for _ in range(AuthService.MAX_ATTEMPTS + 1):
            await auth_service.login_offline("test@test.com", "wrong")

        assert auth_service.locked is False
        assert auth_service.attempts == 0
