"""
Trello REST API wrapper layer.

Credentials are passed as input (credentials_path or credentials_json)
containing api_key and token — not from environment defaults for tool calls.
"""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

from app.core.exceptions import (
    TrelloError,
    TrelloValidationError,
    normalize_trello_error,
)

API_BASE = "https://api.trello.com/1"
DEFAULT_TIMEOUT_SEC = 30
DEFAULT_CARD_FIELDS = (
    "id,name,desc,closed,due,dueComplete,idList,idBoard,url,labels,pos"
)
DEFAULT_BOARD_FIELDS = "id,name,desc,closed,url,shortUrl,prefs"
DEFAULT_LIST_FIELDS = "id,name,closed,pos"
DEFAULT_MEMBER_FIELDS = "id,username,fullName,url,email"


def _request_timeout() -> int:
    raw = os.environ.get("TRELLO_HTTP_TIMEOUT_SEC", "").strip()
    if not raw:
        return DEFAULT_TIMEOUT_SEC
    try:
        return max(1, int(raw))
    except ValueError:
        return DEFAULT_TIMEOUT_SEC


def _credentials_dir() -> Path:
    raw = os.environ.get("TRELLO_CREDENTIALS_DIR", "").strip()
    if raw:
        return Path(raw).resolve()
    return Path(__file__).resolve().parent.parent.parent


def _resolve_credentials_path(credentials_path: str) -> Path:
    """Resolve credentials_path inside TRELLO_CREDENTIALS_DIR (path jail)."""
    base = _credentials_dir()
    candidate = Path(credentials_path)
    if not candidate.is_absolute():
        candidate = (base / candidate).resolve()
    else:
        candidate = candidate.resolve()
    try:
        candidate.relative_to(base)
    except ValueError as e:
        raise TrelloError(
            "credentials_path must be under TRELLO_CREDENTIALS_DIR",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    return candidate


def load_credentials_dict(
    credentials_path: Optional[str] = None,
    credentials_json: Optional[str] = None,
) -> dict:
    """Load and validate Trello credential dict from path or JSON string."""
    creds_dict: Optional[dict] = None
    try:
        if credentials_json:
            creds_dict = json.loads(credentials_json)
        elif credentials_path:
            path = _resolve_credentials_path(credentials_path)
            if not path.exists():
                raise TrelloError(
                    f"Credentials file not found: {credentials_path}",
                    error_code="CREDENTIALS_REQUIRED",
                    retryable=False,
                )
            with open(path, encoding="utf-8") as f:
                creds_dict = json.load(f)
    except TrelloError:
        raise
    except json.JSONDecodeError as e:
        raise TrelloError(
            "Invalid credentials JSON",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e
    except OSError as e:
        raise TrelloError(
            f"Failed to read credentials: {e}",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
            original_error=e,
        ) from e

    if not creds_dict:
        raise TrelloError(
            "Credentials required: provide credentials_path or credentials_json",
            error_code="CREDENTIALS_REQUIRED",
            retryable=False,
        )

    api_key = (creds_dict.get("api_key") or creds_dict.get("key") or "").strip()
    token = (creds_dict.get("token") or creds_dict.get("access_token") or "").strip()
    if not api_key or not token:
        raise TrelloError(
            "Credentials must include api_key and token",
            error_code="INVALID_CREDENTIALS",
            retryable=False,
        )
    return {"api_key": api_key, "token": token}


class TrelloService:
    """Trello REST API client."""

    def __init__(
        self,
        credentials_path: Optional[str] = None,
        credentials_json: Optional[str] = None,
    ):
        creds = load_credentials_dict(credentials_path, credentials_json)
        self._api_key = creds["api_key"]
        self._token = creds["token"]
        self._timeout = _request_timeout()

    def _auth_params(self) -> Dict[str, str]:
        return {"key": self._api_key, "token": self._token}

    def _request(
        self,
        method: str,
        path: str,
        *,
        params: Optional[Dict[str, Any]] = None,
        json_body: Optional[Dict[str, Any]] = None,
    ) -> Any:
        url = f"{API_BASE}{path}"
        merged = {**self._auth_params(), **(params or {})}
        try:
            resp = requests.request(
                method,
                url,
                params=merged,
                json=json_body,
                timeout=self._timeout,
            )
            if resp.status_code >= 400:
                detail = resp.text[:500] if resp.text else resp.reason
                raise normalize_trello_error(
                    Exception(f"HTTP {resp.status_code}: {detail}"),
                    status_code=resp.status_code,
                )
            if resp.status_code == 204 or not resp.content:
                return {}
            return resp.json()
        except TrelloError:
            raise
        except requests.RequestException as e:
            raise normalize_trello_error(e) from e

    def get_me(self) -> Dict[str, Any]:
        return self._request(
            "GET",
            "/members/me",
            params={"fields": DEFAULT_MEMBER_FIELDS},
        )

    def list_boards(
        self,
        *,
        filter_type: str = "open",
        limit: int = 50,
    ) -> List[Dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise TrelloValidationError("limit must be between 1 and 1000")
        boards = self._request(
            "GET",
            "/members/me/boards",
            params={
                "fields": DEFAULT_BOARD_FIELDS,
                "filter": filter_type,
                "limit": limit,
            },
        )
        return boards if isinstance(boards, list) else []

    def get_board(self, board_id: str) -> Dict[str, Any]:
        if not board_id.strip():
            raise TrelloValidationError("board_id is required")
        return self._request(
            "GET",
            f"/boards/{board_id.strip()}",
            params={"fields": DEFAULT_BOARD_FIELDS},
        )

    def list_lists(
        self,
        board_id: str,
        *,
        filter_type: str = "open",
    ) -> List[Dict[str, Any]]:
        if not board_id.strip():
            raise TrelloValidationError("board_id is required")
        lists = self._request(
            "GET",
            f"/boards/{board_id.strip()}/lists",
            params={"fields": DEFAULT_LIST_FIELDS, "filter": filter_type},
        )
        return lists if isinstance(lists, list) else []

    def list_cards(
        self,
        *,
        list_id: Optional[str] = None,
        board_id: Optional[str] = None,
        filter_type: str = "visible",
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        if not list_id and not board_id:
            raise TrelloValidationError("Provide list_id or board_id")
        if list_id and board_id:
            raise TrelloValidationError("Provide only one of list_id or board_id")
        if limit < 1 or limit > 1000:
            raise TrelloValidationError("limit must be between 1 and 1000")

        if list_id:
            path = f"/lists/{list_id.strip()}/cards"
        else:
            path = f"/boards/{board_id.strip()}/cards"

        cards = self._request(
            "GET",
            path,
            params={
                "fields": DEFAULT_CARD_FIELDS,
                "filter": filter_type,
                "limit": limit,
            },
        )
        return cards if isinstance(cards, list) else []

    def get_card(self, card_id: str) -> Dict[str, Any]:
        if not card_id.strip():
            raise TrelloValidationError("card_id is required")
        return self._request(
            "GET",
            f"/cards/{card_id.strip()}",
            params={"fields": DEFAULT_CARD_FIELDS},
        )

    def create_card(
        self,
        *,
        list_id: str,
        name: str,
        desc: str = "",
        due: Optional[str] = None,
        pos: str = "bottom",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        if not list_id.strip():
            raise TrelloValidationError("list_id is required")
        if not name.strip():
            raise TrelloValidationError("name is required")

        body: Dict[str, Any] = {
            "idList": list_id.strip(),
            "name": name.strip(),
            "desc": desc,
            "pos": pos,
        }
        if due:
            body["due"] = due

        if dry_run:
            return {"dry_run": True, "request_body": body}

        return self._request("POST", "/cards", params=body)

    def update_card(
        self,
        card_id: str,
        *,
        name: Optional[str] = None,
        desc: Optional[str] = None,
        due: Optional[str] = None,
        due_complete: Optional[bool] = None,
        closed: Optional[bool] = None,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        if not card_id.strip():
            raise TrelloValidationError("card_id is required")

        body: Dict[str, Any] = {}
        if name is not None:
            body["name"] = name
        if desc is not None:
            body["desc"] = desc
        if due is not None:
            body["due"] = due
        if due_complete is not None:
            body["dueComplete"] = str(due_complete).lower()
        if closed is not None:
            body["closed"] = str(closed).lower()

        if not body:
            raise TrelloValidationError("At least one field to update is required")

        if dry_run:
            return {"dry_run": True, "request_body": body, "card_id": card_id.strip()}

        return self._request("PUT", f"/cards/{card_id.strip()}", params=body)

    def move_card(
        self,
        card_id: str,
        list_id: str,
        *,
        pos: str = "bottom",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        if not card_id.strip():
            raise TrelloValidationError("card_id is required")
        if not list_id.strip():
            raise TrelloValidationError("list_id is required")

        body = {"idList": list_id.strip(), "pos": pos}
        if dry_run:
            return {"dry_run": True, "request_body": body, "card_id": card_id.strip()}

        return self._request("PUT", f"/cards/{card_id.strip()}", params=body)

    def archive_card(
        self,
        card_id: str,
        *,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        return self.update_card(card_id, closed=True, dry_run=dry_run)

    def add_comment(
        self,
        card_id: str,
        text: str,
        *,
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        if not card_id.strip():
            raise TrelloValidationError("card_id is required")
        if not text.strip():
            raise TrelloValidationError("text is required")

        body = {"text": text.strip()}
        if dry_run:
            return {"dry_run": True, "request_body": body, "card_id": card_id.strip()}

        return self._request(
            "POST",
            f"/cards/{card_id.strip()}/actions/comments",
            params=body,
        )

    def create_list(
        self,
        board_id: str,
        name: str,
        *,
        pos: str = "bottom",
        dry_run: bool = False,
    ) -> Dict[str, Any]:
        if not board_id.strip():
            raise TrelloValidationError("board_id is required")
        if not name.strip():
            raise TrelloValidationError("name is required")

        body = {"idBoard": board_id.strip(), "name": name.strip(), "pos": pos}
        if dry_run:
            return {"dry_run": True, "request_body": body}

        return self._request("POST", "/lists", params=body)

    def search_cards(
        self,
        query: str,
        *,
        board_ids: Optional[List[str]] = None,
        limit: int = 20,
    ) -> List[Dict[str, Any]]:
        if not query.strip():
            raise TrelloValidationError("query is required")
        if limit < 1 or limit > 1000:
            raise TrelloValidationError("limit must be between 1 and 1000")

        params: Dict[str, Any] = {
            "query": query.strip(),
            "modelTypes": "cards",
            "cards_limit": limit,
            "card_fields": DEFAULT_CARD_FIELDS,
        }
        if board_ids:
            params["idBoards"] = ",".join(b.strip() for b in board_ids if b.strip())

        result = self._request("GET", "/search", params=params)
        cards = result.get("cards", []) if isinstance(result, dict) else []
        return cards if isinstance(cards, list) else []
