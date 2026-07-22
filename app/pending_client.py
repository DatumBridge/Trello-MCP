"""OAuth pending state stored in datumbridge-mcp (survives trello-mcp restarts/replicas)."""

from __future__ import annotations

import logging
import os
from typing import Optional, Tuple

import requests

from app.core.exceptions import TrelloError
from app.vault_client import mcp_service_headers, resolve_mcp_base_url

logger = logging.getLogger(__name__)


def save_oauth_pending(request_token: str, user_id: str, request_secret: str) -> None:
    url = f"{resolve_mcp_base_url()}/api/v1/internal/credentials/trello/pending"
    body = {
        "request_token": request_token,
        "user_id": user_id,
        "request_token_secret": request_secret,
    }
    try:
        resp = requests.post(url, json=body, headers=mcp_service_headers(), timeout=15)
    except requests.RequestException as exc:
        logger.warning("failed to persist trello oauth pending to MCP: %s", exc)
        return
    if resp.status_code >= 400:
        logger.warning(
            "MCP trello pending save failed: HTTP %s %s",
            resp.status_code,
            resp.text[:200],
        )


def consume_oauth_pending(request_token: str) -> Optional[Tuple[str, str]]:
    url = f"{resolve_mcp_base_url()}/api/v1/internal/credentials/trello/pending/consume"
    body = {"request_token": request_token}
    try:
        resp = requests.post(url, json=body, headers=mcp_service_headers(), timeout=15)
    except requests.RequestException as exc:
        raise TrelloError(
            f"failed to load oauth pending state: {exc}",
            error_code="OAUTH_STATE",
            retryable=True,
        ) from exc
    if resp.status_code == 404:
        return None
    if resp.status_code >= 400:
        raise TrelloError(
            f"oauth pending consume failed: HTTP {resp.status_code}",
            error_code="OAUTH_STATE",
            retryable=resp.status_code >= 500,
            original_error=resp.text[:200],
        )
    data = resp.json()
    user_id = (data.get("user_id") or "").strip()
    secret = (data.get("request_token_secret") or "").strip()
    if not user_id or not secret:
        return None
    return user_id, secret
