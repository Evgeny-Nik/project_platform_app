output "eks" {
  value = <<EOF
###################################### KUBECONFIG ###########################################

        aws eks --region ${var.aws_region} update-kubeconfig --name ${var.cluster_name}

###################################### ARGOCD ###############################################

        kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath={.data.password} | base64 -d ; echo

###################################### N E T W O R K I N G ##################################
        VPC ID                                  ${module.vpc.vpc_id}
        Public subnet 1                         ${module.vpc.public_subnets[0]}
        Public subnet 2                         ${module.vpc.public_subnets[1]}
        Public subnet 3                         ${module.vpc.public_subnets[2]}
        Private subnet 1                        ${module.vpc.private_subnets[0]}
        Private subnet 2                        ${module.vpc.private_subnets[1]}
        Private subnet 3                        ${module.vpc.private_subnets[2]}
###################################### ALB External-DNS ACM #################################
        AWS LoadBalancer controller arn         ${module.aws_load_balancer_controller_irsa_role.iam_role_arn}
        External DNS arn                        ${module.external_dns_irsa_role.iam_role_arn}
        ACM Certificate arn                     ${module.cert.arn}
###################################### EKS Cluster ##########################################

        ${var.cluster_name} EKS Cluster Role             ${module.eks.cluster_iam_role_arn}
        OpenID Connect Provider                 ${module.eks.oidc_provider_arn}
    EOF
}