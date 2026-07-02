#!/usr/bin/env bash
# =============================================================================
# ILLUSTRATIVE — adapt for your orchestration platform (k8s, ECS, Cloud Run, etc.)
#
# Canary deploy / rollback script for the Acme HR Knowledge Assistant.
#
# Usage (standalone):
#   ./deploy.sh deploy_canary
#   ./deploy.sh run_smoke_test
#   ./deploy.sh promote_to_full
#   ./deploy.sh rollback
#
# Or source in a pipeline and call functions directly.
# =============================================================================

set -euo pipefail

# ---------------------------------------------------------------------------
# Environment variables (override via CI environment or export before calling)
# ---------------------------------------------------------------------------
IMAGE_TAG="${IMAGE_TAG:-latest}"
APP_NAME="${APP_NAME:-acme-hr-assistant}"
CANARY_WEIGHT="${CANARY_WEIGHT:-10}"        # percent of traffic routed to canary
SERVICE_URL="${SERVICE_URL:-http://localhost:8000}"
HEALTH_ENDPOINT="${HEALTH_ENDPOINT:-/health}"
MAX_SMOKE_RETRIES="${MAX_SMOKE_RETRIES:-5}"
SMOKE_RETRY_INTERVAL="${SMOKE_RETRY_INTERVAL:-3}"

# ---------------------------------------------------------------------------
# Logging helpers
# ---------------------------------------------------------------------------
info()    { echo "[INFO]    $(date -u +%H:%M:%SZ)  $*"; }
success() { echo "[SUCCESS] $(date -u +%H:%M:%SZ)  $*"; }
warn()    { echo "[WARN]    $(date -u +%H:%M:%SZ)  $*"; }
error()   { echo "[ERROR]   $(date -u +%H:%M:%SZ)  $*" >&2; }

# ---------------------------------------------------------------------------
# deploy_canary
# Route CANARY_WEIGHT% of traffic to the new image.
# Replace the body with your platform's real deploy command.
# ---------------------------------------------------------------------------
deploy_canary() {
    info "Starting canary deploy..."
    info "  app       : ${APP_NAME}"
    info "  image_tag : ${IMAGE_TAG}"
    info "  weight    : ${CANARY_WEIGHT}%"

    # ILLUSTRATIVE — replace with your platform:
    # --- Kubernetes (Argo Rollouts / native):
    #   kubectl argo rollouts set image rollout/${APP_NAME} app=ghcr.io/acme/${APP_NAME}:${IMAGE_TAG}
    #   kubectl argo rollouts set weight ${APP_NAME} ${CANARY_WEIGHT}
    #
    # --- AWS ECS (CodeDeploy blue/green):
    #   aws deploy create-deployment \
    #     --application-name ${APP_NAME} \
    #     --deployment-group-name ${APP_NAME}-prod \
    #     --revision imageDetail=[{"name":"${APP_NAME}","imageUri":"..."}]
    #
    # --- GCP Cloud Run:
    #   gcloud run services update-traffic ${APP_NAME} \
    #     --to-revisions ${IMAGE_TAG}=${CANARY_WEIGHT}
    #
    # --- Azure Container Apps:
    #   az containerapp revision copy --name ${APP_NAME} --resource-group acme-rg \
    #     --image ghcr.io/acme/${APP_NAME}:${IMAGE_TAG}
    #   az containerapp ingress traffic set --name ${APP_NAME} --resource-group acme-rg \
    #     --traffic-weight latest=${CANARY_WEIGHT} previous=$((100-CANARY_WEIGHT))

    info "[ILLUSTRATIVE] Canary deployed — ${CANARY_WEIGHT}% traffic → ${APP_NAME}:${IMAGE_TAG}"
    success "deploy_canary complete"
}

# ---------------------------------------------------------------------------
# run_smoke_test
# Hit the health endpoint to verify the canary is alive.
# Returns 0 on success, 1 on failure.
# ---------------------------------------------------------------------------
run_smoke_test() {
    info "Running smoke tests against ${SERVICE_URL}${HEALTH_ENDPOINT} ..."

    local attempt=0
    while [[ ${attempt} -lt ${MAX_SMOKE_RETRIES} ]]; do
        attempt=$(( attempt + 1 ))
        info "  Attempt ${attempt}/${MAX_SMOKE_RETRIES}..."

        # ILLUSTRATIVE — in a real environment use curl or httpx:
        # http_status=$(curl -s -o /dev/null -w "%{http_code}" "${SERVICE_URL}${HEALTH_ENDPOINT}")
        # Simulating a successful response here since this is an illustrative script:
        http_status="200"

        if [[ "${http_status}" == "200" ]]; then
            success "Smoke test PASSED (HTTP ${http_status})"
            return 0
        fi

        warn "  Got HTTP ${http_status}, retrying in ${SMOKE_RETRY_INTERVAL}s..."
        sleep "${SMOKE_RETRY_INTERVAL}"
    done

    error "Smoke test FAILED after ${MAX_SMOKE_RETRIES} attempts"
    return 1
}

# ---------------------------------------------------------------------------
# promote_to_full
# Shift 100% of traffic to the canary (now the stable) revision.
# ---------------------------------------------------------------------------
promote_to_full() {
    info "Promoting canary to full rollout (100% traffic)..."

    # ILLUSTRATIVE:
    # --- Kubernetes (Argo Rollouts):
    #   kubectl argo rollouts promote ${APP_NAME}
    #
    # --- GCP Cloud Run:
    #   gcloud run services update-traffic ${APP_NAME} \
    #     --to-revisions ${IMAGE_TAG}=100
    #
    # --- AWS ECS blue/green — approve the deployment:
    #   aws deploy continue-deployment --deployment-id ${DEPLOYMENT_ID} \
    #     --deployment-wait-type READY_WAIT

    info "[ILLUSTRATIVE] Traffic fully shifted to ${APP_NAME}:${IMAGE_TAG}"
    success "promote_to_full complete"
}

# ---------------------------------------------------------------------------
# rollback
# Revert traffic to the previous stable revision.
# ---------------------------------------------------------------------------
rollback() {
    error "Rolling back — reverting traffic to previous stable version..."

    # ILLUSTRATIVE:
    # --- Kubernetes (Argo Rollouts):
    #   kubectl argo rollouts abort ${APP_NAME}
    #   kubectl argo rollouts undo ${APP_NAME}
    #
    # --- GCP Cloud Run:
    #   gcloud run services update-traffic ${APP_NAME} --to-latest
    #   # or pin to the last known good revision:
    #   gcloud run services update-traffic ${APP_NAME} --to-revisions ${STABLE_TAG}=100
    #
    # --- AWS ECS blue/green — stop the deployment:
    #   aws deploy stop-deployment --deployment-id ${DEPLOYMENT_ID} --auto-rollback-enabled

    warn "[ILLUSTRATIVE] Rollback complete — ${APP_NAME} is back on previous stable image"
}

# ---------------------------------------------------------------------------
# Main — full canary flow: deploy → smoke test → promote or rollback
# ---------------------------------------------------------------------------
main() {
    info "=== Canary Deploy Pipeline: ${APP_NAME} ==="

    deploy_canary

    info "Waiting for canary to stabilize..."
    sleep 2   # In production: wait for health checks / metrics

    if run_smoke_test; then
        promote_to_full
        success "=== Deployment SUCCEEDED: ${APP_NAME}:${IMAGE_TAG} ==="
        exit 0
    else
        rollback
        error "=== Deployment FAILED and rolled back: ${APP_NAME}:${IMAGE_TAG} ==="
        exit 1
    fi
}

# ---------------------------------------------------------------------------
# Dispatch: allow calling individual functions or run main flow
# ---------------------------------------------------------------------------
case "${1:-main}" in
    deploy_canary)    deploy_canary ;;
    run_smoke_test)   run_smoke_test ;;
    promote_to_full)  promote_to_full ;;
    rollback)         rollback ;;
    main)             main ;;
    *)
        error "Unknown command: ${1}"
        echo "Usage: $0 [deploy_canary|run_smoke_test|promote_to_full|rollback|main]"
        exit 1
        ;;
esac
