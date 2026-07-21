"""Trello OAuth routes for Studio Integrations (credentials live on this MCP deployment)."""

from __future__ import annotations

import logging
import os
import urllib.parse

from starlette.requests import Request
from starlette.responses import JSONResponse, RedirectResponse

from app.core.exceptions import TrelloError
from app.services.trello_oauth import oauth_complete, oauth_info, oauth_start, studio_public_url
from app.vault_client import save_trello_credentials

logger = logging.getLogger(__name__)


def _service_auth_ok(request: Request) -> bool:
    expected = os.environ.get("MCP_SERVICE_API_KEY", "").strip()
    if not expected:
        return False
    got = request.headers.get("X-API-Key", "").strip()
    if got == expected:
        return True
    auth = request.headers.get("Authorization", "").strip()
    return auth == f"Bearer {expected}"


def _resolve_user_id(request: Request) -> str:
    for header in ("X-User-ID", "X-DatumBridge-User-Id"):
        val = request.headers.get(header, "").strip()
        if val:
            return val
    return request.query_params.get("user_id", "").strip()


async def oauth_start_route(request: Request):
    """Start OAuth (called by datumbridge-mcp proxy with service auth + user id)."""
    if not _service_auth_ok(request):
        return JSONResponse(
            {"error_code": "UNAUTHORIZED", "error_message": "service authentication required"},
            status_code=401,
        )
    user_id = _resolve_user_id(request)
    if not user_id:
        return JSONResponse(
            {"error_code": "VALIDATION_ERROR", "error_message": "X-User-ID required"},
            status_code=400,
        )
    try:
        auth_url = oauth_start(user_id)
        if request.query_params.get("format") == "redirect":
            return RedirectResponse(auth_url, status_code=302)
        return JSONResponse({"auth_url": auth_url, "provider": "trello"})
    except TrelloError as e:
        logger.error("oauth start failed: %s", e.error_code)
        return JSONResponse(e.to_dict(), status_code=503)


async def oauth_callback(request: Request):
    """Trello OAuth 1.0a callback — save vault and redirect to Studio Integrations."""
    studio = studio_public_url()
    fail = lambda reason: RedirectResponse(  # noqa: E731
        f"{studio}/account/integrations?trello=error&reason={urllib.parse.quote(reason)}",
        status_code=302,
    )

    request_token = request.query_params.get("oauth_token", "").strip()
    verifier = request.query_params.get("oauth_verifier", "").strip()
    if not request_token or not verifier:
        return fail("missing_params")

    try:
        result = oauth_complete(request_token, verifier)
        save_trello_credentials(
            result["user_id"],
            result["credentials_json"],
            result.get("account_label"),
        )
        return RedirectResponse(
            f"{studio}/account/integrations?trello=connected",
            status_code=302,
        )
    except TrelloError as e:
        logger.error("oauth callback failed: %s", e.error_code)
        return fail(e.error_code.lower())


async def oauth_info_route(_request: Request):
    try:
        return JSONResponse(oauth_info())
    except TrelloError as e:
        return JSONResponse(e.to_dict(), status_code=503)
