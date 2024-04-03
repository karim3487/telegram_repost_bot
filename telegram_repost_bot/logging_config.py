import logging
import sys


def setup_logger(name, level=logging.INFO):
    logger = logging.getLogger(name)
    logger.setLevel(level)

    file_handler = logging.FileHandler(f"{__name__}.log")
    formatter = logging.Formatter("%(name)s %(asctime)s %(levelname)s %(message)s")
    file_handler.setFormatter(formatter)

    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    logger.addHandler(file_handler)
    logger.addHandler(console_handler)

    return logger
