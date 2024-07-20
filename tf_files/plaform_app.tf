resource "kubernetes_namespace" "platform_app" {
  metadata {
    name = "platform-app"
  }
  depends_on = [
    module.eks
  ]
}

resource "kubectl_manifest" "argocd_application" {
  yaml_body = file("${path.module}/platform_app.yaml")

  depends_on = [
    time_sleep.wait_for_argocd
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
