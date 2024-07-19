from flask import Flask, render_template, request, jsonify, url_for, redirect, flash, get_flashed_messages, session
from flask_session import Session
import json
import subprocess
import sys
from kubernetes import client, config
import logging
from dotenv import load_dotenv
import os
import threading
import asyncio
import aiohttp
import time
import requests
import redis

# Load environment variables from .env file
load_dotenv()


app = Flask(__name__)
app.secret_key = os.getenv('SESSION_KEY')  # Set a secret key for session management

# Configure logging
logging.basicConfig(level=logging.INFO)


if "KUBERNETES_SERVICE_HOST" in os.environ:
    # Running inside a Kubernetes cluster
    app.config['SESSION_TYPE'] = 'redis'
    app.config['SESSION_PERMANENT'] = False
    app.config['SESSION_USE_SIGNER'] = True
    app.config['SESSION_KEY_PREFIX'] = 'session:'
    app.config['SESSION_REDIS'] = redis.StrictRedis(
        host=os.getenv('REDIS_HOST_URL', 'localhost'), 
        port=os.getenv('REDIS_HOST_PORT', 6379), 
        db=0,
        password=os.getenv('REDIS_HOST_PASSWORD', None)
    )
else:
    # Configure the session to use filesystem
    app.config['SESSION_TYPE'] = 'filesystem'
    app.config['SESSION_FILE_DIR'] = '/tmp/flask_session/'
    app.config['SESSION_PERMANENT'] = False
Session(app)

# Docker Hub username and access token
DOCKER_HUB_USERNAME = os.getenv('DOCKER_HUB_USERNAME')
DOCKER_HUB_ACCESS_TOKEN = os.getenv('DOCKER_HUB_ACCESS_TOKEN')
# Cache for images and tags
images_cache = {}
namespace_list = []
# Global variables for caching Kubernetes data
kubernetes_data_cache = None
kubernetes_cache_timestamp = 0
FORBIDDEN_NAMESPACES = ['kube-system', 'kube-public', 'kube-node-lease', 'platform-app', 'redis']


def load_kube_config():
    if "KUBERNETES_SERVICE_HOST" in os.environ:
        print("loaded incluster config")
        config.load_incluster_config()
    else:
        kubeconfig_path = os.getenv("KUBECONFIG")
        if kubeconfig_path:
            try:
                logging.info(f"Loading kubeconfig from: {kubeconfig_path}")
                config.load_kube_config(config_file=kubeconfig_path)
                logging.info("Kubeconfig loaded successfully")
            except Exception as e:
                logging.error(f"Error loading kubeconfig: {e}")
        else:
            logging.warning("KUBECONFIG environment variable not set")


async def fetch_image_tags(session, repo_name):
    headers = {
        'Authorization': f'Bearer {DOCKER_HUB_ACCESS_TOKEN}',
        'Accept': 'application/json'
    }
    # Ensure no newline or carriage return characters in the headers
    headers = {k: v.replace('\n', '').replace('\r', '') for k, v in headers.items()}

    url = f"https://hub.docker.com/v2/repositories/{DOCKER_HUB_USERNAME}/{repo_name}/tags/"

    async with session.get(url, headers=headers) as response:
        if response.status == 200:
            data = await response.json()
            tags = [tag['name'] for tag in data.get('results', [])]
            return repo_name, tags
        else:
            logging.error(f"Failed to fetch tags for {repo_name}")
            return repo_name, []


async def fetch_images_and_tags():
    headers = {
        'Accept': 'application/json',
    }
    images_dict = {}
    url = f'https://hub.docker.com/v2/repositories/{DOCKER_HUB_USERNAME}/'

    async with aiohttp.ClientSession(headers=headers) as session:
        while url:
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    repositories = data.get('results', [])
                    tasks = [fetch_image_tags(session, repo['name']) for repo in repositories]
                    results = await asyncio.gather(*tasks)
                    images_dict.update(dict(results))
                else:
                    logging.error("Unable to fetch images")
                url = data.get('next', None)

    return images_dict


async def update_images_cache_and_namespace_list_async():
    global images_cache
    global namespace_list
    while True:
        logging.info("Starting image cache, and namespace list update...")
        images_cache = await fetch_images_and_tags()
        logging.debug(f"Images cache updated: {images_cache}")
        namespace_list = get_namespaces()
        logging.debug(f"Namespace list updated: {namespace_list}")
        # Update every 10 minutes (600 seconds)
        await asyncio.sleep(60)


def update_images_cache():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(update_images_cache_and_namespace_list_async())


@app.route('/api/docker-images', methods=['GET'])
def docker_images():
    return jsonify(images_cache)


@app.route('/api/docker-images/<string:repo_name>/tags', methods=['GET'])
def docker_image_tags(repo_name):
    tags = images_cache.get(repo_name, [])
    return jsonify({repo_name: tags})


def delete_application(namespace):
    """Delete the Helm release in the specified namespace."""
    release_name = f"my-app-{namespace}"
    
    try:
        # Uninstall the Helm release
        result = run_command(f"helm uninstall {release_name} --namespace {namespace}")
        app.logger.info(f"Application in namespace '{namespace}' deleted.")
    except subprocess.CalledProcessError as e:
        # Handle specific errors from helm uninstall command
        error_message = str(e.output) if e.output else str(e)
        print(result.stdout.decode())  # Print stdout
        print(result.stderr.decode())  # Print stderr
        app.logger.error(f"Helm uninstall command failed: {error_message}")
        raise  # Raise the exception to propagate it further
    except Exception as e:
        # Handle other unexpected exceptions
        print(result.stdout.decode())  # Print stdout
        print(result.stderr.decode())  # Print stderr
        app.logger.error(f"An unexpected error occurred: {str(e)}")
        raise  # Raise the exception to propagate it further


def delete_namespace(namespace):
    """Delete a Kubernetes namespace using the Kubernetes API."""
    v1 = client.CoreV1Api()
    try:
        v1 = client.CoreV1Api()
        v1.delete_namespace(name=namespace)
        app.logger.info(f"Namespace '{namespace}' deleted.")
    except client.exceptions.ApiException as e:
        if e.status == 404:
            app.logger.info(f"Namespace '{namespace}' not found for deletion.")
        else:
            app.logger.error(f"Failed to delete namespace '{namespace}': {str(e)}")
            raise


def delete_application_main(namespace):
    """Delete the application using delete_app.py."""
    load_kube_config()

    if not namespace_exists(namespace):
        app.logger.error(f"Namespace '{namespace}' does not exist.")
        flash(f"Namespace '{namespace}' does not exist.")
        return f"Namespace '{namespace}' does not exist."

    try:
        delete_application(namespace)
        delete_namespace(namespace)
        time.sleep(5)  # Wait for Kubernetes to process deletion
        return None
    except Exception as e:
        error_message = str(e)
        app.logger.error(f"An unexpected error occurred: {error_message}")
        flash(f"An unexpected error occurred: {error_message}")
        return error_message


@app.route('/delete', methods=['POST'])
def delete():
    global namespace_list
    global kubernetes_data_cache

    selected_namespace = request.form.get('namespace', '')  # Get selected namespace from form submission
    # Check if there are namespaces available
    if not namespace_list:
        flash("Error, no Namespace data")
        return redirect('/')

    if selected_namespace in namespace_list:
        result = delete_application_main(selected_namespace)
        if result is None:
            namespace_list.remove(selected_namespace)
            kubernetes_data_cache.pop(selected_namespace, None)  # Ensure cache is updated
            if session.get('selected_namespace') == selected_namespace:
                session.pop('kubernetes_data', None)
                session.pop('selected_namespace', None)

        flash(result or f"Deletion of namespace '{selected_namespace}' completed successfully.")
    else:
        flash("Namespace not found or not selected.")

    return redirect('/')


@app.route('/deploy', methods=['POST'])
def deploy():
    global kubernetes_data_cache
    global kubernetes_cache_timestamp

    chart_path = os.getenv("HELM_CHART", "/path/to/helm/chart")
    image_repository = request.form['image_repository']
    image_tag = request.form['image_tag']
    namespace = request.form['deploy_namespace']

    result = deploy_application_main(namespace, image_repository, image_tag, chart_path)
    message = result if result else f"Deployment of {image_repository}:{image_tag} in namespace {namespace} completed."
    # Update Kubernetes data cache
    delay = 2  # Start with 2 seconds
    max_delay = 60  # Max delay time in seconds
    retries = 0

    while retries < 10:  # Try for a maximum of 10 retries
        kubernetes_data_cache = fetch_kubernetes_data()
        if namespace in kubernetes_data_cache and kubernetes_data_cache[namespace]:
            break
        time.sleep(delay)
        delay = min(delay * 2, max_delay)  # Exponentially increase the delay
        retries += 1

    app.logger.debug(f"\ndeploy_cache: {kubernetes_data_cache}\n")  # Log the updated cache for debugging

    # Update session and flash messages
    session['kubernetes_data'] = kubernetes_data_cache
    session['selected_namespace'] = namespace

    flash(message)

    # Make an internal POST request to /describe with namespace data
    describe_url = url_for('describe_kubernetes', _external=True)
    response = requests.post(describe_url, data={'namespace': namespace, 'message': message})

    # Check if the request was successful and handle accordingly
    if response.status_code == 200:
        return response.text  # Or handle the response as needed
    else:
        flash("Failed to describe Kubernetes data.")
        return redirect(url_for('index'))


@app.route('/describe', methods=['POST'])
def describe_kubernetes():
    global kubernetes_data_cache
    global kubernetes_cache_timestamp

    selected_namespace = request.form.get('namespace', '')  # Get selected namespace from form submission
    message = request.form.get('message', '')

    # Only fetch Kubernetes data if a namespace is selected
    if selected_namespace:
        parsed_data = kubernetes_data_cache.get(selected_namespace, {})
        if not parsed_data:
            message += ", in /describe No Kubernetes data available."
        app.logger.debug(f"\nparsed data: {parsed_data}")
        session['kubernetes_data'] = parsed_data
        session['selected_namespace'] = selected_namespace
    else:
        flash("No namespace selected.")
        return redirect('/')
    
    if message:
        flash(message)
    else:
        flash(f"Viewing data for Namespace {selected_namespace}")

    # Redirect to index with parsed_data_json as query parameter
    return redirect('/')


@app.route('/', methods=['GET', 'POST'])
async def index():
    data = None
    namespace = None
    # Retrieve kubernetes_data from session
    kubernetes_data = session.get('kubernetes_data')
    selected_namespace = session.get('selected_namespace')
    if kubernetes_data and selected_namespace:
        data = kubernetes_data
        namespace = selected_namespace

    # Check for flashed messages
    messages = [msg for msg in get_flashed_messages()]

    # Render the page with Kubernetes data
    return render_template('index.html',
                           namespaces=namespace_list,
                           sel_namespace=namespace,
                           kubernetes_data=data,
                           images_cache=images_cache,
                           kubernetes_data_cache=kubernetes_data_cache,
                           messages=messages)


def run_command(command):
    """Run a shell command and return its output or log an error if it fails."""
    try:
        result = subprocess.run(command, shell=True, check=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout = result.stdout.decode('utf-8').strip()
        stderr = result.stderr.decode('utf-8').strip()
        app.logger.info(f"Command output: {stdout}")
        app.logger.info(f"Command error: {stderr}")
        return stdout
    except subprocess.CalledProcessError as e:
        stdout = e.stdout.decode('utf-8').strip() if e.stdout else ''
        stderr = e.stderr.decode('utf-8').strip() if e.stderr else ''
        app.logger.info(f"Command failed with exit code {e.returncode}")
        app.logger.info(f"Command output: {stdout}")
        app.logger.info(f"Command error: {stderr}")
        return stderr
    except Exception as e:
        app.logger.info(f"Unexpected error: {e}")
        return str(e)


def create_namespace(namespace):
    """Create a Kubernetes namespace using the Kubernetes API."""
    global namespace_list
    v1 = client.CoreV1Api()
    ns = client.V1Namespace(metadata=client.V1ObjectMeta(name=namespace))
    v1.create_namespace(ns)
    namespace_list.append(namespace)
    app.logger.info(f"Namespace '{namespace}' created.")


def deploy_application(namespace, image_repository, image_tag, chart_path):
    """Deploy or upgrade the application using Helm from a local chart path."""
    # Ensure no newline or carriage return characters in the variables
    docker_hub_username = DOCKER_HUB_USERNAME.strip()
    image_repository = image_repository.strip()
    image_tag = image_tag.strip()
    namespace = namespace.strip()
    chart_path = chart_path.strip()

    release_name = f"my-app-{namespace}"
    check_helm()
    # Deploy or upgrade the application
    command = (
        f"helm upgrade --install {release_name} {chart_path} "
        f"--namespace {namespace} "
        f"--set deployment.container.image={docker_hub_username}/{image_repository} "
        f"--set deployment.container.tag={image_tag} "
        f"--set namespace={namespace}"
    )
    app.logger.info(run_command(command))
    app.logger.info(f'Application deployed with image tag "{image_tag}" in namespace '
                    f'"{namespace}" from chart path "{chart_path}".')


def check_helm():
    """Check helm installation."""
    app.logger.info(run_command("which helm"))
    app.logger.info(run_command("helm version"))


def deploy_application_main(namespace, image_repository, image_tag, chart_path):
    """Deploy or upgrade the application using Helm."""
    load_kube_config()

    if namespace_exists(namespace) is None:
        app.logger.error("Error checking namespace existence.", file=sys.stderr)
        sys.exit(1)

    if not namespace_exists(namespace):
        create_namespace(namespace)
    deploy_application(namespace, image_repository, image_tag, chart_path)


def get_namespaces():
    try:
        # Load the Kubernetes configuration
        load_kube_config()
        # Create an instance of the CoreV1Api
        v1 = client.CoreV1Api()
        # Get the list of namespaces
        namespaces = v1.list_namespace()
        # Extract and filter namespace names
        namespace_names = [ns.metadata.name for ns in namespaces.items if
                           ns.metadata.name not in FORBIDDEN_NAMESPACES]
        app.logger.debug(f"namespace_names: {namespace_names}")
        return namespace_names
    except client.exceptions.ApiException as e:
        app.logger.error(f"Error fetching namespaces: {e}")
        return []
    except Exception as e:
        app.logger.error(f"Unexpected error: {e}")
        return []


def namespace_exists(namespace):
    if not namespace_list:
        return "Error, no Namespace data"
    try:
        return namespace in namespace_list
    except Exception as e:
        app.logger.error(f"Error checking namespace existence: {e}")
        return False


def fetch_kubernetes_data():
    # Load kube config from the default location
    load_kube_config()

    v1 = client.CoreV1Api()
    apps_v1 = client.AppsV1Api()
    networking_v1 = client.NetworkingV1Api()

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
            'age': pod.metadata.creation_timestamp
        })

    # Retrieve and process Deployments
    deployments = apps_v1.list_deployment_for_all_namespaces()
    for deployment in deployments.items:
        ns = deployment.metadata.namespace
        namespace_dict[ns].setdefault('Deployments', []).append({
            'name': deployment.metadata.name,
            'ready': f"{deployment.status.ready_replicas}/{deployment.status.replicas or 0}",
            'up_to_date': deployment.status.updated_replicas or 0,
            'available': deployment.status.available_replicas or 0,
            'age': deployment.metadata.creation_timestamp
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
            'age': replicaset.metadata.creation_timestamp
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
            'age': daemonset.metadata.creation_timestamp
        })

    # Retrieve and process StatefulSets
    statefulsets = apps_v1.list_stateful_set_for_all_namespaces()
    for statefulset in statefulsets.items:
        ns = statefulset.metadata.namespace
        namespace_dict[ns].setdefault('StatefulSets', []).append({
            'name': statefulset.metadata.name,
            'ready': f"{statefulset.status.ready_replicas or 0}/{statefulset.spec.replicas or 0}",
            'age': statefulset.metadata.creation_timestamp
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
            'age': service.metadata.creation_timestamp
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
            'age': ingress.metadata.creation_timestamp
        })

    return namespace_dict


def update_kubernetes_cache():
    global kubernetes_data_cache
    global kubernetes_cache_timestamp

    while True:
        kubernetes_json = fetch_kubernetes_data()
        if kubernetes_json:
            kubernetes_data_cache = kubernetes_json
            kubernetes_cache_timestamp = time.time()
            app.logger.debug(f"\nkubernetes_data_cache : {kubernetes_data_cache}\n")
            app.logger.info("Kubernetes data parsed and cached successfully.")
        time.sleep(60)  # Update every minute


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Start background thread for cache updates
    thread = threading.Thread(target=update_images_cache, daemon=True)
    thread.start()
    # Start thread for updating Kubernetes cache
    thread = threading.Thread(target=update_kubernetes_cache, daemon=True)
    thread.start()
    app.run()
