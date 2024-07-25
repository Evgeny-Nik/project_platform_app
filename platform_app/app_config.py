import logging
import os
from dotenv import load_dotenv
import redis

load_dotenv()

SESSION_KEY = os.getenv('SESSION_KEY')
KUBECONFIG = os.getenv("KUBECONFIG")
DOCKER_HUB_USERNAME = os.getenv('DOCKER_HUB_USERNAME')
DOCKER_HUB_ACCESS_TOKEN = os.getenv('DOCKER_HUB_ACCESS_TOKEN')
REDIS_HOST_URL = os.getenv('REDIS_HOST_URL', 'localhost')
REDIS_HOST_PORT = int(os.getenv('REDIS_HOST_PORT', 6379))
REDIS_HOST_PASSWORD = os.getenv('REDIS_HOST_PASSWORD', None)
SELF_K8S_SERVICE_DNS = 'http://platform-app-service.platform-app.svc.cluster.local/describe'
# Create a Redis client instance for general use
redis_client = redis.StrictRedis(
    host=REDIS_HOST_URL,
    port=REDIS_HOST_PORT,
    db=0,
    password=REDIS_HOST_PASSWORD
)

# Session configuration
SESSION_CONFIG = {
    'SESSION_TYPE': 'redis',
    'SESSION_PERMANENT': False,
    'SESSION_USE_SIGNER': True,
    'SESSION_KEY_PREFIX': 'session:',
    'SESSION_REDIS': redis_client,
}
# for local session management:
# {
#     'SESSION_TYPE': 'filesystem',
#     'SESSION_FILE_DIR': '/tmp/flask_session/',
#     'SESSION_PERMANENT': False
# }

FORBIDDEN_NAMESPACES = ['kube-system',
                        'kube-public',
                        'kube-node-lease',
                        'default',
                        'redis',
                        'argocd',
                        'platform-app'
                        ]
OS_ENV = os.environ

logging.basicConfig(level=logging.INFO)

logger = logging.getLogger(__name__)












