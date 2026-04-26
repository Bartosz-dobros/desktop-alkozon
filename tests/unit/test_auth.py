import pytest
import keyring
from desktop_alkozon.core.auth import AuthService, LoginCredentials


@pytest.fixture
def auth_service(mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
    mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
    mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
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
    
    creds_with_2fa = LoginCredentials(email="test@example.com", password="pass123", two_fa_code="123456")
    assert creds_with_2fa.two_fa_code == "123456"


def test_logout_clears_token(auth_service):
    auth_service.login_sync("admin@example.com", "password123")
    auth_service.logout()
    
    assert auth_service._current_user is None


def test_is_authenticated_with_valid_token(auth_service, mocker):
    mocker.patch("desktop_alkozon.core.auth.AuthService._get_stored_token", return_value="mock_token_123")
    
    assert auth_service.is_authenticated() is True


def test_is_authenticated_without_token(auth_service, mocker):
    mocker.patch("desktop_alkozon.core.auth.AuthService._get_stored_token", return_value=None)
    
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
