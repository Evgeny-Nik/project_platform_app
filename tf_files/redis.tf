resource "kubernetes_namespace" "redis" {
  metadata {
    name = "redis"
  }
  depends_on = [
    module.eks
  ]
}

resource "helm_release" "redis" {
  name = "redis"

  repository = "https://charts.bitnami.com/bitnami"
  chart      = "redis"
  namespace  = kubernetes_namespace.redis.metadata[0].name
  version    = "16.12.0"

  depends_on = [
    module.eks,
    kubernetes_namespace.redis
  ]
}

resource "time_sleep" "wait_for_redis" {
  depends_on      = [helm_release.redis]
  create_duration = var.wait_time
}

data "kubernetes_service" "redis" {
  metadata {
    name      = "redis-master"
    namespace = helm_release.redis.namespace
  }

  depends_on = [
    time_sleep.wait_for_redis
  ]
}

data "kubernetes_secret" "redis_password" {
  metadata {
    name      = helm_release.redis.name
    namespace = helm_release.redis.namespace
  }

  depends_on = [
    time_sleep.wait_for_redis
  ]
}