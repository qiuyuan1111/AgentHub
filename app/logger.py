import logging
import sys

from app.config import LOG_LEVEL
from app.request_context import get_request_id


def get_logger(name: str) -> logging.Logger:

    logger = logging.getLogger(name)

    # 防止重复添加 Handler
    if not logger.handlers:

        handler = logging.StreamHandler(sys.stdout)

        handler.addFilter(
            RequestIdFilter()
        )

        formatter = logging.Formatter(
            "%(asctime)s | "
            "%(levelname)s | "
            "%(name)s | "
            "request_id=%(request_id)s | "
            "%(message)s"
        )

        handler.setFormatter(
            formatter
        )

        logger.addHandler(
            handler
        )

        logger.setLevel(
            logging.INFO
        )

        # 把 "INFO" / "DEBUG"
        # 转成 logging.INFO / logging.DEBUG
        # 从 logging 里取出 LOG_LEVEL.upper() ,没有则默认为 logging.INFO
        level = getattr(
            logging,
            LOG_LEVEL.upper(),
            logging.INFO
        )

        logger.setLevel(level)

        logger.propagate = False

    return logger

class RequestIdFilter(logging.Filter):

    def filter(
        self,
        record
    ):
        record.request_id = get_request_id()

        return True