# MLOps PoC: Triton on KServe (GKE)

Cluster: `gke-kserve`, zone `us-central1-a`, project `mlops-511108` (3x e2-standard-2, CPU only).

## Layout
| Path | Purpose |
|---|---|
| `k8s/00-cert-manager` | cert-manager (KServe webhook certs) |
| `k8s/01-kserve` | KServe controller + patch for RawDeployment mode |
| `k8s/02-kserve-runtimes` | Default serving runtimes (includes Triton) |
| `k8s/03-models-namespace` | `models` namespace for InferenceServices |
| `k8s/04-inference` | InferenceService manifests (ResNet-50 on Triton) |
| `models/resnet50` | Triton model repository (`config.pbtxt`, `1/model.onnx`) |
| `scripts` | Test client |
| `google-cloud-sdk/` | Local gcloud install (git-ignored) |

## Install order
`make cert-manager` -> `make kserve` -> `make runtimes` -> `make namespace`
