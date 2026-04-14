import pytest
import keyring
from desktop_alkozon.core.auth import AuthService, LoginCredentials


@pytest.fixture
def auth_service(mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
    mocker.patch("desktop_alkozon.core.auth.keyring.set_password")
    mocker.patch("desktop_alkozon.core.auth.keyring.delete_password")
    return AuthService()


def test_login_success(auth_service, valid_credentials):
    result = auth_service.login(valid_credentials["username"], valid_credentials["password"])
    assert result is True


def test_login_failure_wrong_password(auth_service, valid_credentials):
    result = auth_service.login(valid_credentials["username"], "wrongpassword")
    assert result is False


def test_login_failure_wrong_username(auth_service):
    result = auth_service.login("wronguser", "password123")
    assert result is False


def test_login_with_2fa_valid(auth_service, valid_credentials, two_fa_code):
    result = auth_service.login(valid_credentials["username"], valid_credentials["password"], two_fa_code)
    assert result is True


def test_login_with_2fa_invalid_length(auth_service, valid_credentials):
    result = auth_service.login(valid_credentials["username"], valid_credentials["password"], "123")
    assert result is False


def test_account_lockout_after_max_attempts(auth_service):
    auth_service.attempts = 0
    auth_service.locked = False
    
    for _ in range(AuthService.MAX_ATTEMPTS + 1):
        auth_service.login("wrong", "wrong")
    
    assert auth_service.is_locked() is True


def test_login_updates_activity(auth_service, valid_credentials):
    initial_activity = auth_service.last_activity
    auth_service.login(valid_credentials["username"], valid_credentials["password"])
    
    assert auth_service.last_activity >= initial_activity


def test_check_inactivity_within_timeout(auth_service):
    auth_service.last_activity = auth_service.last_activity
    result = auth_service.check_inactivity(None)
    assert result is False


def test_check_inactivity_expired(auth_service, mocker):
    auth_service.last_activity = 0
    result = auth_service.check_inactivity(None)
    assert result is True


def test_credentials_model_validation():
    creds = LoginCredentials(username="test", password="pass")
    assert creds.username == "test"
    assert creds.password == "pass"
    assert creds.two_fa_code is None
    
    creds_with_2fa = LoginCredentials(username="test", password="pass", two_fa_code="123456")
    assert creds_with_2fa.two_fa_code == "123456"


def test_logout_clears_token(auth_service, valid_credentials, mocker):
    auth_service.login(valid_credentials["username"], valid_credentials["password"])
    
    keyring.delete_password.reset_mock()
    auth_service.logout()
    
    keyring.delete_password.assert_called_once_with("desktop_alkozon", "auth_token")


def test_is_authenticated_with_valid_token(auth_service, mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value="mock_token_123")
    
    assert auth_service.is_authenticated() is True


def test_is_authenticated_without_token(auth_service, mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value=None)
    
    assert auth_service.is_authenticated() is False


def test_token_refresh_updates_token(auth_service, mocker):
    mocker.patch("desktop_alkozon.core.auth.keyring.get_password", return_value="old_token")
    
    auth_service.refresh_token("new_token_456")
    
    keyring.set_password.assert_called_with("desktop_alkozon", "auth_token", "new_token_456")


def test_login_with_2fa_none_vs_absent(auth_service, valid_credentials):
    result_with_none = auth_service.login(valid_credentials["username"], valid_credentials["password"], two_fa_code=None)
    result_without_param = auth_service.login(valid_credentials["username"], valid_credentials["password"])
    assert result_with_none is True
    assert result_without_param is True


def test_account_lockout_after_specific_attempts(auth_service):
    auth_service.attempts = 0
    auth_service.locked = False
    
    for _ in range(AuthService.MAX_ATTEMPTS + 1):
        auth_service.login("wrong", "wrong")
    
    assert auth_service.locked is True


def test_unlock_resets_attempts(auth_service, mocker):
    auth_service.locked = True
    auth_service.attempts = AuthService.MAX_ATTEMPTS
    
    auth_service.unlock()
    
    assert auth_service.locked is False
    assert auth_service.attempts == 0


def test_login_sets_token_in_keyring(auth_service, valid_credentials, mocker):
    auth_service.login(valid_credentials["username"], valid_credentials["password"])
    
    keyring.set_password.assert_called()
