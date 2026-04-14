import pytest
import os


class TestConfigLoader:
    def test_load_config_returns_dict(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        from desktop_alkozon.config import load_config
        
        config = load_config()
        assert isinstance(config, dict)

    def test_get_api_base_url_function(self, mocker):
        mocker.patch.dict("os.environ", {"API_BASE_URL": "https://test.com"}, clear=True)
        from desktop_alkozon.config import get_api_base_url
        
        result = get_api_base_url()
        assert isinstance(result, str)

    def test_get_api_timeout_returns_int(self, mocker):
        mocker.patch.dict("os.environ", {"API_TIMEOUT": "30"}, clear=True)
        from desktop_alkozon.config import get_api_timeout
        
        result = get_api_timeout()
        assert isinstance(result, int)
        assert result == 30

    def test_is_debug_mode_default(self, mocker):
        mocker.patch.dict("os.environ", {}, clear=True)
        from desktop_alkozon.config import is_debug_mode
        
        assert is_debug_mode() is False

    def test_is_debug_mode_true(self, mocker):
        mocker.patch.dict("os.environ", {"DEBUG": "true"}, clear=True)
        from desktop_alkozon.config import is_debug_mode
        
        assert is_debug_mode() is True

    def test_config_with_empty_values(self, mocker):
        mocker.patch.dict("os.environ", {"API_BASE_URL": ""}, clear=True)
        from desktop_alkozon.config import get_api_base_url
        
        result = get_api_base_url()
        assert result == ""
