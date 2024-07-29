provider "aws" {
  region = var.aws_region
  alias  = "certificates"
}

provider "aws" {
  region = var.aws_region
  alias  = "dns"
}

module "cert" {
  source = "github.com/azavea/terraform-aws-acm-certificate"

  providers = {
    aws.acm_account     = aws.certificates
    aws.route53_account = aws.dns
  }

  domain_name                       = var.domain
  subject_alternative_names         = ["*.${var.domain}"]
  hosted_zone_id                    = var.hosted_zone_id
  validation_record_ttl             = "60"
  allow_validation_record_overwrite = true
}

# Used to deploy platform-app with https
resource "kubernetes_secret" "cert_arn" {
  metadata {
    name      = "cert-arn-secret"
    namespace = "argocd"  # Ensure this namespace is where ArgoCD can access
  }

  data = {
    CERTIFICATE_ARN = module.cert.arn
  }

  type = "Opaque"
  depends_on = [
    kubernetes_namespace.argocd
  ]
}

resource "time_sleep" "wait_for_cert_arn_secret" {
  depends_on = [
    kubernetes_secret.cert_arn
  ]
  create_duration = "10s"  # Adjust as needed
}
