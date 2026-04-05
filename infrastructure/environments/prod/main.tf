# Prod Environment
# HA cluster configuration with larger nodes and stricter access controls.

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
    key            = "gitops-platform/prod/terraform.tfstate"
    region         = "eu-west-2"
    encrypt        = true
    dynamodb_table = "terraform-state-lock"
  }
}

provider "aws" {
  region = var.aws_region
  default_tags {
    tags = {
      Environment = "prod"
      Project     = "k8s-gitops-platform"
      ManagedBy   = "terraform"
    }
  }
}

module "vpc" {
  source             = "../../modules/vpc"
  name               = "gitops-prod"
  vpc_cidr           = "10.20.0.0/16"
  availability_zones = ["eu-west-2a", "eu-west-2b", "eu-west-2c"]
  cluster_name       = "gitops-prod"
}

module "eks" {
  source                 = "../../modules/eks"
  cluster_name           = "gitops-prod"
  kubernetes_version     = "1.29"
  subnet_ids             = module.vpc.all_subnet_ids
  private_subnet_ids     = module.vpc.private_subnet_ids
  enable_public_endpoint = false
  desired_nodes          = 3
  min_nodes              = 3
  max_nodes              = 10
  instance_types         = ["t3.large"]
}
