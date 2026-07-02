"""
Day 8 Lab — Kubernetes Manifest Validation & Load Testing (solution)

Validates the four Kubernetes manifests in this directory by parsing YAML
and asserting required structural properties, then runs a small concurrent
load test against the shared HR Assistant app via FastAPI's TestClient.

No API key required. No Kubernetes cluster required.

Usage:
    python labs/devops/day-08/solution.py
"""

from __future__ import annotations

import concurrent.futures
import os
import pathlib
import sys
import time

# ---------------------------------------------------------------------------
# Shared app import — resolved relative to this file, works from any cwd
# ---------------------------------------------------------------------------
_HERE = pathlib.Path(__file__).resolve()
_SHARED = _HERE.parents[1] / "_shared"
sys.path.insert(0, str(_SHARED))

from app import app  # FastAPI application instance  # noqa: E402
from starlette.testclient import TestClient  # noqa: E402
import yaml  # noqa: E402

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------
LAB_DIR = _HERE.parent
MANIFEST_FILES = {
    "deployment": LAB_DIR / "deployment.yaml",
    "service":    LAB_DIR / "service.yaml",
    "hpa":        LAB_DIR / "hpa.yaml",
    "configmap":  LAB_DIR / "configmap.yaml",
}
LOAD_TEST_N = 50   # total requests for the load test
LOAD_TEST_W = 5    # max concurrent workers


# ---------------------------------------------------------------------------
# Step 1: Load manifests
# ---------------------------------------------------------------------------

def load_manifests() -> dict[str, dict]:
    """Parse all four YAML manifest files and return them keyed by name."""
    manifests: dict[str, dict] = {}
    for name, path in MANIFEST_FILES.items():
        if not path.exists():
            raise FileNotFoundError(
                f"Manifest not found: {path}\n"
                f"Make sure you are running from the repo root or that the file exists."
            )
        with path.open("r", encoding="utf-8") as fh:
            parsed = yaml.safe_load(fh)
        if parsed is None:
            raise ValueError(f"Empty or invalid YAML in {path}")
        manifests[name] = parsed
    print(f"[manifest] Loaded {len(manifests)} manifests")
    return manifests


# ---------------------------------------------------------------------------
# Step 2: Probe validation
# ---------------------------------------------------------------------------

def check_probes(deployment: dict) -> None:
    """
    Assert readiness and liveness probes exist on the first container
    and target /health.
    """
    containers = deployment["spec"]["template"]["spec"]["containers"]
    assert containers, "Deployment has no containers defined"
    container = containers[0]

    # Readiness probe
    assert "readinessProbe" in container, (
        f"Container '{container.get('name')}' is missing readinessProbe. "
        "Without a readinessProbe, Kubernetes routes traffic to the pod before "
        "it is ready, causing request failures during startup."
    )
    rp_path = container["readinessProbe"]["httpGet"]["path"]
    assert rp_path == "/health", (
        f"readinessProbe.httpGet.path is '{rp_path}', expected '/health'"
    )

    # Liveness probe
    assert "livenessProbe" in container, (
        f"Container '{container.get('name')}' is missing livenessProbe. "
        "Without a livenessProbe, Kubernetes cannot detect deadlocked pods."
    )
    lp_path = container["livenessProbe"]["httpGet"]["path"]
    assert lp_path == "/health", (
        f"livenessProbe.httpGet.path is '{lp_path}', expected '/health'"
    )

    print("[check] Deployment probes OK")


# ---------------------------------------------------------------------------
# Step 3: Resource validation
# ---------------------------------------------------------------------------

def check_resources(deployment: dict) -> None:
    """
    Assert CPU and memory requests and limits are set on the first container.
    Missing resources means the scheduler cannot place the pod correctly and
    the container is subject to best-effort eviction.
    """
    containers = deployment["spec"]["template"]["spec"]["containers"]
    container = containers[0]

    resources = container.get("resources", {})
    assert resources, (
        f"Container '{container.get('name')}' has no 'resources' block. "
        "Always set requests (for scheduler placement) and limits (for OOM protection)."
    )

    for tier in ("requests", "limits"):
        tier_data = resources.get(tier, {})
        assert tier_data, f"resources.{tier} is missing or empty"
        for field in ("cpu", "memory"):
            val = tier_data.get(field, "")
            assert val, (
                f"resources.{tier}.{field} is not set. "
                f"This is required for correct scheduler behaviour and resource isolation."
            )

    print("[check] Resource limits OK")


# ---------------------------------------------------------------------------
# Step 4: Selector/label consistency
# ---------------------------------------------------------------------------

def check_selector_consistency(deployment: dict, service: dict) -> None:
    """
    Assert the Deployment's matchLabels selector equals the Service's selector.

    A mismatch causes the Service to have empty endpoints — traffic is silently
    dropped and no error is raised at apply time. This is one of the most common
    Kubernetes misconfiguration bugs.
    """
    deployment_selector: dict = deployment["spec"]["selector"]["matchLabels"]
    service_selector: dict = service["spec"]["selector"]

    assert deployment_selector == service_selector, (
        f"Selector mismatch!\n"
        f"  Deployment matchLabels: {deployment_selector}\n"
        f"  Service selector:       {service_selector}\n"
        "These must be identical, otherwise the Service has no endpoints "
        "and all traffic is dropped."
    )

    # Also verify pod template labels contain at least the selector labels
    pod_labels: dict = deployment["spec"]["template"]["metadata"]["labels"]
    for key, val in deployment_selector.items():
        assert pod_labels.get(key) == val, (
            f"Pod template label '{key}={val}' (from matchLabels) not found in "
            f"pod template metadata.labels: {pod_labels}"
        )

    print("[check] Selector/label consistency OK")


# ---------------------------------------------------------------------------
# Step 5: HPA target validation
# ---------------------------------------------------------------------------

def check_hpa_target(hpa: dict, deployment: dict) -> None:
    """
    Assert the HPA scaleTargetRef.name matches the Deployment name and
    targets the correct API group.
    """
    scale_target = hpa["spec"]["scaleTargetRef"]
    hpa_target_name: str = scale_target["name"]
    hpa_api_version: str = scale_target["apiVersion"]
    deployment_name: str = deployment["metadata"]["name"]

    assert hpa_target_name == deployment_name, (
        f"HPA scaleTargetRef.name '{hpa_target_name}' does not match "
        f"Deployment name '{deployment_name}'. The HPA will fail to find its target."
    )
    assert hpa_api_version == "apps/v1", (
        f"HPA scaleTargetRef.apiVersion is '{hpa_api_version}', expected 'apps/v1'."
    )

    # Verify replica bounds make sense
    min_replicas = hpa["spec"].get("minReplicas", 1)
    max_replicas = hpa["spec"]["maxReplicas"]
    assert isinstance(min_replicas, int) and min_replicas >= 1, (
        f"HPA minReplicas should be >= 1, got {min_replicas}"
    )
    assert isinstance(max_replicas, int) and max_replicas > min_replicas, (
        f"HPA maxReplicas ({max_replicas}) must be greater than minReplicas ({min_replicas})"
    )

    print("[check] HPA target OK")


# ---------------------------------------------------------------------------
# Step 6: Concurrent load test
# ---------------------------------------------------------------------------

def run_load_test(n: int = LOAD_TEST_N, workers: int = LOAD_TEST_W) -> None:
    """
    Send `n` GET /health requests concurrently using FastAPI's TestClient.

    TestClient drives the ASGI application in-process — no real server
    or network socket is needed. This is identical to the request handling
    path a real server would exercise, making it a valid throughput proxy.

    The test illustrates *why* horizontal scaling matters: measure the
    requests/second achievable by a single in-process replica, then extrapolate
    what happens when demand exceeds that capacity.
    """
    os.environ.setdefault("USE_MOCK", "true")

    with TestClient(app, raise_server_exceptions=True) as client:
        # Sanity-check the app is healthy before load testing
        health_r = client.get("/health")
        assert health_r.status_code == 200, (
            f"Pre-load-test health check failed: {health_r.status_code} {health_r.text}"
        )

        # Submit `n` concurrent GET /health requests
        start = time.perf_counter()
        with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
            futures = [executor.submit(client.get, "/health") for _ in range(n)]
            results = [f.result() for f in concurrent.futures.as_completed(futures)]
        elapsed = time.perf_counter() - start

        ok = sum(1 for r in results if r.status_code == 200)
        rps = n / elapsed if elapsed > 0 else float("inf")

        print(
            f"[load-test] {n} requests in {elapsed:.2f} s "
            f"-> {rps:.1f} req/s ({ok}/{n} 200 OK)"
        )

        # Sanity assertions
        assert ok == n, (
            f"Load test: {n - ok} requests failed (non-200 status). "
            "Check the app logs for errors."
        )


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main() -> None:
    os.environ.setdefault("USE_MOCK", "true")

    manifests = load_manifests()
    check_probes(manifests["deployment"])
    check_resources(manifests["deployment"])
    check_selector_consistency(manifests["deployment"], manifests["service"])
    check_hpa_target(manifests["hpa"], manifests["deployment"])
    run_load_test()
    print("[summary] All manifest checks passed. Load test complete.")


if __name__ == "__main__":
    main()
