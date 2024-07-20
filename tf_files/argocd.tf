resource "kubernetes_namespace" "argocd" {
  metadata {
    name = "argocd"
  }
  depends_on = [
    module.eks
  ]
}

resource "helm_release" "argocd" {
  name = "argocd"

  repository = "https://argoproj.github.io/argo-helm"
  chart      = "argo-cd"
  namespace  = kubernetes_namespace.argocd.metadata[0].name
  version    = "6.7.18"

  values = [
    "${file("${path.module}/argocd.yaml")}"
  ]

  depends_on = [
    module.eks,
    helm_release.aws_load_balancer_controller,
    kubernetes_namespace.argocd
  ]
}

resource "time_sleep" "wait_for_argocd" {
  depends_on      = [helm_release.argocd]
  create_duration = "10s"
}

data "kubernetes_ingress_v1" "argocd" {
  metadata {
    name      = "argocd-server"
    namespace = "argocd"
  }
  depends_on = [
    time_sleep.wait_for_argocd
  ]
}

data "kubernetes_ingress" "argocd_ingress" {
  metadata {
    name      = "argocd-server"
    namespace = helm_release.argocd.namespace
  }
  depends_on = [
    time_sleep.wait_for_argocd
  ]
}

##  this data can be used to set password directly to outputs
# data "kubernetes_secret" "argocd_password" {
#   metadata {
#     name      = "argocd-initial-admin-secret"
#     namespace = helm_release.argocd.namespace
#   }
#   depends_on = [
#     time_sleep.wait_for_argocd
#   ]
# }
