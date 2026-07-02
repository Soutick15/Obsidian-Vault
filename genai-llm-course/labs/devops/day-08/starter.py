"""
Day 8 Lab — Kubernetes Manifest Validation & Load Testing (starter)

Work through each TODO in order. Run the file when done:
    python labs/devops/day-08/starter.py

Expected final output:
    [manifest] Loaded 4 manifests
    [check] Deployment probes OK
    [check] Resource limits OK
    [check] Selector/label consistency OK
    [check] HPA target OK
    [load-test] 50 requests in X.XX s -> YY.Y req/s (all 200 OK)
    [summary] All manifest checks passed. Load test complete.

No API key required — the shared app runs with USE_MOCK=true by default.
"""

from __future__ import annotations

import os
import pathlib
import sys
import time
import concurrent.futures

# ---------------------------------------------------------------------------
# Shared app import — works from any working directory
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
LOAD_TEST_N = 50   # total requests
LOAD_TEST_W = 5    # max concurrent workers


def load_manifests() -> dict[str, dict]:
    """
    TODO 1 — Load and parse all four YAML manifests.

    For each entry in MANIFEST_FILES:
      - Open the file
      - Parse it with yaml.safe_load()
      - Store the result in a dict keyed by the same name (deployment, service, hpa, configmap)

    Return the dict.
    Raise FileNotFoundError with a helpful message if any file is missing.
    """
    manifests: dict[str, dict] = {}

    for name, path in MANIFEST_FILES.items():
        # TODO 1: load and parse `path` with yaml.safe_load()
        raise NotImplementedError(f"TODO 1: load {name} from {path}")

    print(f"[manifest] Loaded {len(manifests)} manifests")
    return manifests


def check_probes(deployment: dict) -> None:
    """
    TODO 2 — Assert readiness and liveness probes are configured correctly.

    Given a parsed Deployment dict, navigate to:
      deployment["spec"]["template"]["spec"]["containers"][0]

    Assert:
      - "readinessProbe" key exists
      - readinessProbe["httpGet"]["path"] == "/health"
      - "livenessProbe" key exists
      - livenessProbe["httpGet"]["path"] == "/health"

    If any assertion fails, raise AssertionError with a descriptive message.
    On success, print: [check] Deployment probes OK
    """
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    # TODO 2: assert readinessProbe and livenessProbe exist and point to /health
    raise NotImplementedError("TODO 2: check probe configuration")

    print("[check] Deployment probes OK")


def check_resources(deployment: dict) -> None:
    """
    TODO 3 — Assert CPU and memory requests and limits are set on the container.

    Navigate to the first container's "resources" dict.
    Assert that both "requests" and "limits" sub-dicts contain
    the keys "cpu" and "memory" with non-empty string values.

    On success, print: [check] Resource limits OK
    """
    container = deployment["spec"]["template"]["spec"]["containers"][0]

    # TODO 3: assert resources.requests and resources.limits each have cpu and memory
    raise NotImplementedError("TODO 3: check resource requests and limits")

    print("[check] Resource limits OK")


def check_selector_consistency(deployment: dict, service: dict) -> None:
    """
    TODO 4 — Assert the Deployment selector and Service selector both target the same labels.

    Extract:
      deployment_selector = deployment["spec"]["selector"]["matchLabels"]
      service_selector    = service["spec"]["selector"]

    Assert they are equal. A mismatch means the Service will have empty
    endpoints and all traffic will be silently dropped.

    On success, print: [check] Selector/label consistency OK
    """
    # TODO 4: extract both selectors and assert they are equal
    raise NotImplementedError("TODO 4: check selector/label consistency")

    print("[check] Selector/label consistency OK")


def check_hpa_target(hpa: dict, deployment: dict) -> None:
    """
    TODO 5 — Assert the HPA scaleTargetRef points to the correct Deployment.

    Extract:
      hpa_target_name      = hpa["spec"]["scaleTargetRef"]["name"]
      deployment_name      = deployment["metadata"]["name"]
      hpa_target_api_group = hpa["spec"]["scaleTargetRef"]["apiVersion"]

    Assert:
      - hpa_target_name == deployment_name
      - hpa_target_api_group == "apps/v1"

    On success, print: [check] HPA target OK
    """
    # TODO 5: extract names and assert they match
    raise NotImplementedError("TODO 5: check HPA target name")

    print("[check] HPA target OK")


def run_load_test(n: int = LOAD_TEST_N, workers: int = LOAD_TEST_W) -> None:
    """
    TODO 6 — Run a concurrent load test against the shared app and print throughput.

    Use FastAPI's TestClient (starlette.testclient.TestClient) to make in-process
    HTTP requests — no real network or running server needed.

    Steps:
      1. Create a TestClient wrapping `app`.
      2. Verify the app is healthy: GET /health must return 200.
      3. Use concurrent.futures.ThreadPoolExecutor(max_workers=workers) to send
         `n` GET /health requests concurrently.
      4. Record start time before submitting futures, end time after all complete.
      5. Count how many returned status_code == 200.
      6. Compute throughput = n / elapsed_seconds.
      7. Print: [load-test] {n} requests in {elapsed:.2f} s -> {rps:.1f} req/s ({ok} OK)

    Hints:
      - TestClient is thread-safe for reads.
      - futures = [executor.submit(client.get, "/health") for _ in range(n)]
      - results = [f.result() for f in concurrent.futures.as_completed(futures)]
    """
    # TODO 6: implement the load test
    raise NotImplementedError("TODO 6: implement concurrent load test")


def main() -> None:
    # Set mock mode so no API key is needed
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
