variable "alb_ingress" {
  type        = string
  description = "AWS Load Balancer Controller Version"
  default     = "1.7.2"
}
variable "cluster_name" {
  type        = string
  description = "Name of EKS cluster"
  default     = "Potatoland"
}
variable "cluster_version" {
  type        = string
  description = "Version of EKS cluster"
  default     = "1.29"
}
variable "domain" {
  type        = string
  description = "Route 53 Domain Name"
  default     = "evg-platform-app.com"
}
variable "environment" {
  type        = string
  description = "Cluster Environment"
  default     = "Development"
}
variable "external_dns" {
  type        = string
  description = "External DNS Version"
  default     = "6.14.3"
}
variable "hosted_zone_id" {
  type        = string
  description = "Route 53 Hosted Zone Id"
}
variable "instance_types" {
  type        = string
  description = "EKS Worker Node Type"
  default     = "t3.medium"
}
variable "desired_size" {
  type        = number
  description = "Autoscaling desired instance size"
  default     = 2
}
variable "max_size" {
  type        = number
  description = "Maximum instances"
  default     = 5
}
variable "min_size" {
  type        = number
  description = "Minimum instances"
  default     = 2
}
variable "max_unavailable" {
  type        = number
  description = "Maximum Unavailable instances"
  default     = 1
}
variable "vpc_cidr" {
  type        = string
  description = "Vpc CIDR"
  default     = "10.0.0.0/16"
}
variable "aws_region" {
  type        = string
  description = "AWS Resources Region"
  default     = "eu-north-1"
}

variable "availability_zones_count" {
  type        = number
  default     = 3
  description = "Number of availability zones to use (min 2)"
}

variable "dockerhub_username" {
  description = "DockerHub username"
  type        = string
}

variable "dockerhub_access_token" {
  description = "DockerHub access token"
  type        = string
}

variable "wait_time" {
  type        = string
  description = "The time to wait for creation of helm charts"
  default     = "30s"
}