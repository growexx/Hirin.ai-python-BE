import logging
import logging.config
import logging.handlers
from queue import Queue
from threading import Thread
import os

log_dir = os.path.join(os.getcwd(), 'logs')
log_file = os.path.join(log_dir, 'app.log.jsonl')

if not os.path.exists(log_dir):
    os.makedirs(log_dir)

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(levelname)s|%(module)s|L%(lineno)d] %(asctime)s: %(message)s",
            "datefmt": "%Y-%m-%dT%H:%M:%S%z"
        },
        "json": {
            "()": "logging.Formatter",
            "format": '{"level": "%(levelname)s", "timestamp": "%(asctime)s", "message": "%(message)s", "module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        }
    },
    "handlers": {
        "queue": {
            "class": "logging.handlers.QueueHandler",
            "queue": None  # Set programmatically later
        },
        "stderr": {
            "class": "logging.StreamHandler",
            "level": "WARNING",
            "formatter": "simple",
            "stream": "ext://sys.stderr"
        },
        "file_json": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "json",
            "filename": "logs/app.log.jsonl",
            "maxBytes": 1048576,
            "backupCount": 5
        }
    },
    "root": {
        "level": "INFO",
        "handlers": ["queue"]
    }
}

log_queue = Queue()

file_handler = logging.handlers.RotatingFileHandler(
    filename="logs/app.log.jsonl",
    maxBytes=1048576,
    backupCount=5
)
file_handler.setFormatter(logging.Formatter('{"level": "%(levelname)s", "message": "%(message)s", "time": "%(asctime)s"}'))

stderr_handler = logging.StreamHandler()
stderr_handler.setFormatter(logging.Formatter("[%(levelname)s|%(module)s] %(message)s"))
listener = logging.handlers.QueueListener(log_queue, file_handler, stderr_handler)
LOGGING_CONFIG["handlers"]["queue"]["queue"] = log_queue
logging.config.dictConfig(LOGGING_CONFIG)
listener.start()
logger = logging.getLogger("app_logger")