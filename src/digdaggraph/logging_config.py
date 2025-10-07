import logging
import os

def get_logger(name: str) -> logging.Logger:
    level = os.environ.get("DIGDAGGRAPH_LOG_LEVEL", "INFO").upper()
    logging.basicConfig(level=level, format="%(levelname)s %(message)s")
    return logging.getLogger(name)
