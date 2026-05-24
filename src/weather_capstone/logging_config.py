import logging
import sys
import time
from functools import wraps
from typing import Optional, Callable, Any

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

def log_execution_time(logger_name: str) -> Callable[[Callable[..., Any]], Callable[..., Any]]:
    """Decorator to measure and log execution time of functions."""
    def decorator(func: Callable[..., Any]) -> Callable[..., Any]:
        @wraps(func)
        def wrapper(*args: Any, **kwargs: Any) -> Any:
            logger = logging.getLogger(logger_name)
            start_time = time.perf_counter()
            result = func(*args, **kwargs)
            elapsed_time = time.perf_counter() - start_time
            logger.info(f"Function '{func.__name__}' completed in {elapsed_time:.3f} seconds")
            return result
        return wrapper
    return decorator
