# Terraform Files for EKS Deployment

## Overview

This directory contains Terraform configurations for deploying an EKS (Elastic Kubernetes Service) cluster on AWS. The setup includes the creation of a VPC, subnets, a routing table, an internet gateway, and the EKS cluster itself. Additionally, it sets up an Application Load Balancer (ALB) and configures the AWS ALB controller on the EKS cluster, ACM certificate for HTTPS support, External DNS for Automatic AWS Route53 record creation, ArgoCD for GitOps, Redis, and an Application resource for Platform_App.

## Prerequisites

Before you begin, ensure you have the following installed:

- [Terraform](https://www.terraform.io/downloads.html)
- [AWS CLI](https://docs.aws.amazon.com/cli/latest/userguide/install-cliv2.html)
- Properly configured AWS credentials (`~/.aws/credentials`)
- [Route53](https://console.aws.amazon.com/route53/) Hosted Zone

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
### Create `terraform.tfvars` Files

Create a `terraform.tfvars` file in the tf_files directory with the following content:
```hcl
dockerhub_username     = "<dockerhub_username>"
dockerhub_access_token = "<dockerhub_access_token>"
hosted_zone_id         = "<route53_hosted_zone_id>"
```
Replace `<dockerhub_username>`, `<dockerhub_access_token>`, and `<route53_hosted_zone_id>` with your actual values.

### Apply the Configuration

Apply the Terraform configuration to create the EKS cluster and related resources:

```bash
terraform plan
terraform apply -auto-approve
```

## Terraform Files

The following Terraform files are included in this directory:

- **acm-certificate.tf**: Creates and validates ACM Certificate.
- **argocd.tf**: Configures ArgoCD for GitOps deployment.
   - **argocd.yaml**: YAML configuration for ArgoCD.
- **aws-load-balancer-controller.tf**: Sets up the AWS Load Balancer Controller.
- **eks.tf**: Configures the EKS cluster.
- **external-dns**: Sets up External-DNS
- **outputs.tf**: Specifies the outputs of the Terraform configuration.
- **platform_app.tf**: Configures the deployment of the platform application.
- **providers.tf**: Specifies the providers used in the Terraform configuration.
- **redis.tf**: Sets up Redis.
- **variables.tf**: Defines the variables used in the Terraform configuration.
- **vpc.tf**: Configures the VPC, subnets, routing table, and internet gateway.


## Outputs

After applying the configuration, Terraform will output the following:

- **KUBECONFIG**: Command to configure `kubeconfig` for connecting to the EKS cluster.
  ```bash
  aws eks --region ${var.aws_region} update-kubeconfig --name ${var.cluster_name}
  ```
- **ARGOCD**: Command to retrieve the initial admin password for ArgoCD.
  ```bash
  kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath={.data.password} | base64 -d
  ```
- **NETWORKING**: Information about the VPC and subnets.
  ```
  VPC ID                                  ${module.vpc.vpc_id}
  Public subnet 1                         ${module.vpc.public_subnets[0]}
  Public subnet 2                         ${module.vpc.public_subnets[1]}
  Public subnet 3                         ${module.vpc.public_subnets[2]}
  Private subnet 1                        ${module.vpc.private_subnets[0]}
  Private subnet 2                        ${module.vpc.private_subnets[1]}
  Private subnet 3                        ${module.vpc.private_subnets[2]}
  ```
- **ALB_External-DNS_ACM**: Information about the AWS LoadBalancer controller role arn, External DNS role arn, and ACM Certificate arn.
  ```
  AWS LoadBalancer controller arn         ${module.aws_load_balancer_controller_irsa_role.iam_role_arn}
  External DNS arn                        ${module.external_dns_irsa_role.iam_role_arn}
  ACM Certificate arn                     ${module.cert.arn}
  ```
- **EKS_Cluster**: Information about the EKS Cluster IAM role arn and its OpenID Connect provider arn.
  ```
  ${var.cluster_name} EKS Cluster Role    ${module.eks.cluster_iam_role_arn}
  OpenID Connect Provider                 ${module.eks.oidc_provider_arn}
  ```

These outputs can be used to access and manage the EKS cluster, VPC, and ArgoCD.

## Access Platform App in Browser
- Once the terraform module finished applying, access the application at `platform-app.<domain_name>` and Argocd at `argocd.<domain_name>`

<details>
<summary><h2>Configure /etc/hosts for Local Testing</h2></summary>

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

</details>

## Cleanup

To clean up and destroy the created resources, run the following command:

```bash
terraform destroy -auto-approve
```

## To-Do List

- [ ] Add Terratest integration
- [ ] Add Terragrunt support
- [x] Add Automatic HTTPS support
- [x] Integrate AWS route53
- [x] Integrate External DNS for automatic record creation
