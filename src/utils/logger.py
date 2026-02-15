import logging
import sys


def get_logger(name: str | None = None) -> logging.Logger:
    """Get or create a logger with consistent configuration."""
    logger = logging.getLogger(name or __name__)

    if not logger.handlers:
        console_handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            "%(levelname)s - %(filename)s:%(lineno)d - %(message)s"
        )
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        logger.setLevel(logging.INFO)
        logger.propagate = False

    return logger