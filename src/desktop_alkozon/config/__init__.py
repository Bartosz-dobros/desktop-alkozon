import os

from dotenv import load_dotenv

load_dotenv()


def _get_api_base_url() -> str:
    try:
        from desktop_alkozon._build_config import API_BASE_URL  # type: ignore

        return API_BASE_URL
    except ImportError:
        return os.getenv("API_BASE_URL", "")


def load_config() -> dict:
    return {
        "API_BASE_URL": _get_api_base_url(),
        "API_TIMEOUT": int(os.getenv("API_TIMEOUT", 10)),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
        "DEMO_MODE": os.getenv("DEMO_MODE", "false").lower() == "true",
    }


def get_api_base_url() -> str:
    return _get_api_base_url()


def get_api_timeout() -> int:
    return int(os.getenv("API_TIMEOUT", 10))


def is_debug_mode() -> bool:
    return os.getenv("DEBUG", "false").lower() == "true"


def is_demo_mode_enabled() -> bool:
    return os.getenv("DEMO_MODE", "false").lower() == "true"
