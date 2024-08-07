# Platform Flask App Integration with EKS

## Project overview

This project demonstrates a CI/CD and GitOps deployment of a Flask application using GitHub Actions, Terraform, and ArgoCD.

## Application
The application is a Flask web platform that facilitates the creation, display, and destruction of various Kubernetes environments using a predefined Helm chart.

## Workflow overview

The project includes the following workflow:
   1. CI/CD for Flask App: Manages the continuous integration and deployment cycle of the platform application.

### 1. CI/CD for Flask App

This workflow builds and deploys a Flask application that communicates with the Kubernetes API. \
Key steps include:

   - **Read and Increment Version**: Reads the `version.txt` file for current version, and increments patch number by 1.
   - **Build the Docker image**: Builds a Docker image and tags it with the current version and latest
   - **Docker Login**: Logs into Docker Hub using provided credentials.
   - **push to Docker Hub**: Pushes the tagged Docker images to Docker Hub.
   - **Update Manifest and Version Files**: Updates the manifest and version file with the new version number for ArgoCD.

#### Trigger

This workflow is triggered on a push event to the `main` branch in the following paths:
```yaml
on:
  push:
    branches: 
      - "main"
    paths:       
      - 'platform_app/**'
      - '.github/workflows/platform_app_ci.yaml'
      - '!**/README.md'
```

<details>
<summary><h2>Reproducing the Project</h2></summary>

## Flask Application:

### Overview

- **platform_app**
  - `app.py`: A simple Flask web application that manages multiple endpoints and communicates with Kubernetes API.

## Web_App Dockerfile

- **Base Image**: Uses `python:alpine3.19` for a lightweight Python environment.
- **Install Helm**: Uses `apk` to install curl, bash, and openssl to install Helm 3, then removes unnecessary packages while keeping Helm operational.
- **Work Directory**: Sets the working directory to `/app`.
- **Install Dependencies**: Copies `requirements.txt` and installs Python dependencies without cache (including the Flask[async] addon).
- **Copy Source Code**: Copies the source code to the working directory.
- **Create Temp Session Store**: Creates a directory to store the temporary session store for use when running in a container.
- **Run Application**: Uses Gunicorn to run the Flask application with pre-configured `gunicorn.conf.py` file.

## Setup

1. **Clone the Repository**:
    ```bash
    git clone https://github.com/Evgeny-Nik/project_platform_app.git
    cd project_platform_app
    ```
2. **Setup the .env file**:
    ```bash
    touch platform_app/.env
    ```

#### Environment Variables Example (.env-example)

The `.env` file in your `platform_app` directory should have the following example values:

    ```
    DOCKER_HUB_USERNAME="<username>"
    DOCKER_HUB_ACCESS_TOKEN="<token>"
    SESSION_KEY="<session_secret_key>"
    HELM_CHART="<path_or_url_to_helm_chart>"
    KUBECONFIG="<path_to_.kube/config>"
    REDIS_HOST_URL='<your_redis_host_url>'
    REDIS_HOST_PORT='<port_num_your_redis_is_exposed_at>'
    REDIS_HOST_PASSWORD='<your_redis_password>'
    ```
    
*KUBECONFIG env var is only required when the app is deployed out of kubernetes.

3. **Trigger the workflow to build the app**:
   - Push changes to the `main` branch.
   - See triggers [here](#trigger).

4. **Deploy the app to the environment of your choosing**:
   - To manually run the platform app locally:
     ```bash
     cd platform_app
     python -m venv venv
     source venv/bin/activate 
     pip install -r requirements.txt
     python3 platform_app/app.py
     ```
     The Platform App will then be accessible in `http://localhost:5000`

   - To manually run the platform app in a container:
     ```bash
     cd platform_app
     docker build -t ${DOCKERHUB_USERNAME}/platform_app:latest .
     docker run -d -v </path/to/.kube/config>:</path/to/.kube/config> -p 8000:8000 --env-file .env ${DOCKERHUB_USERNAME}/platform_app:latest
     ```
     The Platform App will then be accessible in `http://localhost:8000`

   - To manually run the platform in a Kubernetes Cluster:
     ```bash
     cd tf-Files
     terraform init \
       -backend-config="bucket=<your_s3_bucket's_name>" \
       -backend-config="key=<your_s3_statefiles's_key>"
     terraform validate
     terraform plan
     terraform apply -auto-approve
     ```
     For further Setup steps go to [tf_files README](tf_files/README.md)

## Slack

```yaml
    - name: Send Slack Notification
      uses: 8398a7/action-slack@v3
      with:
        status: ${{ job.status }}
        fields: repo,message,commit,author,action,eventName,ref,workflow,job,took
      env:
        SLACK_WEBHOOK_URL: ${{ secrets.SLACK_WEBHOOK_URL }} # required
      if: always() # Pick up events even if the job fails or is canceled.
```

To incorporate Slack notifications for your GitHub Actions pipeline do the following:

1. **Set Up Slack Webhook**:
   - Create a [Slack Application](https://api.slack.com/apps)
   - Create an Incoming Webhook in your Slack workspace and obtain the Webhook URL.
   - Store the Webhook URL as a secret in your GitHub repository settings:
     - Go to your repository on GitHub.
     - Click on `Settings` > `Secrets and variables` > `Actions`.
     - Click on `New repository secret` and add `SLACK_WEBHOOK_URL` with the Webhook URL as the value.

3. **Customize Notification Fields**:
   - Customize the fields parameter in the `with` section to include the details you want in the Slack message.

</details>

### GitHub Actions Plugins Used

- **actions/checkout@v4**: Checks out the repository to the runner.
- **docker/login-action@v3.1.0**: Logs into Docker Hub.
- **8398a7/action-slack@v3**: Sends a Slack message.

## To-Do List

- [ ] Fully integrate flask sessions: add user login/logout, support for multiple pods/gunicorn workers. 
- [ ] Create tests.
- [x] Integrate HTTPS support for the platform app via Let's Encrypt.

## Links
- [platform_app README](platform_app/README.md)
- [tf_files README](tf_files/README.md)
- [charts](charts/README.md)
