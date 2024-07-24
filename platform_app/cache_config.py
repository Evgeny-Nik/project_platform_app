from app_config import redis_client
from datetime import datetime
import json

# Define cache keys
KUBERNETES_NS_LIST_KEY = 'kubernetes_ns_list'
KUBERNETES_DATA_CACHE_KEY = 'kubernetes_data_cache'
KUBERNETES_CACHE_TIMESTAMP_KEY = 'kubernetes_cache_timestamp'
DOCKER_IMAGES_CACHE_KEY = 'docker_images_cache'


def set_cache(key, value, expiration=3600):
    """Set a value in the Redis cache."""
    redis_client.setex(key, expiration, json.dumps(value))


def get_cache(key):
    """Get a value from the Redis cache."""
    value = redis_client.get(key)
    return json.loads(value) if value else None


def delete_cache(key):
    """Delete a value from the Redis cache."""
    redis_client.delete(key)


def update_kubernetes_ns_list(ns_list):
    """Update the Kubernetes namespace list in the cache."""
    set_cache(KUBERNETES_NS_LIST_KEY, ns_list)


def get_kubernetes_ns_list():
    """Retrieve the Kubernetes namespace list from the cache."""
    return get_cache(KUBERNETES_NS_LIST_KEY) or []


def update_kubernetes_data_cache(data):
    """Update the Kubernetes data cache in Redis."""
    set_cache(KUBERNETES_DATA_CACHE_KEY, data)


def get_kubernetes_data_cache():
    """Retrieve the Kubernetes data cache from Redis."""
    return get_cache(KUBERNETES_DATA_CACHE_KEY)


def update_kubernetes_cache_timestamp(timestamp):
    # Convert datetime to Unix timestamp
    timestamp_unix = int(timestamp.timestamp())
    redis_client.set(KUBERNETES_CACHE_TIMESTAMP_KEY, timestamp_unix)


def get_kubernetes_cache_timestamp():
    timestamp_unix = redis_client.get(KUBERNETES_CACHE_TIMESTAMP_KEY)
    if timestamp_unix:
        # Convert Unix timestamp back to datetime
        return datetime.fromtimestamp(int(timestamp_unix))
    return None


def update_docker_images_cache(images_cache):
    """Update the Docker images cache in Redis."""
    set_cache(DOCKER_IMAGES_CACHE_KEY, images_cache)


def get_docker_images_cache():
    """Retrieve the Docker images cache from Redis."""
    return get_cache(DOCKER_IMAGES_CACHE_KEY)
