# Helm Charts for Platform App Deployment

## Overview

This directory contains Helm charts for deploying the Platform App and its dependencies on a Kubernetes cluster. \
The charts included are:

- `platform_app`: Main application chart with comprehensive configurations.
- `deploying_chart`: Secondary chart used by `platform_app` to deploy a generic application.

## Prerequisites

Ensure the following tools are installed and configured before deployment:

- [Helm](https://helm.sh/docs/intro/install/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- A running Kubernetes cluster
- Properly configured Kubernetes context (`~/.kube/config`)

## Helm Charts

### platform_app

This chart deploys the Platform App along with its required configurations.

**Values.yaml**: Defines all values used in the chart

**Templates**:

- **deployment.yaml**: Defines the deployment configuration.
- **service.yaml**: Configures the service.
- **ingress.yaml**: Sets up the ingress.
- **service-account.yaml**: Creates a service account.
- **cluster-role.yaml**: Defines the cluster role.
- **cluster-role-binding.yaml**: Creates a cluster role binding.

### deploying_chart

This chart deploys a generic application with customizable values.

**Values.yaml**: Defines all values used in the chart

**Templates**:

- **deployment.yaml**: Defines the deployment configuration.
- **service.yaml**: Configures the service.
- **ingress.yaml**: Sets up the ingress.

## Deployment Instructions

### Add Helm Repositories

Start by cloning the repository:

```bash
git clone https://github.com/Evgeny-Nik/project_platform_app.git
cd project_platform_app/charts
```

### Deploy Platform App

Deploy the Platform App:

```bash
helm install platform-app ./platform_app -f platform_app/values.yaml
```

### Deploy Generic App

Deploy the generic app:
- **Manually**:
   ```bash
   helm install my-app ./deploying_chart -f deploying_chart/values.yaml
   ```

- **Using `platform_app`**: Select an image, tag and namespace to deploy the app to.

## Setting Up Ingress

After deployment, get the ingress dns using the following commands:
  ```bash
  kubectl get ingress -n platform-app
  kubectl get ingress -n <generic_app_namespace>
  ```

### Configure /etc/hosts for Local Testing

To access the deployed applications locally, configure your `/etc/hosts` file:

1. Use `curl` to get the IP address of the ingress:

   ```bash
   curl -v <argocd_ingress_address>
   curl -v <platform_app_ingress_address>
   curl -v <generic_app_ingress_address>
   ```

2. Open `/etc/hosts` with root privileges:

   ```bash
   sudo nano /etc/hosts
   ```

3. Add the entries:

   ```plaintext
   <argocd_ingress_ip> argocd.example.com
   <platform_app_ingress_ip> platform-app.example.com
   <generic_app_ingress_ip> generic-app.example.com
   ```

4. Save and exit.

This setup allows local access using specified domain names.

## Cleanup

To remove all deployed resources, use the following commands:

```bash
helm uninstall platform-app
helm uninstall my-app
```