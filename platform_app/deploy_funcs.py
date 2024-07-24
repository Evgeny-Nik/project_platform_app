from app_config import logger, DOCKER_HUB_USERNAME
from kubernetes_funcs import run_command, namespace_exists, k8s_api_client, fetch_kubernetes_data
from kubernetes import client
from cache_config import update_kubernetes_data_cache, get_kubernetes_ns_list, update_kubernetes_ns_list
import sys


def deploy_application(namespace, image_repository, image_tag, chart_path):
    """Deploy or upgrade the application using Helm from a local chart path."""
    # Ensure no newline or carriage return characters in the variables
    docker_hub_username = DOCKER_HUB_USERNAME.strip()
    image_repository = image_repository.strip()
    image_tag = image_tag.strip()
    namespace = namespace.strip()
    chart_path = chart_path.strip()

    release_name = f"my-app-{namespace}"
    # Deploy or upgrade the application
    command = (
        f"helm upgrade --install {release_name} {chart_path} "
        f"--namespace {namespace} "
        f"--set deployment.container.image={docker_hub_username}/{image_repository} "
        f"--set deployment.container.tag={image_tag} "
        f"--set namespace={namespace}"
    )
    try:
        logger.debug(run_command(command))
        logger.debug(f'Application deployed with image tag "{image_tag}" in namespace '
                     f'"{namespace}" from chart path "{chart_path}".')
        # Fetch and update the Kubernetes data cache
        kubernetes_data = fetch_kubernetes_data()
        update_kubernetes_data_cache(kubernetes_data)
        return None
    except Exception as e:
        logger.error(e)
        return e


def deploy_application_main(namespace, image_repository, image_tag, chart_path):
    """Deploy or upgrade the application using Helm."""
    result = None
    if namespace_exists(namespace) is None:
        logger.error("Error checking namespace existence.", file=sys.stderr)
        return None

    if not namespace_exists(namespace):
        result = create_namespace(namespace)

    if not result:
        result = deploy_application(namespace, image_repository, image_tag, chart_path)
    return result


def create_namespace(namespace):
    """Create a Kubernetes namespace using the Kubernetes API."""
    v1 = client.CoreV1Api(k8s_api_client)
    ns = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
    try:
        # Create the namespace in Kubernetes
        v1.create_namespace(ns)

        # Retrieve the current list of namespaces from Redis
        cached_namespaces = get_kubernetes_ns_list()

        if namespace not in cached_namespaces:
            # Add the new namespace to the list and update the cache
            cached_namespaces.append(namespace)
            update_kubernetes_ns_list(cached_namespaces)
            logger.debug(f"Namespace '{namespace}' created and added to cache.")
            return None
        else:
            logger.warning(f"Namespace '{namespace}' already exists in cache.")
            return f"Namespace '{namespace}' already exists in cache."
    except client.exceptions.ApiException as err:
        if err.status == 422:
            logger.error(f"Failed to create namespace '{namespace}': {err.reason}\nDetails: {err.body}")
            # Handle the specific error, e.g., flash a message to the user or return an appropriate response
            return (f"Failed to create namespace '{namespace}': {err.reason}. "
                    f"Namespace names must be lowercase alphanumeric characters or '-', "
                    f"and must start and end with an alphanumeric character.")
        else:
            logger.error(f"Unexpected error occurred: {err.reason}")
            return f"Unexpected error occurred: {err.reason}"

