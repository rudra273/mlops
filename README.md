# MLOps PoC: ResNet-50 on Triton via KServe (GKE)

ResNet-50 (ONNX) image classifier served by NVIDIA Triton Inference Server on KServe, running CPU-only on GKE.

- Project `mlops-511108`, cluster `gke-kserve`, zone `us-central1-a` (3x e2-standard-2)
- Model: ResNet-50 v1-12 (ONNX), 1000 ImageNet classes, input `data` `[N,3,224,224]` FP32, output `resnetv17_dense0_fwd` `[N,1000]`
- Protocol: KServe V2 (REST), model name `resnet50`

## Try it

You need the endpoint address (`<host>:<port>`) from the maintainer.

### 1. Check the service

```bash
export TRITON_URL=http://<host>:<port>

curl $TRITON_URL/v2/health/ready -i      # expect HTTP 200
curl $TRITON_URL/v2/models/resnet50      # model metadata
```

### 2. Classify an image

```bash
git clone <this-repo> && cd mlops
python3 -m venv .venv
.venv/bin/pip install numpy pillow

# bundled sample image
.venv/bin/python scripts/classify.py samples/dog.jpg

# your own image(s)
.venv/bin/python scripts/classify.py path/to/photo.jpg other.png
```

Example output:

```
samples/dog.jpg
   94.7%  Samoyed
    2.0%  Pomeranian
    ...
```

`scripts/classify.py` resizes to 256, center-crops to 224, applies ImageNet normalization, calls `POST /v2/models/resnet50/infer` and prints the top 5 classes. It reads the endpoint from `TRITON_URL` (default `http://localhost:8080`).

### Raw API call

```bash
curl -X POST $TRITON_URL/v2/models/resnet50/infer \
  -H "Content-Type: application/json" \
  -d '{"inputs":[{"name":"data","shape":[1,3,224,224],"datatype":"FP32","data":[...150528 floats...]}]}'
```

Use `scripts/smoke_test.py` for a quick end-to-end check with a random tensor (it targets `http://localhost:8080`; edit `BASE` or use a port-forward).

### No public endpoint? Use port-forward

With cluster access (`make creds`):

```bash
kubectl -n models port-forward svc/resnet50-predictor 8080:80
.venv/bin/python scripts/classify.py samples/dog.jpg     # TRITON_URL defaults to localhost:8080
```

## Layout

| Path | Purpose |
|---|---|
| `k8s/00-cert-manager` | cert-manager (KServe webhook certs) |
| `k8s/01-kserve` | KServe controller, `kserve` namespace, RawDeployment patch |
| `k8s/02-kserve-runtimes` | Default serving runtimes (includes Triton) |
| `k8s/03-models-namespace` | `models` namespace |
| `k8s/04-inference` | InferenceService for ResNet-50 on Triton |
| `k8s/05-expose` | NodePort service (30080) for public access |
| `models/resnet50` | Triton model repository (`config.pbtxt`, `1/model.onnx`; the `.onnx` is git-ignored) |
| `samples` | Test image and ImageNet class labels |
| `scripts` | `classify.py` (real images), `smoke_test.py` (synthetic input) |

## Deploy from scratch

```bash
make creds cert-manager kserve runtimes namespace    # `runtimes` may report a harmless LLM-config webhook error; Triton is still installed
gcloud storage cp -r models/resnet50 gs://<bucket>/triton/    # storageUri must point at the repository ROOT
kubectl apply -f k8s/04-inference/resnet50-triton.yaml
kubectl apply -f k8s/05-expose/resnet50-nodeport.yaml
```

The node service account needs `roles/storage.objectViewer` on the bucket. For public access, open `tcp:30080` in a GCP firewall rule.

## Notes

- Raw-deployment mode (no Knative/Istio): no scale-to-zero, and the `isvc` URL shown by KServe is a placeholder.
- Region quotas are small (4 external IPs, 8 E2 vCPUs, 250 GB SSD), so use standard disks.
- Cost: about $0.10/hour for 3 nodes. Delete the cluster when idle: `gcloud container clusters delete gke-kserve --zone us-central1-a`.
