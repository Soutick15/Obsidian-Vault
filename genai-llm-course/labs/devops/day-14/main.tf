# =============================================================================
# ILLUSTRATIVE — swap provider for your cloud (aws / gcp / azure).
# This file uses the "local" provider purely so `terraform validate` runs
# without any cloud credentials. In a real deployment, replace:
#   hashicorp/local  →  hashicorp/aws  (or google / azurerm)
#   local_file       →  aws_ecs_service / google_cloud_run_service / azurerm_container_group
# =============================================================================

terraform {
  required_version = ">= 1.6.0"

  required_providers {
    # ILLUSTRATIVE: swap "local" for your real cloud provider
    # aws   { source = "hashicorp/aws",   version = "~> 5.0" }
    # google { source = "hashicorp/google", version = "~> 5.0" }
    # azurerm { source = "hashicorp/azurerm", version = "~> 3.0" }
    local = {
      source  = "hashicorp/local"
      version = "~> 2.4"
    }
  }

  # Recommended: store state remotely in production
  # backend "s3" {
  #   bucket = "acme-tfstate"
  #   key    = "hr-assistant/terraform.tfstate"
  #   region = "us-east-1"
  # }
}

# =============================================================================
# Provider configuration
# ILLUSTRATIVE — replace with your cloud provider block, e.g.:
#   provider "aws"    { region = var.region }
#   provider "google" { project = var.project_id; region = var.region }
# =============================================================================
provider "local" {
  # No configuration needed for the local provider
}

# =============================================================================
# Variables — parameterise all deployment-specific values
# =============================================================================

variable "app_name" {
  description = "Name of the LLM service (used in resource names and labels)"
  type        = string
  default     = "acme-hr-assistant"
}

variable "image_tag" {
  description = "Docker image tag to deploy (typically the git SHA from CI)"
  type        = string
  # No default — must be supplied at apply time: -var image_tag=abc1234
}

variable "replicas" {
  description = "Number of service replicas (tasks / pods / instances)"
  type        = number
  default     = 2

  validation {
    condition     = var.replicas >= 1 && var.replicas <= 20
    error_message = "replicas must be between 1 and 20."
  }
}

variable "environment" {
  description = "Deployment environment: dev | staging | production"
  type        = string
  default     = "staging"

  validation {
    condition     = contains(["dev", "staging", "production"], var.environment)
    error_message = "environment must be one of: dev, staging, production."
  }
}

# =============================================================================
# Locals — derived values used across resources
# =============================================================================
locals {
  service_name = "${var.app_name}-${var.environment}"
  common_tags = {
    app         = var.app_name
    environment = var.environment
    managed_by  = "terraform"
    image_tag   = var.image_tag
  }
}

# =============================================================================
# Resource — Container / Compute Service
#
# ILLUSTRATIVE: This uses local_file as a stand-in so Terraform can validate
# the config without cloud credentials.
#
# Replace with the real resource for your platform:
#   AWS ECS:      aws_ecs_service + aws_ecs_task_definition
#   GCP Cloud Run: google_cloud_run_v2_service
#   Azure:        azurerm_container_group
#   Kubernetes:   kubernetes_deployment + kubernetes_service
# =============================================================================
resource "local_file" "service_manifest" {
  # ILLUSTRATIVE stand-in — replace with aws_ecs_service / google_cloud_run_service /
  # azurerm_container_group once you swap the provider above.
  filename = "${path.module}/.terraform-local/${local.service_name}-manifest.json"
  content = jsonencode({
    service     = local.service_name
    image       = "ghcr.io/acme/${var.app_name}:${var.image_tag}"
    replicas    = var.replicas
    environment = var.environment
    port        = 8000
    health_path = "/health"
    tags        = local.common_tags
  })

  # Example of what a real ECS resource block looks like (commented out):
  # resource "aws_ecs_service" "hr_assistant" {
  #   name            = local.service_name
  #   cluster         = aws_ecs_cluster.main.id
  #   task_definition = aws_ecs_task_definition.hr_assistant.arn
  #   desired_count   = var.replicas
  #   launch_type     = "FARGATE"
  #   ...
  # }
}

# =============================================================================
# Outputs — expose key deployment values for downstream use (e.g., CI smoke tests)
# =============================================================================
output "service_url" {
  description = "Public URL of the deployed LLM service"
  # ILLUSTRATIVE: replace with the real attribute from your cloud resource, e.g.:
  #   aws_lb.main.dns_name
  #   google_cloud_run_v2_service.hr_assistant.uri
  #   azurerm_container_group.hr_assistant.fqdn
  value = "https://${local.service_name}.example.com"
}

output "image_deployed" {
  description = "Full image reference that was deployed"
  value       = "ghcr.io/acme/${var.app_name}:${var.image_tag}"
}

output "environment" {
  description = "Target environment for this deployment"
  value       = var.environment
}
