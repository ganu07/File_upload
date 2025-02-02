import logging

def get_logger(level=logging.INFO):
    # Set the logging configuration once (in your main app, usually).
    logger = logging.getLogger(__name__)

    # Only set up basicConfig if it's not already set up.
    if not logging.getLogger().hasHandlers():
        logging.basicConfig(level=level)

    return logger
