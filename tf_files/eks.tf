module "eks" {
  # source  = "terraform-aws-modules/eks/aws"
  # version = "~> 20.0"
  source = "git::https://github.com/terraform-aws-modules/terraform-aws-eks.git?ref=afadb14e44d1cdbd852dbae815be377c4034e82a"

  cluster_name    = var.cluster_name
  cluster_version = "1.29"

  cluster_endpoint_public_access = true

  cluster_addons = {
    coredns = {
      most_recent = true
    }
    kube-proxy = {
      most_recent = true
    }
    vpc-cni = {
      most_recent = true
    }
    aws-ebs-csi-driver = {
      most_recent = true
    }
  }

  vpc_id     = module.vpc.vpc_id
  subnet_ids = module.vpc.private_subnets
  # control_plane_subnet_ids = module.vpc.public_subnets
  enable_irsa = true

  # Disable encryption
  create_kms_key                   = false
  cluster_encryption_config        = {}
  attach_cluster_encryption_policy = false
  ### TEST ONLY ###

  authentication_mode = "API_AND_CONFIG_MAP"

  # EKS Managed Node Group(s)
  eks_managed_node_group_defaults = {
    instance_types = ["t3.medium"]
    disk_size      = 20
    capacity_type  = "ON_DEMAND"
  }

  eks_managed_node_groups = {
    eks_cluster = {
      min_size     = 1
      max_size     = 10
      desired_size = 2
      iam_role_additional_policies = {
        AmazonEBSCSIDriverPolicy = "arn:aws:iam::aws:policy/service-role/AmazonEBSCSIDriverPolicy"
      }
    }
  }
  # Cluster access entry
  # To add the current caller identity as an administrator
  enable_cluster_creator_admin_permissions = true

  tags = {
    Environment = "dev"
    Terraform   = "true"
  }

  depends_on = [
    module.vpc
  ]
}