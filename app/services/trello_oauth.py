"""
Trello OAuth 1.0a (request token → authorize → access token).

Configuration via deployment env:
  TRELLO_API_KEY, TRELLO_API_SECRET, OAUTH_REDIRECT_URI, STUDIO_PUBLIC_URL
"""

from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import secrets
import time
import urllib.parse
from typing import Any, Dict, Optional, Tuple

import requests

from app.core.exceptions import TrelloError

TRELLO_REQUEST_TOKEN_URL = "https://trello.com/1/OAuthGetRequestToken"
TRELLO_AUTHORIZE_TOKEN_URL = "https://trello.com/1/OAuthAuthorizeToken"
TRELLO_ACCESS_TOKEN_URL = "https://trello.com/1/OAuthGetAccessToken"
TRELLO_API_BASE = "https://api.trello.com/1"
DEFAULT_SCOPES = "read,write"

_pending: Dict[str, Dict[str, Any]] = {}


def _purge_pending() -> None:
    now = time.time()
    expired = [k for k, v in _pending.items() if now - v.get("created_at", 0) > 600]
    for k in expired:
        _pending.pop(k, None)


def _api_key() -> str:
    key = os.environ.get("TRELLO_API_KEY", "").strip()
    if not key:
        raise TrelloError(
            "TRELLO_API_KEY is required",
            error_code="OAUTH_CONFIG",
            retryable=False,
        )
    return key


def _api_secret() -> str:
    secret = os.environ.get("TRELLO_API_SECRET", "").strip()
    if not secret:
        raise TrelloError(
            "TRELLO_API_SECRET is required",
            error_code="OAUTH_CONFIG",
            retryable=False,
        )
    return secret


def oauth_redirect_uri() -> str:
    uri = os.environ.get("OAUTH_REDIRECT_URI", "").strip()
    if uri:
        return uri
    public = os.environ.get("TRELLO_MCP_PUBLIC_URL", "").strip().rstrip("/")
    if public:
        return f"{public}/oauth/callback"
    raise TrelloError(
        "OAUTH_REDIRECT_URI or TRELLO_MCP_PUBLIC_URL is required",
        error_code="OAUTH_CONFIG",
        retryable=False,
    )


def studio_public_url() -> str:
    url = os.environ.get("STUDIO_PUBLIC_URL", "http://localhost:5173").strip().rstrip("/")
    return url


def oauth_info() -> Dict[str, str]:
    return {
        "redirect_uri": oauth_redirect_uri(),
        "studio_public_url": studio_public_url(),
        "scopes": DEFAULT_SCOPES,
    }


def _oauth1_percent_encode(value: str) -> str:
    return urllib.parse.quote(str(value), safe="")


def _oauth1_nonce() -> str:
    return base64.b64encode(secrets.token_bytes(16)).decode("ascii")


def _oauth1_params(consumer_key: str, token: str = "") -> Dict[str, str]:
    params = {
        "oauth_consumer_key": consumer_key,
        "oauth_signature_method": "HMAC-SHA1",
        "oauth_timestamp": str(int(time.time())),
        "oauth_nonce": _oauth1_nonce(),
        "oauth_version": "1.0",
    }
    if token:
        params["oauth_token"] = token
    return params


def _oauth1_signature(
    method: str, url: str, params: Dict[str, str], signing_key: str
) -> str:
    pairs = sorted(f"{_oauth1_percent_encode(k)}={_oauth1_percent_encode(v)}" for k, v in params.items())
    param_string = "&".join(pairs)
    base = "&".join(
        [
            method.upper(),
            _oauth1_percent_encode(url),
            _oauth1_percent_encode(param_string),
        ]
    )
    digest = hmac.new(signing_key.encode("utf-8"), base.encode("utf-8"), hashlib.sha1).digest()
    return base64.b64encode(digest).decode("ascii")


def _post_oauth(url: str, params: Dict[str, str]) -> Dict[str, str]:
    resp = requests.post(url, data=params, timeout=30)
    if resp.status_code >= 400:
        raise TrelloError(
            f"OAuth request failed: HTTP {resp.status_code}",
            error_code="OAUTH_ERROR",
            retryable=resp.status_code >= 500,
            original_error=resp.text[:200],
        )
    parsed = urllib.parse.parse_qs(resp.text)
    return {k: v[0] if v else "" for k, v in parsed.items()}


def _get_request_token(api_key: str, api_secret: str, callback: str) -> Tuple[str, str]:
    params = _oauth1_params(api_key)
    params["oauth_callback"] = callback
    params["oauth_signature"] = _oauth1_signature(
        "POST", TRELLO_REQUEST_TOKEN_URL, params, f"{api_secret}&"
    )
    data = _post_oauth(TRELLO_REQUEST_TOKEN_URL, params)
    token = data.get("oauth_token", "")
    secret = data.get("oauth_token_secret", "")
    if not token or not secret:
        raise TrelloError(
            "Trello request token missing fields",
            error_code="OAUTH_ERROR",
            retryable=False,
        )
    return token, secret


def _get_access_token(
    api_key: str,
    api_secret: str,
    request_token: str,
    request_secret: str,
    verifier: str,
) -> str:
    params = _oauth1_params(api_key, request_token)
    params["oauth_verifier"] = verifier
    params["oauth_signature"] = _oauth1_signature(
        "POST",
        TRELLO_ACCESS_TOKEN_URL,
        params,
        f"{api_secret}&{_oauth1_percent_encode(request_secret)}",
    )
    data = _post_oauth(TRELLO_ACCESS_TOKEN_URL, params)
    token = data.get("oauth_token", "")
    if not token:
        raise TrelloError(
            "Trello access token missing oauth_token",
            error_code="OAUTH_ERROR",
            retryable=False,
        )
    return token


def _fetch_username(api_key: str, token: str) -> str:
    resp = requests.get(
        f"{TRELLO_API_BASE}/members/me",
        params={"key": api_key, "token": token, "fields": "username,fullName"},
        timeout=30,
    )
    if resp.status_code >= 400:
        return ""
    info = resp.json()
    return info.get("fullName") or info.get("username") or ""


def oauth_start(user_id: str) -> str:
    """Begin OAuth; return Trello authorize URL."""
    if not user_id.strip():
        raise TrelloError("user_id required", error_code="VALIDATION_ERROR", retryable=False)
    _purge_pending()
    api_key = _api_key()
    api_secret = _api_secret()
    redirect = oauth_redirect_uri()
    req_token, req_secret = _get_request_token(api_key, api_secret, redirect)
    _pending[req_token] = {
        "user_id": user_id.strip(),
        "request_token_secret": req_secret,
        "created_at": time.time(),
    }
    q = urllib.parse.urlencode(
        {
            "oauth_token": req_token,
            "name": "DatumBridge Studio",
            "scope": DEFAULT_SCOPES,
            "expiration": "never",
        }
    )
    return f"{TRELLO_AUTHORIZE_TOKEN_URL}?{q}"


def oauth_complete(request_token: str, verifier: str) -> Dict[str, Any]:
    """Exchange verifier for access token; return vault payload metadata."""
    _purge_pending()
    pending = _pending.pop(request_token, None)
    if not pending or not pending.get("user_id"):
        raise TrelloError(
            "invalid or expired trello oauth state",
            error_code="OAUTH_STATE",
            retryable=False,
        )
    api_key = _api_key()
    api_secret = _api_secret()
    access_token = _get_access_token(
        api_key,
        api_secret,
        request_token,
        pending["request_token_secret"],
        verifier,
    )
    account_label = _fetch_username(api_key, access_token)
    bundle = {"api_key": api_key, "token": access_token}
    return {
        "user_id": pending["user_id"],
        "account_label": account_label,
        "credentials_json": json.dumps(bundle),
        "bundle": bundle,
    }
