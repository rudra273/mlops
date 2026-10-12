"""Smoke test: send a random 1x3x224x224 tensor to Triton (V2 REST) via a local port-forward."""
import json, random, urllib.request

BASE = "http://localhost:8080"
MODEL = "resnet50"

def call(path, body=None):
    req = urllib.request.Request(BASE + path, data=None if body is None else json.dumps(body).encode(),
                                 headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return r.status, r.read()

print("ready:", call("/v2/health/ready")[0])
print("model:", json.loads(call(f"/v2/models/{MODEL}")[1])["name"])
random.seed(0)
data = [random.gauss(0, 1) for _ in range(3 * 224 * 224)]
body = {"inputs": [{"name": "data", "shape": [1, 3, 224, 224], "datatype": "FP32", "data": data}]}
out = json.loads(call(f"/v2/models/{MODEL}/infer", body)[1])["outputs"][0]
scores = out["data"]
top = sorted(range(len(scores)), key=lambda i: -scores[i])[:5]
print("output:", out["name"], out["shape"])
print("top5 class ids:", top)
