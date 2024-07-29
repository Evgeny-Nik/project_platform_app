resource "kubernetes_namespace" "platform_app" {
  metadata {
    name = "platform-app"
  }
  depends_on = [
    module.eks
  ]
}

resource "kubectl_manifest" "platform_app_manifest" {
  yaml_body = <<YAML
apiVersion: argoproj.io/v1alpha1
kind: Application
metadata:
  name: platform-app
  namespace: argocd
  labels:
    test: "true"
spec:
  project: default
  source:
    repoURL: https://github.com/Evgeny-Nik/project_platform_app
    path: charts/platform_app
    targetRevision: HEAD
    helm:
      parameters:
        - name: ingress.alb.certificateArn
          value: ${module.cert.arn}
  destination:
    server: https://kubernetes.default.svc
    namespace: platform-app
  syncPolicy:
    automated:
      prune: true
      selfHeal: true
YAML

  depends_on = [
    time_sleep.wait_for_argocd,
    kubernetes_namespace.platform_app
  ]
}

resource "kubernetes_secret" "redis_password" {
  metadata {
    name      = "redis-password"
    namespace = kubernetes_namespace.platform_app.metadata[0].name
  }

  data = {
    REDIS_HOST_PASSWORD = data.kubernetes_secret.redis_password.data["redis-password"]
  }

  type = "Opaque"

  depends_on = [
    data.kubernetes_secret.redis_password,
    kubernetes_namespace.platform_app
  ]
}

resource "kubernetes_secret" "dockerhub_credentials" {
  metadata {
    name      = "docker-hub-credentials"
    namespace = kubernetes_namespace.platform_app.metadata[0].name
  }

  data = {
    DOCKER_HUB_USERNAME     = var.dockerhub_username
    DOCKER_HUB_ACCESS_TOKEN = var.dockerhub_access_token
  }

  type = "Opaque"

  depends_on = [
    kubernetes_namespace.platform_app
  ]
}

resource "time_sleep" "wait_for_platform_app" {
  depends_on      = [kubectl_manifest.platform_app_manifest]
  create_duration = var.wait_time
}
