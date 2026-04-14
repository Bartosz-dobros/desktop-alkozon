import os
from dotenv import load_dotenv

load_dotenv()


def load_config() -> dict:
    return {
        "API_BASE_URL": os.getenv("API_BASE_URL"),
        "API_TIMEOUT": int(os.getenv("API_TIMEOUT", 10)),
        "DEBUG": os.getenv("DEBUG", "false").lower() == "true",
    }


def get_api_base_url() -> str:
    return os.getenv("API_BASE_URL", "")


def get_api_timeout() -> int:
    return int(os.getenv("API_TIMEOUT", 10))


def is_debug_mode() -> bool:
    return os.getenv("DEBUG", "false").lower() == "true"
