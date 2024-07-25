from app_config import logger
from wsgi import start_background_threads
import multiprocessing


def post_fork(server, worker):
    logger.debug("Gunicorn post-fork hook executing")
    start_background_threads()  # Start background threads
    logger.debug("Gunicorn started background threads")


# General settings
bind = '0.0.0.0:8000'
workers = 2
threads = 2
timeout = 120
graceful_timeout = 120
keepalive = 2

# Logging settings
loglevel = 'info'
accesslog = '-'
errorlog = '-'

# Additional settings (optional)
worker_class = 'sync'  # or 'gevent', 'eventlet' for async workers
