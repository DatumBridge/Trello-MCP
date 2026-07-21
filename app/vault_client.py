"""Store Trello credentials in DatumBridge MCP credential vault (service-to-service)."""

from __future__ import annotations

import os
from typing import Optional

import requests

from app.core.exceptions import TrelloError


def _vault_base_url() -> str:
    base = os.environ.get("CREDENTIAL_VAULT_API_URL", "").strip().rstrip("/")
    if not base:
        base = os.environ.get("DATUMBRIDGE_MCP_URL", "").strip().rstrip("/")
    if not base:
        raise TrelloError(
            "CREDENTIAL_VAULT_API_URL or DATUMBRIDGE_MCP_URL is required for vault save",
            error_code="VAULT_CONFIG",
            retryable=False,
        )
    return base


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
    headers = {
        "Content-Type": "application/json",
        "X-API-Key": _service_api_key(),
    }
    body = {
        "user_id": user_id,
        "credentials_json": credentials_json,
        "account_label": account_label or "",
    }
    resp = requests.post(url, json=body, headers=headers, timeout=30)
    if resp.status_code >= 400:
        raise TrelloError(
            f"vault save failed: HTTP {resp.status_code}",
            error_code="VAULT_ERROR",
            retryable=resp.status_code >= 500,
            original_error=resp.text[:200],
        )
