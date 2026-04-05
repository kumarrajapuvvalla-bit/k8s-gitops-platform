# Dev Environment
# Lightweight cluster configuration for development workloads.

terraform {
  required_version = ">= 1.5"
  required_providers {
    aws = {
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }
  }

  backend "s3" {
    bucket         = "your-tfstate-bucket"
    key            = "gitops-platform/dev/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = "dev"
      Project     = "k8s-gitops-platform"
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  name               = "gitops-dev"
  vpc_cidr           = "10.10.0.0/16"
  availability_zones = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  cluster_name       = "gitops-dev"
}

module "eks" {
  source              = "../../modules/eks"
  cluster_name        = "gitops-dev"
  kubernetes_version  = "1.29"
  subnet_ids          = module.vpc.all_subnet_ids
  private_subnet_ids  = module.vpc.private_subnet_ids
  desired_nodes       = 2
  min_nodes           = 1
  max_nodes           = 4
  instance_types      = ["t3.medium"]
}
