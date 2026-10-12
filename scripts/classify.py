"""Classify an image with the resnet50 model on Triton (V2 REST) via a local port-forward."""
import json, os, sys, urllib.request
import numpy as np
from PIL import Image

BASE, MODEL = os.environ.get("TRITON_URL", "http://localhost:8080"), "resnet50"
MEAN = np.array([0.485, 0.456, 0.406], dtype=np.float32)
STD = np.array([0.229, 0.224, 0.225], dtype=np.float32)

def preprocess(path):
    img = Image.open(path).convert("RGB")
    w, h = img.size
    s = 256 / min(w, h)
    img = img.resize((round(w * s), round(h * s)), Image.BILINEAR)
    w, h = img.size
    l, t = (w - 224) // 2, (h - 224) // 2
    img = img.crop((l, t, l + 224, t + 224))
    x = (np.asarray(img, dtype=np.float32) / 255.0 - MEAN) / STD
    return x.transpose(2, 0, 1)[None]  # 1x3x224x224

def infer(x):
    body = {"inputs": [{"name": "data", "shape": list(x.shape), "datatype": "FP32", "data": x.flatten().tolist()}]}
    req = urllib.request.Request(f"{BASE}/v2/models/{MODEL}/infer", json.dumps(body).encode(),
                                 {"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=60) as r:
        return np.array(json.load(r)["outputs"][0]["data"], dtype=np.float32)

if __name__ == "__main__":
    labels = open("samples/imagenet_classes.txt").read().splitlines()
    for p in sys.argv[1:] or ["samples/dog.jpg"]:
        logits = infer(preprocess(p))
        probs = np.exp(logits - logits.max()); probs /= probs.sum()
        print(p)
        for i in np.argsort(-probs)[:5]:
            print(f"  {probs[i]*100:5.1f}%  {labels[i]}")
