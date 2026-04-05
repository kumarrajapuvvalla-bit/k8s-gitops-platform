variable "name" {
  type        = string
  description = "Name prefix for all VPC resources"
}

variable "vpc_cidr" {
  type        = string
  description = "CIDR block for the VPC"
  default     = "10.0.0.0/16"
}

variable "availability_zones" {
  type        = list(string)
  description = "List of AZs to deploy subnets into"
}

variable "cluster_name" {
  type        = string
  description = "EKS cluster name for subnet tagging"
}

variable "tags" {
  type    = map(string)
  default = {}
}
