# Speaker diarization 3.1 (self-host)

CPU FastAPI wrapper around `pyannote/speaker-diarization-3.1`. Same image runs on Docker Compose (EC2 POC) and Kubernetes.

## Hugging Face (required)

Accept the gates, then create a read token:

- https://hf.co/pyannote/segmentation-3.0
- https://hf.co/pyannote/speaker-diarization-3.1
- https://hf.co/settings/tokens

```bash
cp .env.example .env
# set HF_TOKEN=...
```

## Local / EC2 Compose

```bash
docker compose up --build -d
./scripts/smoke.sh http://127.0.0.1:8000
```

Listens on port 8000. One Uvicorn worker. Cache: Docker volume `hf-cache` → `/root/.cache/huggingface`.

## EC2 POC

Use **t3.large** (8 GiB). Smaller RAM will OOM. Ubuntu 22.04, ~30 GB disk, security group: SSH and 8000 from your IP only. User-data: `scripts/ec2-user-data.sh` (Docker + 4 GiB swap). Copy this repo to `/opt/diarization`, set `.env`, then `docker compose up --build -d`.

Stop or terminate the instance after the smoke test.

## Kubernetes

```bash
kubectl create secret generic hf-secret --from-literal=HF_TOKEN="$HF_TOKEN"
# load or push the same image, then:
kubectl apply -f k8s/pvc.yaml -f k8s/deployment.yaml -f k8s/service.yaml
# optional: k8s/ingress.yaml k8s/hpa.yaml
```

GPU: uncomment `nvidia.com/gpu` in `k8s/deployment.yaml` and install the NVIDIA device plugin. Keep replicas at 1 while the cache PVC is `ReadWriteOnce`.
