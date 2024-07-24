"""Module for gunicorn wsgi usage."""
from app import app
from kubernetes_funcs import update_k8s_namespace_list, update_kubernetes_cache
from docker_funcs import update_docker_images_cache_loop
import threading


def start_background_threads():
    # Start background thread for cache updates
    thread_docker = threading.Thread(target=update_docker_images_cache_loop, daemon=True)
    thread_docker.start()
    # Start background thread for namespace updates
    thread_namespaces = threading.Thread(target=update_k8s_namespace_list, daemon=True)
    thread_namespaces.start()
    # Start thread for updating Kubernetes cache
    thread_k8s_resources = threading.Thread(target=update_kubernetes_cache, daemon=True)
    thread_k8s_resources.start()


if __name__ == "__main__":
    start_background_threads()
    app.run()
