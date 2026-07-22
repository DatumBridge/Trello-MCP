"""Store Trello credentials in DatumBridge MCP credential vault (service-to-service)."""

from __future__ import annotations

import os
from typing import Dict, Optional

import requests

from app.core.exceptions import TrelloError


def resolve_mcp_base_url() -> str:
    """Resolve datumbridge-mcp base URL for in-cluster service calls."""
    base = os.environ.get("CREDENTIAL_VAULT_API_URL", "").strip().rstrip("/")
    if not base:
        base = os.environ.get("DATUMBRIDGE_MCP_URL", "").strip().rstrip("/")
    if not base:
        ns = os.environ.get("DATUMBRIDGE_MCP_NAMESPACE", "datumbridge-adk-db").strip()
        svc = os.environ.get("DATUMBRIDGE_MCP_SERVICE", "datumbridge-mcp").strip()
        port = os.environ.get("DATUMBRIDGE_MCP_PORT", "8081").strip() or "8081"
        base = f"http://{svc}.{ns}.svc.cluster.local:{port}"
    return base


def mcp_service_headers() -> Dict[str, str]:
    key = os.environ.get("MCP_SERVICE_API_KEY", "").strip()
    if not key:
        raise TrelloError(
            "MCP_SERVICE_API_KEY is required for vault save",
            error_code="VAULT_CONFIG",
            retryable=False,
        )
    return {
        "Content-Type": "application/json",
        "X-API-Key": key,
    }


def _vault_base_url() -> str:
    return resolve_mcp_base_url()


def _service_api_key() -> str:
    key = os.environ.get("MCP_SERVICE_API_KEY", "").strip()
    if not key:
        raise TrelloError(
            "MCP_SERVICE_API_KEY is required for vault save",
            error_code="VAULT_CONFIG",
            retryable=False,
        )
    return key


def save_trello_credentials(
    user_id: str,
    credentials_json: str,
    account_label: Optional[str] = None,
) -> None:
    url = f"{_vault_base_url()}/api/v1/internal/credentials/trello"
    headers = mcp_service_headers()
    body = {
        "user_id": user_id,
        "credentials_json": credentials_json,
        "account_label": account_label or "",
    }
    try:
        resp = requests.post(url, json=body, headers=headers, timeout=30)
    except requests.RequestException as exc:
        raise TrelloError(
            f"vault save unreachable at {_vault_base_url()}: {exc}",
            error_code="VAULT_ERROR",
            retryable=True,
        ) from exc
    if resp.status_code >= 400:
        raise TrelloError(
            f"vault save failed: HTTP {resp.status_code} at {_vault_base_url()}",
            error_code="VAULT_ERROR",
            retryable=resp.status_code >= 500,
            original_error=resp.text[:200],
        )
