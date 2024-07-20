variable "aws_region" {
  type        = string
  description = "The aws region to use"
  default     = "eu-north-1"
}

variable "availability_zones_count" {
  type        = number
  default     = 2
  description = "Number of availability zones to use (min 2)"
}

variable "vpc_cidr" {
  type        = string
  description = "An CIDR for the VPC"
  default     = "10.0.0.0/16"
}

variable "cluster_name" {
  type        = string
  description = "The name of the cluster"
  default     = "potatoland"
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
  default     = "10s"
}