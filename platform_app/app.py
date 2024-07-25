from flask import Flask, render_template, request, jsonify, url_for, redirect, flash, get_flashed_messages, session
from flask_session import Session
from app_config import logger, SESSION_KEY, SESSION_CONFIG, OS_ENV
import os
import threading
import time
import requests
from cache_config import get_kubernetes_data_cache, get_kubernetes_ns_list, get_docker_images_cache
from docker_funcs import update_docker_images_cache_loop
from kubernetes_funcs import update_kubernetes_cache, update_k8s_namespace_list, fetch_kubernetes_data
from delete_funcs import delete_application_main
from deploy_funcs import deploy_application_main


app = Flask(__name__)

# Load session configuration
app.config.update(SESSION_CONFIG)

app.secret_key = SESSION_KEY  # Set a secret key for session management

Session(app)


@app.route('/api/docker-images', methods=['GET'])
def docker_images():
    return jsonify(get_docker_images_cache())


@app.route('/api/docker-images/<string:repo_name>/tags', methods=['GET'])
def docker_image_tags(repo_name):
    docker_images_cache = get_docker_images_cache()
    tags = docker_images_cache.get(repo_name, [])
    return jsonify({repo_name: tags})


@app.route('/delete', methods=['POST'])
def delete():
    selected_namespace = request.form.get('namespace', '')  # Get selected namespace from form submission
    # Check if there are namespaces available
    if not get_kubernetes_ns_list():
        flash("Error, no Namespace data")
        return redirect('/')

    if selected_namespace in get_kubernetes_ns_list():
        result = delete_application_main(selected_namespace)
        if not result:
            session.pop('selected_namespace', None)
            session.pop('parsed_data', None)
        flash(result or f"Deletion of namespace '{selected_namespace}' completed successfully.")
    else:
        flash("Namespace not found or not selected.")

    return redirect('/')


@app.route('/deploy', methods=['POST'])
def deploy():
    chart_path = os.getenv("HELM_CHART", "/path/to/helm/chart")
    image_repository = request.form['image_repository']
    image_tag = request.form['image_tag']
    namespace = request.form['deploy_namespace']

    result = deploy_application_main(namespace, image_repository, image_tag, chart_path)
    message = result if result else f"Deployment of {image_repository}:{image_tag} in namespace {namespace} completed."

    if result:
        flash(message)
        return redirect(url_for('index'))

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

    logger.debug(f"\ndeploy_cache: {get_kubernetes_data_cache}\n")  # Log the updated cache for debugging

    flash(message)

    # Make an internal POST request to /describe with namespace data
    if "KUBERNETES_SERVICE_HOST" in OS_ENV:
        describe_url = 'http://platform-app-service.platform-app.svc.cluster.local/describe'
    else:
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
    selected_namespace = request.form.get('namespace', '')  # Get selected namespace from form submission
    message = request.form.get('message', '')

    # Only fetch Kubernetes data if a namespace is selected
    if selected_namespace:
        parsed_data = get_kubernetes_data_cache().get(selected_namespace, {})
        # Store data in session to be used on the index page
        session['selected_namespace'] = selected_namespace
        session['parsed_data'] = parsed_data
        if not parsed_data:
            message += ", in /describe No Kubernetes data available."
        logger.debug(f"\nparsed data: {parsed_data}")
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
    # Retrieve data from session
    selected_namespace = session.pop('selected_namespace', None)
    parsed_data = session.pop('parsed_data', None)
    if selected_namespace:
        data = parsed_data
        namespace = selected_namespace

    # Check for flashed messages
    messages = [msg for msg in get_flashed_messages()]

    # Render the page with Kubernetes data
    return render_template('index.html',
                           namespaces=get_kubernetes_ns_list(),
                           sel_namespace=namespace,
                           kubernetes_data=data,
                           images_cache=get_docker_images_cache(),
                           kubernetes_data_cache=get_kubernetes_data_cache(),
                           messages=messages)


@app.route('/logout')
def logout():
    session.clear()
    flash('You have been logged out.')
    return redirect(url_for('index'))


if __name__ == '__main__':
    # Start background thread for cache updates
    thread_docker = threading.Thread(target=update_docker_images_cache_loop, daemon=True)
    thread_docker.start()
    # Start background thread for namespace updates
    thread_namespaces = threading.Thread(target=update_k8s_namespace_list, daemon=True)
    thread_namespaces.start()
    # Start thread for updating Kubernetes cache
    thread_k8s_resources = threading.Thread(target=update_kubernetes_cache, daemon=True)
    thread_k8s_resources.start()
    app.run()
