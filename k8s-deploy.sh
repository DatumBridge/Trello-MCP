#!/usr/bin/env bash
set -euo pipefail

NAMESPACE="${NAMESPACE:-mcp-tools}"
IMAGE_REPO="${IMAGE_REPO:-trello-mcp}"
IMAGE_TAG="${IMAGE_TAG:-local}"
SKIP_BUILD=0
SKIP_PUSH=1
SKIP_SMOKE=0
CREATE_SECRET=1

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MANIFEST_PATH="${ROOT_DIR}/k8s/deployment.yaml"
ENV_FILE="${ROOT_DIR}/.env"

while [[ $# -gt 0 ]]; do
  case "$1" in
    --image-repo) IMAGE_REPO="${2:-}"; shift 2 ;;
    --image-tag) IMAGE_TAG="${2:-}"; shift 2 ;;
    --namespace) NAMESPACE="${2:-}"; shift 2 ;;
    --skip-build) SKIP_BUILD=1; shift ;;
    --push) SKIP_PUSH=0; shift ;;
    --skip-smoke) SKIP_SMOKE=1; shift ;;
    --skip-secret) CREATE_SECRET=0; shift ;;
    -h|--help) echo "Usage: ./k8s-deploy.sh [--skip-build] [--push]"; exit 0 ;;
    *) echo "Unknown argument: $1"; exit 1 ;;
  esac
done

MCP_IMAGE="${IMAGE_REPO}:${IMAGE_TAG}"
cd "${ROOT_DIR}"

if [[ ${SKIP_BUILD} -eq 0 ]]; then
  echo "[1/4] Building ${MCP_IMAGE}..."
  docker build -t "${MCP_IMAGE}" .
else
  echo "[1/4] Skipping build"
fi

if [[ ${SKIP_PUSH} -eq 0 ]]; then
  echo "[2/4] Pushing ${MCP_IMAGE}..."
  docker push "${MCP_IMAGE}"
else
  echo "[2/4] Skipping push"
fi

echo "[3/4] Ensuring namespace + secret..."
kubectl create namespace "${NAMESPACE}" 2>/dev/null || true

if [[ ${CREATE_SECRET} -eq 1 ]]; then
  if [[ ! -f "${ENV_FILE}" ]]; then
    echo "Error: ${ENV_FILE} not found. Copy .env.example to .env and set TRELLO_API_KEY/SECRET."
    exit 1
  fi
  TMP_ENV="$(mktemp)"
  trap 'rm -f "${TMP_ENV}"' EXIT
  grep -E '^(TRELLO_API_KEY|TRELLO_API_SECRET|STUDIO_PUBLIC_URL|OAUTH_REDIRECT_URI|MCP_SERVICE_API_KEY|CREDENTIAL_VAULT_API_URL|TRELLO_MCP_PUBLIC_URL|DATUMBRIDGE_MCP_NAMESPACE|DATUMBRIDGE_MCP_SERVICE|DATUMBRIDGE_MCP_PORT)=' \
    "${ENV_FILE}" | grep -v '^=*$' > "${TMP_ENV}" || true
  if [[ ! -s "${TMP_ENV}" ]]; then
    echo "Error: set TRELLO_API_KEY and TRELLO_API_SECRET in .env"
    exit 1
  fi
  if ! grep -q '^CREDENTIAL_VAULT_API_URL=' "${TMP_ENV}"; then
    echo "CREDENTIAL_VAULT_API_URL=http://datumbridge-mcp.datumbridge-adk-db.svc.cluster.local:8081" >> "${TMP_ENV}"
  fi
  if ! grep -q '^STUDIO_PUBLIC_URL=' "${TMP_ENV}"; then
    echo "STUDIO_PUBLIC_URL=http://localhost:30080" >> "${TMP_ENV}"
  fi
  kubectl -n "${NAMESPACE}" create secret generic trello-mcp-main-secret \
    --from-env-file="${TMP_ENV}" \
    --dry-run=client -o yaml | kubectl apply -f -
fi

echo "[4/4] Applying manifests..."
sed \
  -e "s|namespace: mcp-tools|namespace: ${NAMESPACE}|g" \
  -e "s|image: trello-mcp:local|image: ${MCP_IMAGE}|g" \
  "${MANIFEST_PATH}" | kubectl apply -f -

kubectl -n "${NAMESPACE}" rollout status deploy/trello-mcp-main --timeout=300s

NODE_PORT="$(kubectl -n "${NAMESPACE}" get svc trello-mcp-main -o jsonpath='{.spec.ports[0].nodePort}')"
REDIRECT_URI="http://127.0.0.1:${NODE_PORT}/oauth/callback"

kubectl -n "${NAMESPACE}" patch secret trello-mcp-main-secret --type merge -p \
  "{\"stringData\":{\"OAUTH_REDIRECT_URI\":\"${REDIRECT_URI}\",\"TRELLO_MCP_PUBLIC_URL\":\"http://127.0.0.1:${NODE_PORT}\"}}" >/dev/null || true
kubectl -n "${NAMESPACE}" set env deployment/trello-mcp-main \
  "OAUTH_REDIRECT_URI=${REDIRECT_URI}" \
  "TRELLO_MCP_PUBLIC_URL=http://127.0.0.1:${NODE_PORT}" >/dev/null || true
kubectl -n "${NAMESPACE}" rollout status deploy/trello-mcp-main --timeout=180s

if [[ ${SKIP_SMOKE} -eq 0 ]]; then
  kubectl -n "${NAMESPACE}" run trello-mcp-smoke --rm -i --restart=Never --image=curlimages/curl -- \
    curl -fsS "http://trello-mcp-main:8000/health"
fi

echo "Done."
echo "  In-cluster MCP: http://trello-mcp-main.${NAMESPACE}.svc.cluster.local:8000/mcp/"
echo "  OAuth callback: ${REDIRECT_URI}"
echo "  Register that callback URL in Trello Power-Up admin."
echo "  OAuth info:     http://127.0.0.1:${NODE_PORT}/oauth/info"
