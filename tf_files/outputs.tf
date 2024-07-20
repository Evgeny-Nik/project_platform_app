output "eks_connect" {
  value = "aws eks --region eu-north-1 update-kubeconfig --name ${module.eks.cluster_name}"
}

output "argocd_ingress_address" {
  value = data.kubernetes_ingress.argocd_ingress.status[0].load_balancer[0].ingress[0].hostname
}

output "argocd_initial_admin_secret" {
  value = "kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath={.data.password} | base64 -d"
}

output "platform_app_ingress_address" {
  value = data.kubernetes_ingress.platform_app_ingress.status[0].load_balancer[0].ingress[0].hostname
}