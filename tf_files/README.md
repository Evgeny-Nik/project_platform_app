# Terraform Files for EKS Deployment

## Overview

This directory contains Terraform configurations for deploying an EKS (Elastic Kubernetes Service) cluster on AWS. The setup includes the creation of a VPC, subnets, a routing table, an internet gateway, and the EKS cluster itself. Additionally, it sets up an Application Load Balancer (ALB) and configures the AWS ALB controller on the EKS cluster, ArgoCD for GitOps, Redis, and an Application resource for Platform_App.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Terraform](https://www.terraform.io/downloads.html)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- Properly configured AWS credentials (`~/.aws/credentials`)

## Setup

### Clone the Repository

Start by cloning the repository:

```bash
git clone https://github.com/Evgeny-Nik/project_platform_app.git
cd project_platform_app/tf_files
```

### Initialize Terraform and Configure Backend

Initialize and configure the Terraform backend by providing your S3 bucket name and key for storing the Terraform state files:

```bash
terraform init \
  -backend-config="bucket=<your_s3_bucket_name>" \
  -backend-config="key=<your_s3_statefiles_key>"
```

### Apply the Configuration

Apply the Terraform configuration to create the EKS cluster and related resources:

```bash
terraform plan
terraform apply -auto-approve
```

## Terraform Files

The following Terraform files are included in this directory:

- **argocd.tf**: Configures ArgoCD for GitOps deployment.
   - **argocd.yaml**: YAML configuration for ArgoCD.
- **aws-load-balancer-controller.tf**: Sets up the AWS Load Balancer Controller.
- **eks.tf**: Configures the EKS cluster.
- **outputs.tf**: Specifies the outputs of the Terraform configuration.
- **platform_app.tf**: Configures the deployment of the platform application.
   - **platform_app.yaml**: YAML configuration for the platform application.
- **providers.tf**: Specifies the providers used in the Terraform configuration.
- **redis.tf**: Sets up Redis.
- **variables.tf**: Defines the variables used in the Terraform configuration.
- **vpc.tf**: Configures the VPC, subnets, routing table, and internet gateway.

## Outputs

After applying the configuration, Terraform will output the following:

- **eks_connect**: Command to configure `kubeconfig` for connecting to the EKS cluster.
  ```bash
  aws eks --region eu-north-1 update-kubeconfig --name <your-cluster-name>
  ```
- **argocd_initial_admin_secret**: Command to retrieve the initial admin password for ArgoCD.
  ```bash
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath={.data.password} | base64 -d
  ```
- **argocd_ingress_address**: The ingress address for accessing ArgoCD.
- **platform_app_ingress_address**: The ingress address for accessing the platform application.

These outputs can be used to access and manage the EKS cluster, ArgoCD, and the platform application.

## Configure /etc/hosts for Local Testing

To test the application locally, you need to configure the `/etc/hosts` file with the following entries:

1. Use `curl` to get the IP address of the ingress:

   ```bash
   curl -v <argocd_ingress_address>
   curl -v <platform_app_ingress_address>
   # if any apps were deployed:
   # curl -v <deployed_app_ingress_address>
   ```

   Replace `<argocd_ingress_address>` and `<platform_app_ingress_address>` with the actual addresses provided by the Terraform outputs.

2. Open the `/etc/hosts` file in your favorite text editor with root privileges:

   ```bash
   sudo nano /etc/hosts
   ```

3. Add the following entries to map the local addresses to the respective domains:

   ```plaintext
   <argocd_ingress_ip> argocd.example.com
   <platform_app_ingress_ip> platform-app.example.com
   <deployed_app_ingress_ip> <namespace>.example.com
   ```

   Replace `<argocd_ingress_ip>`, `<platform_app_ingress_ip>`, and `<deployed_app_ingress_ip>` with the IP addresses obtained from the `curl` command. Replace `<namespace>` with your specific namespace.

4. Save the changes and exit the text editor.

This configuration allows you to access ArgoCD and the Platform App locally using the specified domain names.

## Cleanup

To clean up and destroy the created resources, run the following command:

```bash
terraform destroy -auto-approve
```

## To-Do List

- [ ] Add Terratest integration
- [ ] Add Terragrunt support
