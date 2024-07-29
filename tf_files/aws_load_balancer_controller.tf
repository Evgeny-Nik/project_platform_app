module "aws_load_balancer_controller_irsa_role" {
  # source  = "terraform-aws-modules/iam/aws//modules/iam-role-for-service-accounts-eks"
  # version = "~> 5.0"
  source    = "git::https://github.com/terraform-aws-modules/terraform-aws-iam.git//modules/iam-role-for-service-accounts-eks?ref=39e42e1f847afe5fd1c1c98c64871817e37e33ca"
  role_name = "aws-load-balancer-controller"

  attach_load_balancer_controller_policy = true

  oidc_providers = {
    eks = {
      provider_arn               = module.eks.oidc_provider_arn
      namespace_service_accounts = ["kube-system:aws-load-balancer-controller"]
    }
  }
  depends_on = [
    module.eks
  ]
}

resource "helm_release" "aws_load_balancer_controller" {
  name = "aws-load-balancer-controller"

  repository = "https://aws.github.io/eks-charts"
  chart      = "aws-load-balancer-controller"
  namespace  = "kube-system"
  version    = var.alb_ingress

  set {
    name  = "replicaCount"
    value = "2"
  }

  set {
    name  = "clusterName"
    value = var.cluster_name
  }

  set {
    name  = "serviceAccount.name"
    value = "aws-load-balancer-controller"
  }

  set {
    name  = "serviceAccount.annotations.eks\\.amazonaws\\.com/role-arn"
    value = module.aws_load_balancer_controller_irsa_role.iam_role_arn
  }

  depends_on = [
    module.eks,
    module.aws_load_balancer_controller_irsa_role
  ]
}

resource "time_sleep" "wait_for_load_balancer_controller" {
  depends_on = [helm_release.aws_load_balancer_controller]
  create_duration = var.wait_time
}