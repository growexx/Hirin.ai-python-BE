import logging
from logging.handlers import RotatingFileHandler

# Configure logger
logger = logging.getLogger("app_logger")
log_level = logging.DEBUG
log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
log_file = 'app.log'

file_handler = RotatingFileHandler(log_file, maxBytes=10 * 1024 * 1024, backupCount=5)
file_handler.setLevel(log_level)
file_handler.setFormatter(logging.Formatter(log_format))

logger.setLevel(log_level)
logger.addHandler(file_handler)
