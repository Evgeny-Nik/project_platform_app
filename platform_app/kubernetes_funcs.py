from kubernetes import client, config
import time
from datetime import datetime
import subprocess
from cache_config import (get_kubernetes_data_cache, update_kubernetes_data_cache,
                          get_kubernetes_cache_timestamp, update_kubernetes_cache_timestamp,
                          update_kubernetes_ns_list, get_kubernetes_ns_list)
from app_config import logger, KUBECONFIG, OS_ENV


def load_kube_config():
    try:
        if "KUBERNETES_SERVICE_HOST" in OS_ENV:
            # Running inside a Kubernetes cluster
            config.load_incluster_config()
            logger.debug("Loaded in-cluster config")
        else:
            # Running outside of Kubernetes
            kubeconfig_path = KUBECONFIG
            if kubeconfig_path:
                logger.debug(f"Loading kubeconfig from: {kubeconfig_path}")
                config.load_kube_config(config_file=kubeconfig_path)
                logger.debug("Kubeconfig loaded successfully")
            else:
                raise ValueError("KUBECONFIG environment variable not set")

        api_client = client.ApiClient()
        logger.debug("Kubernetes API client created successfully")
        return api_client

    except Exception as e:
        logger.error(f"Error loading kubeconfig or creating API client: {e}")
        # Handle the exception or re-raise if necessary
        raise


k8s_api_client = load_kube_config()


def fetch_kubernetes_data():
    # Load kube config from the default location
    v1 = client.CoreV1Api(k8s_api_client)
    apps_v1 = client.AppsV1Api(k8s_api_client)
    networking_v1 = client.NetworkingV1Api(k8s_api_client)

    namespaces = v1.list_namespace().items
    namespace_dict = {ns.metadata.name: {} for ns in namespaces}

    # Retrieve and process Pods
    pods = v1.list_pod_for_all_namespaces()
    for pod in pods.items:
        ns = pod.metadata.namespace
        container_statuses = pod.status.container_statuses or []
        namespace_dict[ns].setdefault('Pods', []).append({
            'name': pod.metadata.name,
            'ready': f"{sum(c.ready for c in container_statuses)}/{len(container_statuses)}",
            'status': pod.status.phase,
            'restarts': sum(c.restart_count for c in container_statuses),
            'age': convert_datetime_to_str(pod.metadata.creation_timestamp)
        })

    # Retrieve and process Deployments
    deployments = apps_v1.list_deployment_for_all_namespaces()
    for deployment in deployments.items:
        ns = deployment.metadata.namespace
        namespace_dict[ns].setdefault('Deployments', []).append({
            'name': deployment.metadata.name,
            'ready': f"{deployment.status.ready_replicas or 0}/{deployment.status.replicas or 0}",
            'up_to_date': deployment.status.updated_replicas or 0,
            'available': deployment.status.available_replicas or 0,
            'age': convert_datetime_to_str(deployment.metadata.creation_timestamp)
        })

    # Retrieve and process ReplicaSets
    replicasets = apps_v1.list_replica_set_for_all_namespaces()
    for replicaset in replicasets.items:
        ns = replicaset.metadata.namespace
        namespace_dict[ns].setdefault('ReplicaSets', []).append({
            'name': replicaset.metadata.name,
            'desired': replicaset.spec.replicas or 0,
            'current': replicaset.status.replicas or 0,
            'ready': replicaset.status.ready_replicas or 0,
            'age': convert_datetime_to_str(replicaset.metadata.creation_timestamp)
        })

    # Retrieve and process DaemonSets
    daemonsets = apps_v1.list_daemon_set_for_all_namespaces()
    for daemonset in daemonsets.items:
        ns = daemonset.metadata.namespace
        node_selector = daemonset.spec.template.spec.node_selector or {}
        node_selector_str = ', '.join([f"{k}={v}" for k, v in node_selector.items()])
        namespace_dict[ns].setdefault('DaemonSets', []).append({
            'name': daemonset.metadata.name,
            'desired': daemonset.status.desired_number_scheduled or 0,
            'current': daemonset.status.current_number_scheduled or 0,
            'ready': daemonset.status.number_ready or 0,
            'up_to_date': daemonset.status.updated_number_scheduled or 0,
            'available': daemonset.status.number_available or 0,
            'node_selector': node_selector_str,
            'age': convert_datetime_to_str(daemonset.metadata.creation_timestamp)
        })

    # Retrieve and process StatefulSets
    statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
    for statefulset in statefulsets.items:
        ns = statefulset.metadata.namespace
        namespace_dict[ns].setdefault('StatefulSets', []).append({
            'name': statefulset.metadata.name,
            'ready': f"{statefulset.status.ready_replicas or 0}/{statefulset.spec.replicas or 0}",
            'age': convert_datetime_to_str(statefulset.metadata.creation_timestamp)
        })

    # Retrieve and process Services
    services = v1.list_service_for_all_namespaces()
    for service in services.items:
        ns = service.metadata.namespace
        external_ips = service.status.load_balancer.ingress or []
        external_ip_str = ', '.join([ip.ip if ip.ip else '' for ip in external_ips])

        namespace_dict[ns].setdefault('Services', []).append({
            'name': service.metadata.name,
            'type': service.spec.type,
            'cluster_ip': service.spec.cluster_ip,
            'external_ip': external_ip_str,
            'ports': ', '.join([f"{p.port}/{p.protocol}" for p in service.spec.ports]),
            'age': convert_datetime_to_str(service.metadata.creation_timestamp)
        })

    # Retrieve and process Ingresses
    ingresses = networking_v1.list_ingress_for_all_namespaces()
    for ingress in ingresses.items:
        ns = ingress.metadata.namespace
        addresses = ingress.status.load_balancer.ingress or []
        address_str = ', '.join([addr.ip if addr.ip else '' for addr in addresses])

        namespace_dict[ns].setdefault('Ingresses', []).append({
            'name': ingress.metadata.name,
            'class': ingress.spec.ingress_class_name,
            'hosts': ', '.join([rule.host for rule in ingress.spec.rules]),
            'address': address_str,
            'ports': ', '.join([str(p.backend.service.port.number) if p.backend and p.backend.service else
                                'N/A' for rule in ingress.spec.rules for p in rule.http.paths]),
            'age': convert_datetime_to_str(ingress.metadata.creation_timestamp)
        })

    return namespace_dict


def convert_datetime_to_str(data):
    """Convert datetime objects to ISO 8601 format strings."""
    if isinstance(data, dict):
        return {key: convert_datetime_to_str(value) for key, value in data.items()}
    elif isinstance(data, list):
        return [convert_datetime_to_str(item) for item in data]
    elif isinstance(data, datetime):
        return data.isoformat()
    else:
        return data


def update_kubernetes_cache():
    while True:
        kubernetes_json = fetch_kubernetes_data()
        if kubernetes_json:
            update_kubernetes_data_cache(kubernetes_json)
            update_kubernetes_cache_timestamp(datetime.now())
            logger.debug(f"\nkubernetes_data_cache : {get_kubernetes_data_cache()}\n")
            logger.debug(f"\nkubernetes_cache_timestamp : {get_kubernetes_cache_timestamp()}\n")
            logger.debug("Kubernetes data parsed and cached successfully.")
        time.sleep(60)  # Update every minute


def update_k8s_namespace_list():
    while True:
        new_list = get_namespaces()
        if new_list:
            update_kubernetes_ns_list(new_list)
            logger.debug("Kubernetes namespace list has been updated successfully")
        time.sleep(60)


def get_namespaces():
    try:
        # Create an instance of the CoreV1Api
        v1 = client.CoreV1Api(k8s_api_client)
        # Get the list of namespaces
        namespaces = v1.list_namespace()
        # Extract and filter namespace names
        namespace_names = [ns.metadata.name for ns in namespaces.items]
        logger.debug(f"namespace_names: {namespace_names}")
        return namespace_names
    except client.exceptions.ApiException as e:
        logger.error(f"Error fetching namespaces: {e}")
        return []
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return []


def namespace_exists(namespace):
    if not get_kubernetes_ns_list():
        return "Error, no Namespace data"
    try:
        return namespace in get_kubernetes_ns_list()
    except Exception as e:
        logger.error(f"Error checking namespace existence: {e}")
        return False


def run_command(command):
    """Run a shell command and return its output or log an error if it fails."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8').strip()
        stderr = result.stderr.decode('utf-8').strip()
        logger.debug(f"Command output: {stdout}")
        logger.debug(f"Command error: {stderr}")
        return 0
    except subprocess.CalledProcessError as e:
        stdout = e.stdout.decode('utf-8').strip() if e.stdout else ''
        stderr = e.stderr.decode('utf-8').strip() if e.stderr else ''
        logger.error(f"Command failed with exit code {e.returncode}")
        logger.error(f"Command output: {stdout}")
        logger.error(f"Command error: {stderr}")
        return stderr
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        return str(e)
