from app_config import logger
from wsgi import start_background_threads
from kubernetes_funcs import load_kube_config  # Assuming load_kube_config is defined in app.py


def post_fork(server, worker):
    logger.info("Gunicorn post-fork hook executing")
    load_kube_config()  # Load Kubernetes configuration
    logger.info("Gunicorn loaded kube-config")
    start_background_threads()  # Start background threads
    logger.info("Gunicorn started background threads")


# Other Gunicorn settings
workers = 2
bind = "0.0.0.0:8000"
