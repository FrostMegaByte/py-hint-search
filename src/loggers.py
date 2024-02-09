import os
from datetime import datetime
import logging


def _create_logger(name: str, log_file: str) -> logging.Logger:
    logger = logging.getLogger(name)
    logger.setLevel(logging.DEBUG)
    handler = logging.FileHandler(log_file)
    handler.setLevel(logging.DEBUG)
    formatter = logging.Formatter(
        "%(asctime)s %(levelname)-8s [%(filename)s:%(lineno)d] %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


def create_main_logger() -> logging.Logger:
    logs_path = os.path.abspath(os.path.join(os.getcwd(), "logs"))
    os.makedirs(logs_path, exist_ok=True)
    log_file = f"logs/{datetime.today().strftime('%Y-%m-%d %H_%M_%S')}.txt"
    return _create_logger("main", log_file)


def create_evaluation_logger() -> logging.Logger:
    evaluation_logs_path = os.path.abspath(os.path.join(os.getcwd(), "logs-evaluation"))
    os.makedirs(evaluation_logs_path, exist_ok=True)
    log_file = f"logs-evaluation/{datetime.today().strftime('%Y-%m-%d %H_%M_%S')}.txt"
    return _create_logger("evaluation", log_file)


def close_logger(logger: logging.Logger) -> None:
    for handler in logger.handlers:
        handler.close()
        logger.removeHandler(handler)
