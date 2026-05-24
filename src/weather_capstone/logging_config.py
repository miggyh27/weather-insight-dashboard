import logging
import sys
from typing import Optional

def configure_logging(level: int = logging.INFO, log_file: Optional[str] = None) -> None:
    root_logger = logging.getLogger()
    if root_logger.hasHandlers():
        return

    log_format = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    formatter = logging.Formatter(log_format)

    handlers = []
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    handlers.append(console_handler)

    if log_file:
        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setFormatter(formatter)
        handlers.append(file_handler)

    logging.basicConfig(
        level=level,
        format=log_format,
        handlers=handlers
    )
