#!/bin/bash

# Variables
NAMESPACE=$1
INGRESS_NAME=$2
CLUSTER_NAME=$3
AWS_REGION=$4

# Debugging: Print the received variables
echo "NAMESPACE: $NAMESPACE"
echo "INGRESS_NAME: $INGRESS_NAME"
echo "CLUSTER_NAME: $CLUSTER_NAME"
echo "AWS_REGION: $AWS_REGION"

# Apply the new EKS kubeconfig once
if [ ! -f "/tmp/kubeconfig_applied" ]; then
  aws eks update-kubeconfig --name "$CLUSTER_NAME" --region "$AWS_REGION"
  if [ $? -ne 0 ]; then
    echo "Failed to apply EKS kubeconfig"
    exit 1
  fi
  touch /tmp/kubeconfig_applied
fi

# Check ingress status
echo "Checking ingress status for $INGRESS_NAME in namespace $NAMESPACE..."
while true; do
  STATUS=$(kubectl get ingress $INGRESS_NAME -n $NAMESPACE -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>&1)

  if [ $? -ne 0 ]; then
    echo "Error fetching ingress status: $STATUS"
  elif [ -n "$STATUS" ]; then
    echo "Ingress is ready: $STATUS"
    # If namespace is argocd, fetch the admin secret
    if [ "$NAMESPACE" == "argocd" ]; then
      echo "Fetching ArgoCD admin password..."
      ADMIN_PASSWORD=$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath={.data.password} | base64 -d)
      if [ $? -eq 0 ]; then
        echo "ArgoCD admin password: $ADMIN_PASSWORD"
      else
        echo "Failed to fetch ArgoCD admin password"
      fi
    fi
    exit 0
  else
    echo "Ingress hostname not yet available. Waiting..."
    sleep 10
  fi
done
