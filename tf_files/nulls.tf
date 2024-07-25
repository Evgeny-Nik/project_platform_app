resource "null_resource" "run_local_script" {
  provisioner "local-exec" {
    command = "${path.module}/check_ingress_status.sh ${helm_release.argocd.namespace} argocd-server ${var.cluster_name} ${var.aws_region} > ${path.module}/check_argocd.log"
    interpreter = ["/bin/bash", "-c"]
  }

  depends_on = [
    time_sleep.wait_for_argocd
  ]
}
