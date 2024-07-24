from kubernetes_funcs import namespace_exists, run_command, k8s_api_client, fetch_kubernetes_data
from app_config import logger, FORBIDDEN_NAMESPACES
import time
from kubernetes import client
from cache_config import update_kubernetes_data_cache, get_kubernetes_ns_list, update_kubernetes_ns_list


def delete_application_main(namespace):
    """Delete the application using delete_app.py."""
    if not namespace_exists(namespace):
        logger.error(f"Namespace '{namespace}' does not exist.")
        return f"Namespace '{namespace}' does not exist."
    if namespace in FORBIDDEN_NAMESPACES:
        logger.error(f"Namespace '{namespace}' cannot be deleted.")
        return f"Namespace '{namespace}' cannot be deleted."
    try:
        delete_application(namespace)
        delete_namespace(namespace)
        time.sleep(5)  # Wait for Kubernetes to process deletion
        return None
    except Exception as e:
        error_message = str(e)
        logger.error(f"An unexpected error occurred: {error_message}")
        return error_message


def delete_application(namespace):
    """Delete the Helm release in the specified namespace."""
    release_name = f"my-app-{namespace}"

    # Uninstall the Helm release
    result = run_command(f"helm uninstall {release_name} --namespace {namespace}")
    if result:
        logger.error(f"Error uninstalling app {release_name} in namespace {namespace}\n"
                     f"Reason: {result}")
    else:
        logger.debug(f"Application in namespace '{namespace}' deleted.")
    # Fetch and update the Kubernetes data cache
    kubernetes_data = fetch_kubernetes_data()
    update_kubernetes_data_cache(kubernetes_data)
    logger.debug('Kubernetes data cache updated.')


def delete_namespace(namespace):
    """Delete a Kubernetes namespace using the Kubernetes API."""
    try:
        v1 = client.CoreV1Api(k8s_api_client)
        v1.delete_namespace(name=namespace)
        logger.debug(f"Namespace '{namespace}' deleted.")
        # Update the namespace list in Redis cache
        ns_list = get_kubernetes_ns_list()
        if namespace in ns_list:
            ns_list.remove(namespace)
            update_kubernetes_ns_list(ns_list)
            logger.debug(f"Namespace '{namespace}' removed from the cached namespace list.")
        else:
            logger.debug(f"Namespace '{namespace}' was not found in the cached namespace list.")

    except client.exceptions.ApiException as e:
        if e.status == 404:
            logger.error(f"Namespace '{namespace}' not found for deletion.")
        else:
            logger.error(f"Failed to delete namespace '{namespace}': {str(e)}")
            raise
