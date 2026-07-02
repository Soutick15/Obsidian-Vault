#!/usr/bin/env bash
# deploy.sh — Capstone deployment script stub
#
# TODO: Implement the deployment steps for the capstone AI service.
#
# Requirements (from project-brief.md and rubric.md):
#   1. Build and push the Docker image to your container registry
#   2. Apply Kubernetes manifests (or equivalent IaC) to the target cluster
#   3. Wait for the rollout to complete and verify health
#   4. Run a smoke test against the deployed service
#   5. Print a summary of what was deployed and where
#
# Usage:
#   ./deploy.sh [environment]          # e.g. ./deploy.sh staging
#
# Environment variables expected (set in CI/CD or .env):
#   IMAGE_REGISTRY   — container registry URL (e.g. ghcr.io/your-org)
#   IMAGE_TAG        — image tag to deploy (default: git SHA)
#   KUBE_CONTEXT     — kubectl context to use (default: current context)
#   NAMESPACE        — Kubernetes namespace (default: default)
#
# Reference: curriculum/devops/Day-14-cicd-iac-github-terraform-capstone.md
# for CI/CD pipeline design and deployment script best practices.

set -euo pipefail

ENVIRONMENT="${1:-dev}"
IMAGE_REGISTRY="${IMAGE_REGISTRY:-TODO_SET_REGISTRY}"
IMAGE_TAG="${IMAGE_TAG:-$(git rev-parse --short HEAD 2>/dev/null || echo 'latest')}"
NAMESPACE="${NAMESPACE:-default}"

echo "=== Capstone Deploy ==="
echo "  Environment : ${ENVIRONMENT}"
echo "  Image       : ${IMAGE_REGISTRY}/ai-service:${IMAGE_TAG}"
echo "  Namespace   : ${NAMESPACE}"
echo ""

# ---------------------------------------------------------------------------
# TODO 1 — Build and push Docker image
# ---------------------------------------------------------------------------
# docker build -t "${IMAGE_REGISTRY}/ai-service:${IMAGE_TAG}" .
# docker push "${IMAGE_REGISTRY}/ai-service:${IMAGE_TAG}"
echo "[TODO 1] Build and push Docker image — not yet implemented"

# ---------------------------------------------------------------------------
# TODO 2 — Apply Kubernetes manifests
# ---------------------------------------------------------------------------
# kubectl apply -f k8s/ --namespace "${NAMESPACE}"
# kubectl set image deployment/ai-service \
#   ai-service="${IMAGE_REGISTRY}/ai-service:${IMAGE_TAG}" \
#   --namespace "${NAMESPACE}"
echo "[TODO 2] Apply Kubernetes manifests — not yet implemented"

# ---------------------------------------------------------------------------
# TODO 3 — Wait for rollout to complete
# ---------------------------------------------------------------------------
# kubectl rollout status deployment/ai-service \
#   --namespace "${NAMESPACE}" \
#   --timeout=300s
echo "[TODO 3] Wait for rollout — not yet implemented"

# ---------------------------------------------------------------------------
# TODO 4 — Smoke test
# ---------------------------------------------------------------------------
# SERVICE_URL=$(kubectl get service ai-service \
#   --namespace "${NAMESPACE}" \
#   -o jsonpath='{.status.loadBalancer.ingress[0].hostname}')
# curl -sf "http://${SERVICE_URL}/health" | grep '"status":"ok"'
echo "[TODO 4] Smoke test — not yet implemented"

# ---------------------------------------------------------------------------
# TODO 5 — Print deployment summary
# ---------------------------------------------------------------------------
echo ""
echo "=== Deploy complete (stub) ==="
echo "  Replace TODO sections above with real deployment commands."
