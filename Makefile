# Usage: make <target>. Requires google-cloud-sdk/bin on PATH and kubectl pointed at gke-kserve.
CLUSTER ?= gke-kserve
ZONE    ?= us-central1-a

.PHONY: creds cert-manager kserve runtimes namespace status
creds:
	gcloud container clusters get-credentials $(CLUSTER) --zone $(ZONE)

cert-manager:
	kubectl apply --server-side -k k8s/00-cert-manager
	kubectl -n cert-manager rollout status deploy/cert-manager-webhook --timeout=300s

kserve:
	kubectl apply --server-side -k k8s/01-kserve
	kubectl -n kserve rollout status deploy/kserve-controller-manager --timeout=300s

runtimes:
	kubectl apply --server-side -k k8s/02-kserve-runtimes

namespace:
	kubectl apply -f k8s/03-models-namespace/namespace.yaml

status:
	kubectl get pods -A | grep -E "cert-manager|kserve|models"
	kubectl get clusterservingruntimes
