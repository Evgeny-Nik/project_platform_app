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
        # for minikube add -v </path/to/.minikube>:</path/to/.minikube_in_container>
         -p 8000:8000 \
         --env-file .env \
         ${DOCKERHUB_USERNAME}/platform_app:latest
   ```

3. Open your web browser and navigate to `http://localhost:8000/`.

## Kubernetes

<details>
<summary><h2>Minikube</h2></summary>
1. **Start Minikube**

   ```sh
   minikube start
   ```

2. **Deploy Redis**

  - Install a helm chart for Redis:

   ```sh
   helm repo add bitnami https://charts.bitnami.com/bitnami
   helm repo update
   helm install redis bitnami/redis
   ```

  - Copy secret to platform-app namespace

   ```sh
   kubectl create secret generic redis-password --namespace platform-app \
     --from-literal=REDIS_HOST_PASSWORD="$(kubectl get secret redis -n redis -o \
     jsonpath='{.data.redis-password}' | base64 -d)"
   ```

3. **Install Argo CD**

  - Install Argo CD using the following commands:

   ```sh
   kubectl create namespace argocd
   kubectl apply -n argocd -f https://raw.githubusercontent.com/argoproj/argo-cd/stable/manifests/install.yaml
   ```

  - Expose the Argo CD server:

   ```sh
   kubectl port-forward svc/argocd-server -n argocd 8080:443
   ```

  - Login to the Argo CD UI:

     Open your browser and go to `http://localhost:8080` \
     The default username is `admin`. Obtain the initial password:

   ```sh
   kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d
   ```

4. **Deploy `platform-app` with Argo CD**

  - Create dockerhub-credentials secret

   ```sh
   kubectl create secret generic docker-hub-credentials \
     --namespace platform-app \
     --from-literal=DOCKER_HUB_USERNAME='<your_dockerhub_username>' \
     --from-literal=DOCKER_HUB_ACCESS_TOKEN='<your__dockerhub_access_token>'
   ```
  - Configure Argo CD

    1. Create a Git Repository with Kubernetes Manifests: Ensure you have a Git repository containing the manifests for deploying `platform-app`.

    2. Create an Argo CD Application:
   ```sh
   kubectl apply -f <path_to_application_manifest.yaml>
   ```

5. **Access the Application**

   Expose your application using a LoadBalancer service type or port-forwarding for testing:

   ```sh
   kubectl port-forward svc/platform-app-service 8000:8000
   ```

   Visit `http://localhost:8000` in your browser to access `platform-app`.
</details>

<details>
<summary><h2>Using Terraform</h2></summary>

- [Automatically using Terraform](../tf_files/README.md)
</details>

## To Do List

- [ ] Add web application tests
- [x] Integrate HTTPS support for the platform app via Let's Encrypt. (executed on k8s via aws acm and external-dns)
- [ ] Set up history, logging and monitoring functions (MongoDB, Elastik Stack, Prometheu/Loki + Grafana)
- [ ] Fully integrate flask sessions: add user login/logout, support for multiple pods/gunicorn workers.
