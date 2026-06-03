import logging
import os


def setup_logger():
    log_dir = os.path.join(
        os.path.dirname(os.path.abspath(__file__)), "..", "..", "logs"
    )
    os.makedirs(log_dir, exist_ok=True)
    log_file = os.path.join(log_dir, "alkozon.log")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler(log_file, mode="w", encoding="utf-8"),
        ],
    )
    logger = logging.getLogger("desktop_alkozon")
    logger.info("Logger initialized - security events ready")
