# Day 8 — Scaling & Orchestration: Kubernetes for LLM Services

**Track:** DevOps | **Week:** 2 | **Day:** 8 of 15

---

## 1. Objectives

By the end of this day you will be able to:

- Describe the **core Kubernetes primitives** — Deployment, Service, HorizontalPodAutoscaler, ConfigMap, Secret — and explain how they compose to deploy a production LLM service.
- Write `deployment.yaml` manifests with correct **resource requests/limits**, **readiness**, **liveness**, and **startup probes** targeting your service's `/health` endpoint.
- Configure a **HorizontalPodAutoscaler** to scale on CPU/memory and articulate how custom metrics (requests-per-second, queue depth) extend that model.
- Explain **rolling update** strategies and why they matter for LLM services with slow startup times.
- Describe **GPU scheduling** in Kubernetes: node selectors, taints/tolerations, and the NVIDIA device plugin.
- Explain why GPUs matter for **self-hosted LLM inference** and what happens when you try to run inference on CPU-only pods.
- Understand inference optimisations that change scaling economics: **continuous batching**, **PagedAttention** (vLLM), **quantization for serving**, and **speculative decoding** — and how each shifts throughput, latency, and cost.
- Validate Kubernetes manifests programmatically and measure the throughput of the shared app under concurrent load.

---

## 2. Concept Reading

### 2.1 Why Kubernetes for LLM Services?

Deploying an LLM service is not the same as deploying a stateless API. Consider what is special:

- **Large memory footprint**: even quantised models occupy gigabytes of GPU VRAM. Misscheduling a pod onto a node without enough VRAM causes OOM kills, not a polite HTTP 503.
- **Slow startup**: loading model weights from disk or object storage can take 30–120 seconds. Kubernetes needs to know when the pod is truly ready to serve traffic, not just when the container process has started.
- **Spiky but inelastic demand**: a company-wide HR assistant may idle at 2 RPS for hours and then spike to 80 RPS during business hours. Manual scaling cannot respond in time.
- **Heterogeneous hardware**: GPU nodes are expensive. You want LLM pods scheduled onto GPU nodes and everything else onto cheaper CPU nodes.

Kubernetes addresses all four concerns through its scheduling, probing, and autoscaling primitives.

---

### 2.2 Core Primitives

#### 2.2.1 Deployment

A `Deployment` declares the desired state for a set of identical pods (replicas). Kubernetes continuously reconciles actual state toward desired state — if a pod crashes, it is replaced; if a node is drained, pods are rescheduled.

```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: hr-assistant
spec:
  replicas: 2
  selector:
    matchLabels:
      app: hr-assistant
  template:
    metadata:
      labels:
        app: hr-assistant
    spec:
      containers:
        - name: hr-assistant
          image: acme/hr-assistant:0.1.0
          ports:
            - containerPort: 8000
          resources:
            requests:
              cpu: "250m"
              memory: "512Mi"
            limits:
              cpu: "1000m"
              memory: "1Gi"
```

**Resource requests vs. limits** is a distinction that trips up many teams:

- **Request**: what the scheduler guarantees the pod will have. The pod is placed on a node that has at least this much free. Never set requests to zero — the scheduler cannot make sensible placement decisions.
- **Limit**: a hard ceiling. If CPU usage exceeds the limit, the kernel throttles the process. If memory exceeds the limit, the pod is OOM-killed and restarted. For LLM services, set memory limits conservatively above the known peak (model weights + serving overhead + request buffers).

#### 2.2.2 Probes

Kubernetes uses three probe types to manage pod lifecycle:

| Probe | Question answered | Action on failure |
|-------|-------------------|-------------------|
| **startupProbe** | Has the app finished initialising? | Keep retrying; block liveness/readiness checks until it passes |
| **readinessProbe** | Is the app ready to accept traffic? | Remove pod from Service endpoints (no traffic sent) |
| **livenessProbe** | Is the app still alive (not deadlocked)? | Restart the container |

For LLM services:

- Use a **startupProbe** with a generous `failureThreshold` × `periodSeconds` window (e.g., 20 × 15s = 5 minutes) to cover model loading time.
- Use a **readinessProbe** on `/health` with a tight `successThreshold` (1 pass = ready). This ensures traffic is only routed once the model is warm and the service can actually respond.
- Use a **livenessProbe** less aggressively (longer `initialDelaySeconds`) to avoid killing a healthy but slow-starting pod.

```yaml
startupProbe:
  httpGet:
    path: /health
    port: 8000
  failureThreshold: 20
  periodSeconds: 15

readinessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 10
  periodSeconds: 5
  failureThreshold: 3

livenessProbe:
  httpGet:
    path: /health
    port: 8000
  initialDelaySeconds: 60
  periodSeconds: 15
  failureThreshold: 4
```

#### 2.2.3 Service

A `Service` provides a stable DNS name and virtual IP (ClusterIP) that load-balances across the matching pods. The selector must match the pod labels exactly.

```yaml
apiVersion: v1
kind: Service
metadata:
  name: hr-assistant-svc
spec:
  selector:
    app: hr-assistant
  ports:
    - port: 80
      targetPort: 8000
  type: ClusterIP
```

Service types:
- **ClusterIP** — internal only; use with an Ingress controller for external access.
- **NodePort** — exposes on a node port; adequate for demos, not production.
- **LoadBalancer** — cloud provider provisions a load balancer (AWS ELB, GCP LB, etc.).

#### 2.2.4 HorizontalPodAutoscaler (HPA)

The HPA watches metrics and adjusts `spec.replicas` on the target Deployment. The default metrics are CPU and memory utilisation relative to requests. Custom metrics (queue depth, pending requests, GPU utilisation) require the Kubernetes Custom Metrics API backed by Prometheus Adapter or KEDA.

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: hr-assistant-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: hr-assistant
  minReplicas: 1
  maxReplicas: 8
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 60
    - type: Resource
      resource:
        name: memory
        target:
          type: Utilization
          averageUtilization: 75
```

**Scale-out lag**: the HPA evaluates metrics every 15 seconds by default and waits for the `--horizontal-pod-autoscaler-sync-period`. New pods must also pass readiness probes before receiving traffic. For LLM services with 60-second startup, a spike can saturate current capacity for 75–120 seconds before relief arrives. Mitigation strategies: over-provision minimum replicas, use KEDA with predictive scaling, or keep warm standby pods.

#### 2.2.5 ConfigMap and Secret

- **ConfigMap**: non-sensitive configuration (feature flags, model names, log levels, default K values). Mounted as environment variables or files.
- **Secret**: sensitive values (API keys, database passwords, TLS certificates). Base64-encoded in etcd; mount via `envFrom` or volume, never bake into container images.

```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: hr-assistant-config
data:
  APP_VERSION: "0.1.0"
  DEFAULT_K: "3"
  LOG_LEVEL: "INFO"
  USE_MOCK: "true"
```

---

### 2.3 Rolling Updates

A `RollingUpdate` strategy (the default) replaces old pods with new ones gradually:

```yaml
strategy:
  type: RollingUpdate
  rollingUpdate:
    maxSurge: 1        # create up to 1 extra pod above desired count
    maxUnavailable: 0  # never drop below desired count during update
```

`maxUnavailable: 0` combined with readiness probes gives zero-downtime deployments: Kubernetes waits for each new pod to pass readiness before terminating an old one. For LLM services where model loading is slow, this is not optional — it is the safety guarantee.

**Rollback**: `kubectl rollout undo deployment/hr-assistant` immediately reverts to the previous ReplicaSet. Kubernetes retains the last 10 ReplicaSets by default (`revisionHistoryLimit`).

---

### 2.4 Autoscaling Strategies

| Strategy | Mechanism | Best for |
|----------|-----------|----------|
| **CPU/Memory HPA** | Built-in Kubernetes metrics | Stateless services with CPU-bound work |
| **Custom metrics HPA** | Prometheus Adapter + HPA | Request queue depth, tokens/sec, GPU utilisation |
| **KEDA** | Event-driven: Kafka lag, SQS depth, HTTP RPS | Async inference pipelines, batch jobs |
| **Vertical Pod Autoscaler (VPA)** | Adjusts requests/limits, not replica count | Right-sizing memory-heavy pods |
| **Cluster Autoscaler** | Adds/removes nodes | Expensive GPU nodes you only want when needed |

For LLM inference in production, **KEDA with HTTP RPS or queue depth** is often more responsive than CPU-based HPA because GPU-bound inference may never spike CPU while the request queue grows.

---

### 2.5 GPU Scheduling

#### 2.5.1 Why GPUs for LLM Inference?

A transformer forward pass is dominated by large matrix multiplications. On a modern GPU (e.g., NVIDIA A100 80GB):

- **Tensor cores** execute INT8/FP16 matrix operations at ~300 TFLOPS vs. ~2 TFLOPS on a high-end CPU.
- **High-bandwidth memory (HBM)**: 2 TB/s vs. ~50 GB/s on a CPU. For LLM inference, memory bandwidth is often the bottleneck, not compute — loading 70B model weights from VRAM to registers at each forward pass benefits enormously from HBM.

Result: a 7B-parameter model that generates 2–5 tokens/second on CPU generates 80–150 tokens/second on a single A100. For a multi-user service, this is not a performance difference — it is the difference between viable and non-viable.

#### 2.5.2 NVIDIA Device Plugin

To expose GPUs to Kubernetes pods, you deploy the [NVIDIA device plugin](https://github.com/NVIDIA/k8s-device-plugin) as a DaemonSet. It:

1. Detects GPUs on each node via the NVIDIA Management Library (NVML).
2. Registers them as the extended resource `nvidia.com/gpu`.
3. Kubelet then allocates them to pods that request them.

Pod request:

```yaml
resources:
  limits:
    nvidia.com/gpu: 1   # request 1 GPU
```

Unlike CPU and memory, GPUs are not divisible (without MIG or time-slicing). Requesting `nvidia.com/gpu: 1` reserves the entire physical GPU.

#### 2.5.3 Node Selectors and Taints/Tolerations

You need to ensure LLM pods land on GPU nodes and non-LLM pods do not waste GPU slots:

```yaml
# On the GPU node (via kubectl taint):
# kubectl taint nodes gpu-node-1 nvidia.com/gpu=present:NoSchedule

# In the pod spec:
nodeSelector:
  accelerator: nvidia-a100

tolerations:
  - key: "nvidia.com/gpu"
    operator: "Equal"
    value: "present"
    effect: "NoSchedule"
```

**Taints** repel pods; **tolerations** allow a pod to be scheduled on a tainted node. Together they form an opt-in mechanism: only pods that explicitly tolerate the GPU taint land on those expensive nodes.

---

### 2.6 Inference Optimisations That Affect Scaling

Understanding these concepts lets you choose serving infrastructure wisely. They are the reason a well-tuned vLLM deployment can serve 10× more concurrent users on the same hardware as a naive implementation.

#### 2.6.1 Continuous Batching

**Naive batching**: collect N requests, run one forward pass for all of them together, return N responses. Simple, but requests at different stages of generation must wait for the slowest one in the batch to finish. GPU utilisation drops when some sequences finish early.

**Continuous batching** (also called *iteration-level scheduling* or *in-flight batching*): the serving engine schedules at the granularity of individual decoding steps. A newly arrived request joins the batch immediately when any existing sequence finishes its current token. The GPU always has a full batch to process. This is the fundamental algorithmic advance in [Orca (OSDI 2022)](https://www.usenix.org/conference/osdi22/presentation/yu) and is implemented in vLLM, TGI, and TensorRT-LLM.

**Effect on scaling**: continuous batching multiplies effective throughput by 2–10× compared to static batching at the same hardware cost. You need fewer GPU replicas for the same RPS target, which substantially reduces cost.

#### 2.6.2 PagedAttention (vLLM)

During autoregressive decoding, the KV cache (key-value pairs from the attention mechanism) grows with each generated token. In a naive implementation, each sequence pre-allocates the maximum context length in contiguous GPU memory — even if most sequences are much shorter.

**PagedAttention** (from [vLLM, SOSP 2023](https://arxiv.org/abs/2309.05852)) applies the OS paging concept to KV cache:

- KV cache is divided into fixed-size **blocks** (like memory pages).
- Each sequence is allocated only the blocks it actually uses; they need not be contiguous.
- A **block manager** tracks allocation; finished sequences' blocks are immediately returned to a free pool.

**Effect on scaling**: memory fragmentation drops from ~70% waste (naive) to ~4% waste (PagedAttention). This allows vLLM to batch 10–20× more concurrent sequences in the same VRAM. Higher batch sizes at the same memory footprint means more tokens/second per GPU — directly improving service throughput and reducing cost-per-request.

#### 2.6.3 Quantization for Serving

Quantization reduces the numerical precision of model weights and/or activations:

| Format | Bits per weight | Memory vs. FP16 | Throughput impact | Quality impact |
|--------|----------------|-----------------|-------------------|----------------|
| FP16 | 16 | 1× (baseline) | Baseline | None |
| INT8 (LLM.int8, SmoothQuant) | 8 | 0.5× | +20–40% | Negligible for large models |
| NF4/INT4 (GPTQ, AWQ, bitsandbytes) | 4 | 0.25× | +50–80% | Small but measurable |
| INT2 | 2 | 0.125× | Higher | Significant |

For a 70B FP16 model requiring 140 GB VRAM (2× A100 80GB), INT4 quantization fits it in ~35 GB (single A100). The practical consequence: quantization can eliminate the need for multi-GPU tensor parallelism, dramatically simplifying deployment and reducing cost.

**Serving-time quantization** (AWQ, GPTQ, bitsandbytes NF4): weights are quantized offline; dequantization happens just-in-time during the forward pass. vLLM, TGI, and Ollama all support these formats natively.

#### 2.6.4 Speculative Decoding

Autoregressive generation is sequential: each token requires a full forward pass. This is inherently latency-bound even on powerful hardware.

**Speculative decoding** uses a small, fast **draft model** (e.g., 7B) to predict the next N tokens cheaply, then the large **verifier model** (e.g., 70B) checks all N in a single parallel forward pass:

1. Draft model generates tokens t₁, t₂, ..., tₙ speculatively.
2. Verifier runs one pass over all N tokens simultaneously.
3. Accepted tokens (those the verifier agrees with) are returned as output.
4. The first rejected token is replaced with the verifier's alternative; speculative generation restarts.

When the draft model's predictions are accurate (often 60–80% for domain-constrained text), the effective throughput of the verifier increases by the acceptance rate × N / 1, often yielding **2–4× latency reduction** for the verifier model with no quality loss.

**Effect on scaling**: speculative decoding reduces time-to-first-token and reduces per-token latency for the large model. Fewer GPU-seconds per request means each GPU pod handles more concurrent users, reducing the replica count needed for a given SLA.

---

## 3. Hands-On Lab

Open `labs/devops/day-08/` and work through the TODO markers in `starter.py`.

**Files:**

| File | Purpose |
|------|---------|
| `README.md` | Lab setup and instructions |
| `requirements.txt` | Python dependencies |
| `starter.py` | Scaffolded file with TODO markers |
| `solution.py` | Complete reference implementation |
| `deployment.yaml` | Kubernetes Deployment manifest |
| `service.yaml` | Kubernetes Service manifest |
| `hpa.yaml` | HorizontalPodAutoscaler manifest |
| `configmap.yaml` | ConfigMap manifest |

**What you will build:**

1. Write the four Kubernetes YAML manifests for the shared HR Assistant app.
2. Complete `starter.py` to parse and validate those manifests — asserting probes, resource limits, label selectors, and HPA target are all correctly wired.
3. Run a small concurrent load test against the shared app (in-process via TestClient) to measure requests/second and motivate why autoscaling is needed.

No real Kubernetes cluster is required. All validation is done by parsing YAML and testing the app in-process.

---

## 4. Self-Check Quiz

Answer each question, then check the answer.

---

**Q1.** What is the difference between a `readinessProbe` and a `livenessProbe`, and why does the distinction matter for a service that takes 90 seconds to load model weights?

<details>
<summary>Show answer</summary>

A **readinessProbe** controls whether a pod receives traffic from its Service. If it fails, the pod is removed from the endpoint list but is **not restarted**. A **livenessProbe** controls whether the container is considered alive; if it fails repeatedly, Kubernetes **restarts** the container.

For a service with a 90-second model-loading startup: if you only had a livenessProbe (no startupProbe), Kubernetes might restart the container before it ever finishes loading — an infinite restart loop. The correct approach is a **startupProbe** with a long enough `failureThreshold × periodSeconds` window to cover model loading, which blocks both readiness and liveness checks until the app declares itself ready. Once the startupProbe passes, the readinessProbe takes over for ongoing traffic gating and the livenessProbe for deadlock detection.

</details>

---

**Q2.** Why does CPU-based HPA often behave poorly as the sole autoscaling metric for GPU-accelerated LLM inference?

<details>
<summary>Show answer</summary>

GPU-accelerated LLM inference offloads virtually all compute to the GPU. The CPU pods typically manage HTTP parsing, batching, tokenization, and result serialization — tasks that may stay at 10–20% CPU utilization even when the GPU is saturated at 100% and the request queue is growing. The HPA sees low CPU and does not scale out, while users experience degraded latency or timeouts. The correct signal is **GPU utilization**, **request queue depth**, or **requests-per-second** — all custom metrics that require Prometheus Adapter or KEDA. CPU HPA is appropriate for CPU-bound services; LLM inference is VRAM-bandwidth-bound and compute-bound on the GPU, not the CPU.

</details>

---

**Q3.** What does `maxUnavailable: 0` mean in a rolling update strategy, and what is the trade-off?

<details>
<summary>Show answer</summary>

`maxUnavailable: 0` means Kubernetes will never terminate an old pod until a new one has passed its readiness probe and is confirmed available. The deployment will temporarily run `desired + maxSurge` pods. This guarantees zero-downtime for clients — requests always have at least the desired number of healthy pods available.

The trade-off is **resource cost and time**: you need enough cluster capacity to run the surge pods simultaneously, and updates take longer because each new pod must fully start and pass readiness before the next old pod is terminated. For slow-starting LLM pods (90s startup), a 4-replica update with `maxSurge: 1` could take 4 × 90s = 6 minutes. Accept this cost — the alternative is a service interruption.

</details>

---

**Q4.** A team ships a 70B parameter model in FP16 (140 GB VRAM required). They have 2× A100 80GB available. After applying INT4 quantization (AWQ), what VRAM requirement change should they expect, and what deployment simplification does this enable?

<details>
<summary>Show answer</summary>

INT4 quantization reduces weight storage to ~4 bits per parameter, roughly a 4× reduction from FP16 (16 bits). For a 70B model: `70B × 4 bits / 8 = ~35 GB` VRAM for weights alone, plus KV cache and activation buffers (~5–10 GB), totalling roughly 40–45 GB — fitting comfortably on a single A100 80GB.

The deployment simplification: instead of **tensor parallelism across 2 GPUs** (which requires NVLink or high-bandwidth interconnect, complex sharding logic in the serving framework, and failure-coupling between both GPUs), you can run the quantized model on a **single GPU**. This means: simpler Kubernetes pod spec (one GPU limit, no affinity rules for multi-GPU placement), lower hardware cost per replica, easier autoscaling (add individual GPU pods rather than pairs), and no inter-GPU communication latency on each forward pass. Quality trade-off is modest for large models.

</details>

---

**Q5.** Explain PagedAttention in your own words. What OS concept inspired it, and what scaling problem does it solve?

<details>
<summary>Show answer</summary>

PagedAttention is inspired by **virtual memory paging** in operating systems. In a traditional OS, physical RAM is divided into fixed-size pages, and processes are given pages on demand — they need not occupy contiguous memory and memory is not pre-allocated to the maximum address space.

Applied to KV caches: instead of pre-allocating a contiguous block of GPU VRAM equal to `max_context_length × model_dim × 2` (K and V) per sequence — even for sequences much shorter than the maximum — PagedAttention divides VRAM into fixed-size **blocks** and allocates them to sequences on demand. When a sequence finishes, its blocks are immediately freed and reused.

The scaling problem it solves: **KV cache memory fragmentation**. Naive allocation wastes 60–70% of VRAM because most sequences never reach max context length, yet memory is reserved. PagedAttention reduces waste to ~4%, allowing vLLM to batch far more concurrent sequences in the same VRAM — directly translating to higher throughput (more tokens/second per GPU) and lower cost per request.

</details>

---

**Q6.** Your Deployment uses `strategy.type: RollingUpdate` with `maxUnavailable: 0` and `maxSurge: 1`. A new pod is created but its `readinessProbe` never passes because the model-loading code has a bug. What happens to the old pods, and how do you recover?

<details>
<summary>Show answer</summary>

The old pods are **never terminated** — Kubernetes waits for the new pod to pass its readiness probe before replacing any old pods. With `maxUnavailable: 0`, Kubernetes will not remove an old pod until a replacement is confirmed healthy. The rollout stalls: `kubectl rollout status` reports "Waiting for rollout to finish" indefinitely. Traffic continues to flow to the old, working pods uninterrupted.

To recover: `kubectl rollout undo deployment/hr-assistant` immediately reverts to the previous ReplicaSet. The stalled new pod is terminated, and Kubernetes confirms the old pods are still healthy before closing out the rollout. This is the intended safety guarantee of `maxUnavailable: 0` — a bad deploy can never silently reduce capacity.

</details>

---

## 5. Concept Deep-Dive Q&A

Answer each question before revealing the answer.

---

**Q1.** A Kubernetes Deployment with `replicas: 3` has a pod whose `/health` endpoint starts returning HTTP 503 after a memory leak causes it to partially fail. Which probe fires, what happens to traffic routing, and is the pod restarted?

<details>
<summary>Show answer</summary>

The **readinessProbe** fires first (it runs more frequently and has a lower threshold). After `failureThreshold` consecutive failures, Kubernetes removes this pod's IP from the Service's endpoint slice — **no new traffic is routed to it**. The other two pods continue to receive traffic normally.

The **livenessProbe** continues to run. If `/health` keeps returning 503 beyond the liveness `failureThreshold`, Kubernetes marks the container as unhealthy and **restarts it** (the container, not the pod — the pod keeps its IP and scheduling metadata). After restart and a successful startup/readiness probe sequence, the pod re-enters the endpoint slice.

If the root cause is a memory leak, the restart may reclaim memory temporarily (new process), but without fixing the leak the cycle repeats. The correct fix is identifying and patching the leak, not relying on liveness restarts as a steady-state solution — though liveness restarts are a valid safety net.

</details>

---

**Q2.** You are designing HPA configuration for a text-generation service. The service is GPU-saturated at 40 concurrent requests but CPU is only at 25%. Describe a complete autoscaling architecture that would correctly scale this service.

<details>
<summary>Show answer</summary>

CPU-based HPA will not help here — the signal (CPU at 25%) does not reflect the actual bottleneck (GPU saturation). A complete architecture:

1. **Export GPU metrics**: instrument the serving process (vLLM, TGI) to export `gpu_utilization_percent` and `active_request_count` to Prometheus. Add a `/metrics` endpoint or sidecar Prometheus exporter.

2. **Prometheus Adapter or KEDA**: configure Kubernetes to consume these custom metrics. KEDA's `ScaledObject` is often simpler than the Prometheus Adapter for this use case.

3. **Scale on active_request_count or queue depth**: set a target of, say, 30 concurrent requests per replica (below the saturation point of 40). When `active_request_count / replicas > 30`, KEDA adds a replica.

4. **Cluster Autoscaler for GPU nodes**: GPU nodes are expensive and not always pre-provisioned. Configure the Cluster Autoscaler to provision additional GPU nodes from a node pool when pending GPU pods exist.

5. **minReplicas > 0**: always keep at least 1 replica warm. Cold-starting a GPU pod (pulling the model from object storage) takes minutes. Scale-to-zero is only viable if you can tolerate that latency.

6. **Startup optimisation**: use model pre-caching (pull image layers and model weights to node local storage) or shared storage mounts to reduce startup time, making scale-out more responsive.

</details>

---

**Q3.** What is the difference between speculative decoding and continuous batching? Could they be used together?

<details>
<summary>Show answer</summary>

They address different bottlenecks and operate at different levels:

**Continuous batching** is a **scheduling strategy**: instead of waiting for an entire batch of sequences to complete before accepting new requests, the serving engine fills available batch slots at every decoding step. It maximises GPU utilisation by keeping the hardware busy with real requests rather than idle between batches.

**Speculative decoding** is a **generation algorithm**: a small draft model proposes multiple tokens ahead; a large verifier model checks them in one parallel pass. It reduces the number of sequential forward passes required for a given output length, reducing latency for individual sequences.

They are **complementary and can run together**. A production serving engine (e.g., vLLM with speculative decoding enabled) can simultaneously:
- Use PagedAttention for efficient KV cache management.
- Use continuous batching to keep the verifier GPU busy at every step.
- Use speculative decoding to reduce per-sequence latency by verifying multiple draft tokens per verifier step.

The verifier model runs in continuous-batching mode with its real sequences; draft tokens for each sequence are proposed in parallel by the draft model and verified in a single augmented batch. vLLM's implementation of speculative decoding integrates directly with its continuous batching scheduler.

</details>

---

**Q4.** A DevOps engineer sets `resources.requests.memory: "4Gi"` and `resources.limits.memory: "4Gi"` for an LLM serving pod. During a traffic spike the pod gets OOM-killed. What likely went wrong, and how should the manifest be fixed?

<details>
<summary>Show answer</summary>

Several things could cause this:

1. **KV cache growth**: the serving framework pre-allocates KV cache based on `max_model_len` and batch size at startup. If this allocation plus model weights plus Python runtime overhead exceeds 4 GiB, the process is OOM-killed. The engineer may have only measured model weight size (`~3.5 GB for a 7B INT8 model`) and not accounted for KV cache and serving overhead.

2. **Traffic spike increases KV cache**: more concurrent requests mean more active KV cache entries. At low traffic the footprint may be fine; at peak it exceeds the limit.

3. **No headroom**: setting `requests == limits` (a "Guaranteed" QoS class) is good for predictability but means there is zero slack. A momentary spike kills the pod.

**Fixes**:
- Profile actual memory usage at peak load (`kubectl top pod` or Prometheus `container_memory_working_set_bytes`), including model weights + KV cache + overhead.
- Set `limits` to 20–30% above the observed peak, not equal to it.
- If the framework supports it, set `gpu_memory_utilization` (vLLM parameter) to cap KV cache allocation below 100% of VRAM, leaving headroom.
- Consider `requests` slightly below `limits` to allow the pod to use burst memory on nodes with slack capacity.
- Add a `readinessProbe` that checks a `/metrics` endpoint for memory pressure and fails early — allowing graceful load shedding before OOM-kill.

</details>

---

**Q5.** Explain the taint/toleration mechanism for GPU nodes. Why is it necessary, and what happens if you skip the taint?

<details>
<summary>Show answer</summary>

**Why taints are necessary**: GPU nodes are expensive (A100 nodes cost ~$3–10/hour on cloud providers). Without a taint, the Kubernetes scheduler treats GPU nodes like any other node. CPU-only workloads (web servers, background jobs, sidecars) will freely schedule onto GPU nodes — wasting expensive GPU capacity and potentially blocking LLM pods from scheduling because the node's CPU/memory is full.

**Mechanism**:
- A **taint** is a key-value-effect triple placed on a node: `kubectl taint nodes gpu-node-1 nvidia.com/gpu=present:NoSchedule`. Pods without a matching toleration cannot be scheduled there.
- A **toleration** in a pod spec allows that pod to be placed on a tainted node: it declares "I am aware of this taint and I can run here."
- A **nodeSelector** or **nodeAffinity** further restricts the pod to GPU nodes (without it, the pod tolerates the taint but might still land on a non-GPU node).

**Without the taint**: CPU workloads fill GPU nodes. New LLM pods become `Pending` because no GPU node has free CPU/memory slots, even though the GPU itself is idle. In a cost-sensitive environment this also means you are paying GPU prices for workloads that run fine on $0.10/hour CPU nodes.

**NVIDIA device plugin behaviour**: the plugin also adds `nvidia.com/gpu: "true"` as a label and may itself apply a taint — in managed Kubernetes (GKE, EKS, AKS) this is often done automatically by the GPU node pool configuration.

</details>

---

**Q6.** A team uses INT4 quantization (AWQ) for a production model. A stakeholder asks: "Did we make the model worse by doing this?" What is the technically accurate answer?

<details>
<summary>Show answer</summary>

The accurate answer is: **yes, but almost certainly not in a way that matters for your use case, and the trade-off is usually favourable**.

Technically, INT4 quantization introduces quantization error — rounding continuous floating-point weights to the nearest representable 4-bit value. This is a lossy compression. The model is mathematically different from the FP16 original.

However, empirically:
- **Large models (13B+) are highly robust to quantization**. Perplexity degradation with AWQ INT4 on models like Llama-3-70B is typically 0.1–0.5 points — within noise for most downstream tasks.
- **AWQ (Activation-aware Weight Quantization)** is specifically designed to identify and protect the ~1% of weights that are highly sensitive to precision (those activated by large-magnitude activations), reducing quality loss further.
- **For domain-constrained applications** (an HR assistant with factual, short answers), quantization effects are usually imperceptible to end users. Quality problems like hallucination come from the base model and retrieval, not from 4-bit precision.

The complete answer: run your evaluation suite (task-specific accuracy metrics, not just perplexity) on both FP16 and AWQ INT4 variants. If the difference is below your SLA threshold, ship the quantized model — you get 4× memory reduction, potentially single-GPU deployment, and significantly lower cost per request. Document the comparison so the decision is traceable.

</details>

---

**Q7.** What is the `selector` field in a Kubernetes Service, and what happens if it does not match the labels on the Deployment's pod template?

<details>
<summary>Show answer</summary>

The `selector` field in a Service is a **label query** that identifies which pods should receive traffic through this Service. Kubernetes continuously watches pods with matching labels and maintains an **Endpoints** (or EndpointSlice) object containing their IPs and ports.

If the selector does not match the pod template labels:
- The Endpoints object is **empty** — no pod IPs are enrolled.
- Traffic sent to the Service's ClusterIP has no backends to route to.
- Depending on the proxy mode (iptables/ipvs), connection attempts silently time out or are refused.
- No error is thrown at apply time — `kubectl apply` succeeds because the manifest is syntactically valid. The misconfiguration is only visible by inspecting `kubectl get endpoints hr-assistant-svc` and seeing an empty address list.

This is one of the most common Kubernetes misconfiguration bugs and is entirely silent without monitoring. The programmatic validation in today's lab (`assert deployment_selector == service_selector`) exists precisely to catch this class of error before deployment. In production, add an integration test that verifies `GET /health` responds after deploying both resources.

</details>

---

## 6. Further Reading

- [Kubernetes official docs — Deployments](https://kubernetes.io/docs/concepts/workloads/controllers/deployment/) — authoritative reference for rolling updates, revision history, and pausing deployments
- [Kubernetes official docs — Configure Liveness, Readiness, and Startup Probes](https://kubernetes.io/docs/tasks/configure-pod-container/configure-liveness-readiness-startup-probes/) — probe types, HTTP/TCP/exec, tuning parameters
- [Kubernetes official docs — Horizontal Pod Autoscaling](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/) — algorithm, stabilisation windows, custom metrics
- [NVIDIA k8s-device-plugin](https://github.com/NVIDIA/k8s-device-plugin) — GPU resource plugin for Kubernetes, time-slicing, MIG support
- [vLLM: Easy, Fast, and Cheap LLM Serving with PagedAttention (SOSP 2023)](https://arxiv.org/abs/2309.05852) — original PagedAttention paper; essential reading
- [Orca: A Distributed Serving System for Transformer-Based Generative Models (OSDI 2022)](https://www.usenix.org/conference/osdi22/presentation/yu) — continuous batching / iteration-level scheduling
- [KEDA — Kubernetes Event-Driven Autoscaling](https://keda.sh/docs/latest/) — scale on HTTP RPS, queue depth, Prometheus metrics
- [AWQ: Activation-aware Weight Quantization for LLM Compression and Acceleration](https://arxiv.org/abs/2306.00978) — INT4 quantization method with minimal quality loss
- [Fast Inference from Transformers via Speculative Decoding (Google, ICML 2023)](https://arxiv.org/abs/2211.17192) — original speculative decoding paper

---

## 7. Key Takeaways

- **Kubernetes provides the control plane for production LLM deployments**: Deployments manage desired state and rolling updates; Services provide stable networking; HPA handles demand-driven scaling.
- **Probe design is non-negotiable for LLM services**: startupProbes prevent premature liveness kills during slow model loading; readinessProbes gate traffic; livenessProbes detect deadlocks. Tune thresholds for your actual startup time.
- **Resource requests and limits must be measured, not guessed**: memory limits must cover model weights + KV cache + overhead with headroom, or you trade correctness for OOM-kills.
- **CPU HPA is usually wrong for GPU inference**: the real signals are GPU utilisation, queue depth, and active request count. Use KEDA or custom metrics HPA.
- **GPU scheduling requires the full trifecta**: NVIDIA device plugin (to expose GPUs as resources), node taints (to reserve GPU nodes), and pod tolerations + nodeSelector (to land LLM pods on GPU nodes).
- **Continuous batching and PagedAttention are multipliers**: they let the same GPU hardware serve dramatically more concurrent users, changing the unit economics of self-hosted inference.
- **Quantization is usually free money**: INT4/AWQ on large models (13B+) reduces VRAM requirements by 4×, often enabling single-GPU deployment, with quality loss that is empirically small on domain-constrained tasks.
- **Speculative decoding reduces per-request latency** by using a small draft model to speculatively generate tokens verified in parallel by the large model — effective when draft model accuracy is high.
- **Label selector mismatches are silent failures**: the Service becomes a black hole. Always validate selector consistency programmatically or with post-deploy smoke tests.
