#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-mcp-tools}"
IMAGE_REPO="${IMAGE_REPO:-trello-mcp}"
IMAGE_TAG="${IMAGE_TAG:-local}"
SKIP_BUILD=0
SKIP_PUSH=1
SKIP_SMOKE=0

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_PATH="${ROOT_DIR}/k8s/deployment.yaml"

usage() {
  cat <<'EOF'
Usage: ./k8s-deploy.sh [--image-repo <repo>] [--image-tag <tag>] [--namespace <ns>] [--skip-build] [--push] [--skip-smoke]
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-repo) IMAGE_REPO="${2:-}"; shift 2 ;;
    --image-tag) IMAGE_TAG="${2:-}"; shift 2 ;;
    --namespace) NAMESPACE="${2:-}"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --push) SKIP_PUSH=0; shift ;;
    --skip-smoke) SKIP_SMOKE=1; shift ;;
    -h|--help) usage; exit 0 ;;
    *) echo "Unknown argument: $1"; usage; exit 1 ;;
  esac
done

MCP_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"
cd "${ROOT_DIR}"

if [[ ${SKIP_BUILD} -eq 0 ]]; then
  echo "[1/3] Building ${MCP_IMAGE}..."
  docker build -t "${MCP_IMAGE}" .
else
  echo "[1/3] Skipping build"
fi

if [[ ${SKIP_PUSH} -eq 0 ]]; then
  echo "[2/3] Pushing ${MCP_IMAGE}..."
  docker push "${MCP_IMAGE}"
else
  echo "[2/3] Skipping push"
fi

echo "[3/3] Applying manifests..."
kubectl create namespace "${NAMESPACE}" 2>/dev/null || true
sed \
  -e "s|namespace: mcp-tools|namespace: ${NAMESPACE}|g" \
  -e "s|image: trello-mcp:local|image: ${MCP_IMAGE}|g" \
  "${MANIFEST_PATH}" | kubectl apply -f -

kubectl -n "${NAMESPACE}" rollout status deploy/trello-mcp-main --timeout=300s

if [[ ${SKIP_SMOKE} -eq 0 ]]; then
  kubectl -n "${NAMESPACE}" run trello-mcp-smoke --rm -i --restart=Never --image=curlimages/curl -- \
    curl -fsS "http://trello-mcp-main:8000/health"
fi

echo "Done. MCP: http://trello-mcp-main.${NAMESPACE}.svc.cluster.local:8000/mcp/"
echo "Registry id: mcpServer=trello"
