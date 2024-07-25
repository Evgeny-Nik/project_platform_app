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

    # Perform a curl to the STATUS and capture verbose output
    CURL_OUTPUT=$(curl -v $STATUS 2>&1)
    echo "Curl output for debugging:"
    echo "$CURL_OUTPUT"

    # Extract IP address using grep and awk
    IP_ADDRESS=$(echo "$CURL_OUTPUT" | grep -oP 'Connected to [^ ]+ \(\K[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+')

    if [[ $IP_ADDRESS =~ ^[0-9]+\.[0-9]+\.[0-9]+\.[0-9]+$ ]]; then
      echo "Extracted IP address from curl: $IP_ADDRESS"

      # Edit /etc/hosts file
      TEMP_HOSTS=$(mktemp)
      sudo cp /etc/hosts $TEMP_HOSTS

      # Update or add entries for argocd.example.com and platform-app.example.com
      if grep -q "argocd.example.com" $TEMP_HOSTS; then
        sudo sed -i "s/.*argocd.example.com/$IP_ADDRESS argocd.example.com/" $TEMP_HOSTS
        echo "Updated entry for argocd.example.com"
      else
        echo "$IP_ADDRESS argocd.example.com" | sudo tee -a $TEMP_HOSTS > /dev/null
        echo "Added entry for argocd.example.com"
      fi

      if grep -q "platform-app.example.com" $TEMP_HOSTS; then
        sudo sed -i "s/.*platform-app.example.com/$IP_ADDRESS platform-app.example.com/" $TEMP_HOSTS
        echo "Updated entry for platform-app.example.com"
      else
        echo "$IP_ADDRESS platform-app.example.com" | sudo tee -a $TEMP_HOSTS > /dev/null
        echo "Added entry for platform-app.example.com"
      fi

      sudo cp $TEMP_HOSTS /etc/hosts
      sudo rm $TEMP_HOSTS
    else
      echo "Failed to extract a valid IP address from curl output"
    fi

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
