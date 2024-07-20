data "aws_availability_zones" "available" {
  state = "available"
}

locals {
  name   = "eks-${var.cluster_name}"
  region = var.aws_region

  vpc_cidr = var.vpc_cidr
  azs      = slice(data.aws_availability_zones.available.names, 0, var.availability_zones_count)

  tags = {
    ManagedBy = "terraform-aws-vpc"
  }
}

module "vpc" {
  # source  = "terraform-aws-modules/vpc/aws"
  # version = "~> 5.7"
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-vpc.git?ref=25322b6b6be69db6cca7f167d7b0e5327156a595"

  name = local.name
  cidr = local.vpc_cidr

  azs             = local.azs
  private_subnets = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k)]
  public_subnets  = [for k, v in local.azs : cidrsubnet(local.vpc_cidr, 8, k + 4)]

  public_subnet_tags = {
    "kubernetes.io/role/elb" = "1"
  }
  private_subnet_tags = {
    "kubernetes.io/role/internal-elb" = "1"
  }

  enable_dns_hostnames = true
  enable_dns_support   = true

  enable_nat_gateway     = true
  single_nat_gateway     = true
  one_nat_gateway_per_az = false

  tags = local.tags
}