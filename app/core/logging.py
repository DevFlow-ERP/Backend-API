"""
Logging configuration for the application
애플리케이션 로깅 설정을 정의합니다.
"""

import logging
import sys
from pathlib import Path
from typing import Any

from loguru import logger

from app.config import settings


class InterceptHandler(logging.Handler):
    """
    표준 logging 모듈의 로그를 loguru로 리다이렉트하는 핸들러
    """

    def emit(self, record: logging.LogRecord) -> None:
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = sys._getframe(6), 6
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging() -> None:
    """
    로깅 시스템을 설정합니다.
    - loguru를 사용한 구조화된 로깅
    - 환경별 로그 레벨 설정
    - 파일 및 콘솔 출력 설정
    """
    # Remove default logger
    logger.remove()

    # Console logging format
    log_format = (
        "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | "
        "<level>{level: <8}</level> | "
        "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
        "<level>{message}</level>"
    )

    # Add console handler
    logger.add(
        sys.stdout,
        format=log_format,
        level=settings.LOG_LEVEL,
        colorize=True,
        backtrace=True,
        diagnose=True,
    )

    # Add file handler for production
    if settings.ENVIRONMENT == "production":
        # Create logs directory if it doesn't exist
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)

        # Add file handler with rotation
        logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            format=log_format,
            level=settings.LOG_LEVEL,
            rotation="00:00",  # Rotate at midnight
            retention="30 days",  # Keep logs for 30 days
            compression="zip",  # Compress old logs
            backtrace=True,
            diagnose=True,
        )

        # Add error-only file handler
        logger.add(
            "logs/error_{time:YYYY-MM-DD}.log",
            format=log_format,
            level="ERROR",
            rotation="00:00",
            retention="90 days",  # Keep error logs longer
            compression="zip",
            backtrace=True,
            diagnose=True,
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set log levels for third-party libraries
    for logger_name in ["uvicorn", "uvicorn.access", "uvicorn.error", "fastapi"]:
        logging_logger = logging.getLogger(logger_name)
        logging_logger.handlers = [InterceptHandler()]

    # Suppress overly verbose loggers
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)


def get_logger(name: str) -> Any:
    """
    이름이 지정된 로거를 반환합니다.

    Args:
        name: 로거 이름 (보통 __name__ 사용)

    Returns:
        loguru logger instance
    """
    return logger.bind(name=name)
