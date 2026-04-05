variable "cluster_name" {
  type        = string
  description = "Name of the EKS cluster"
}

variable "kubernetes_version" {
  type        = string
  description = "Kubernetes version"
  default     = "1.29"
}

variable "subnet_ids" {
  type        = list(string)
  description = "All subnet IDs (public + private)"
}

variable "private_subnet_ids" {
  type        = list(string)
  description = "Private subnet IDs for node groups"
}

variable "enable_public_endpoint" {
  type        = bool
  description = "Enable public API endpoint"
  default     = false
}

variable "public_access_cidrs" {
  type        = list(string)
  description = "CIDRs allowed to reach public endpoint"
  default     = []
}

variable "desired_nodes" {
  type    = number
  default = 2
}

variable "min_nodes" {
  type    = number
  default = 1
}

variable "max_nodes" {
  type    = number
  default = 5
}

variable "instance_types" {
  type    = list(string)
  default = ["t3.medium"]
}

variable "tags" {
  type    = map(string)
  default = {}
}
