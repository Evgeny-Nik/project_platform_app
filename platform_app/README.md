# AWS Lambda Web App

This is a Python Flask application designed to manage various environments, deploy Helm charts, and monitor Kubernetes resources. The application is tailored for developers who need a streamlined platform for deploying and managing applications in Kubernetes environments.

## Table of Contents

- [Usage](#usage)
- [Endpoints](#endpoints)
- [Setup](#setup)
- [Docker](#docker)
- [Kubernetes](#kubernetes)
- [To Do List](#to-do-list)

### Usage

- **Home Page**: The home page provides access to different functionalities, including managing Kubernetes resources and selecting Docker images and tags.
- **Manage Kubernetes Resources**: Create or delete namespaces and deploy or remove Helm charts.
- **Monitor Status**: Check the status of your Kubernetes resources.
- **Docker Integration**: View and select Docker images and tags for deployment.

### Endpoints

- **`GET /`**: The home page, which displays the list of namespaces, Docker images, and Kubernetes data. It also shows flashed messages and renders the main user interface.
  
- **`POST /delete`**: Deletes the selected Kubernetes namespace and updates the application state. If the namespace is successfully deleted, it is removed from the list and session and the cache is updated. Flashes a message indicating the result.

- **`POST /deploy`**: Deploys an application using Helm in the selected namespace with the specified Docker image repository and tag. Updates the Kubernetes data cache and session. It also makes an internal `POST` request to `/describe` for further processing.

- **`POST /describe`**: Fetches and displays Kubernetes data for the selected namespace. Updates session data and flashes a message indicating the view status. Redirects to the home page with updated data.

- **`GET /logout`**: Clears the user session and redirects to the home page with a logout confirmation message, currently used for debugging.

## Setup

1. Clone the repository:
   ```sh
   git clone https://github.com/Evgeny-Nik/project_platform_app.git
   cd project_platform_app/platform_app
   ```

2. Create a virtual environment:
   ```sh
   python3 -m venv venv
   source venv/bin/activate
   ```

3. Install the dependencies:
   ```sh
   pip install -r requirements.txt
   ```

4. Set the necessary environment variables,
These variables can be set in your environment or a `.env` file:
   ```sh
   DOCKER_HUB_USERNAME='<username>'
   DOCKER_HUB_ACCESS_TOKEN='<token>'
   SESSION_KEY='<session_secret_key>'
   HELM_CHART='<path_or_url_to_helm_chart>'
   KUBECONFIG='<path_to_.kube/config>'
   REDIS_HOST_URL='<your_redis_host_url>'
   REDIS_HOST_PORT='<port_num_your_redis_is_exposed_at>'
   REDIS_HOST_PASSWORD='<your_redis_password>'
   ```

5. Run the Flask app:
   ```sh
   python3 app.py
   ```
   or
   ```sh
   gunicorn -c gunicorn.conf.py wsgi:app
   ```

6. Open your web browser and navigate to: `http://localhost:5000/` or if ran using gunicorn command:`http://localhost:8000/`.

## Docker

To run the app using Docker:

1. Build the Docker image:
   ```sh
   docker build -t ${DOCKERHUB_USERNAME}/platform_app:latest .
   ```

2. Run the Docker container:
   ```sh
     docker run -d -v </path/to/.kube/config>:</path/to/.kube/config> \
         -p 8000:8000 \
         --env-file .env \
         ${DOCKERHUB_USERNAME}/platform_app:latest
   ```

3. Open your web browser and navigate to `http://localhost:8000/`.

## Kubernetes

To run the app within Kubernetes:

- [Manually](../charts/README.md)

- [Automatically using Terraform](../tf_files/README.md)

## To Do List

- [ ] Add web application tests
- [ ] Integrate HTTPS support for the platform app via Let's Encrypt.
- [ ] Set up history, logging and monitoring functions (MongoDB, Elastik Stack, Prometheu/Loki + Grafana)
- [ ] Fully integrate flask sessions: add user login/logout, support for multiple pods/gunicorn workers.
