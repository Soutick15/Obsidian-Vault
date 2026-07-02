# TODO: Terraform configuration for the capstone AI service infrastructure.
#
# Requirements (from project-brief.md and rubric.md):
#   - Declare required providers and backend configuration
#   - Define at least one variable (e.g., environment, region, image_tag)
#   - Define at least one resource (e.g., container registry, secret store entry,
#     or cloud run / ECS service for the AI service)
#   - Define at least one output (e.g., service endpoint URL)
#
# Reference: curriculum/devops/Day-14-cicd-iac-github-terraform-capstone.md §3.6
# for Terraform core concepts and an illustrative HCL example.
#
# Stub — this file will not apply as-is. Fill in all TODO sections.

terraform {
  required_version = ">= 1.5"

  # TODO: configure remote backend (e.g., S3 + DynamoDB lock, GCS, Terraform Cloud)
  # backend "s3" {
  #   bucket         = "TODO-your-state-bucket"
  #   key            = "capstone/ai-service/terraform.tfstate"
  #   region         = "us-east-1"
  #   dynamodb_table = "TODO-your-lock-table"
  #   encrypt        = true
  # }

  required_providers {
    # TODO: add the provider(s) you need, e.g.:
    # aws = {
    #   source  = "hashicorp/aws"
    #   version = "~> 5.0"
    # }
  }
}

# TODO: configure the provider, e.g.:
# provider "aws" {
#   region = var.region
# }

# ---------------------------------------------------------------------------
# Variables
# ---------------------------------------------------------------------------

variable "environment" {
  description = "Deployment environment (dev | staging | production)"
  type        = string
  default     = "dev"  # TODO: override via tfvars or CI/CD pipeline variable
}

variable "image_tag" {
  description = "Docker image tag to deploy (set by CI/CD pipeline)"
  type        = string
  default     = "latest"  # TODO: pin to a specific SHA in production
}

# TODO: add additional variables as needed (region, project, etc.)

# ---------------------------------------------------------------------------
# Resources
# ---------------------------------------------------------------------------

# TODO: define your infrastructure resources here.
# Examples:
#   - aws_secretsmanager_secret for the LLM API key
#   - aws_ecr_repository for the container image
#   - aws_ecs_service / google_cloud_run_service for the AI service
#   - kubernetes_namespace + kubernetes_deployment if using K8s via Terraform

# ---------------------------------------------------------------------------
# Outputs
# ---------------------------------------------------------------------------

# TODO: expose useful values as outputs, e.g.:
# output "service_endpoint" {
#   description = "Public URL of the deployed AI service"
#   value       = "TODO"
# }

output "environment" {
  description = "Deployed environment name"
  value       = var.environment
}
