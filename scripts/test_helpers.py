#!/usr/bin/env python3
"""Unit tests for Trello MCP helpers (no live Trello API / no FastMCP required)."""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock, patch

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.core.exceptions import (
    TrelloError,
    TrelloValidationError,
    normalize_trello_error,
)
from app.services.trello_service import TrelloService, load_credentials_dict


class TestExceptions(unittest.TestCase):
    def test_normalize_401(self):
        err = normalize_trello_error(Exception("HTTP 401"), status_code=401)
        self.assertEqual(err.error_code, "AUTH_ERROR")
        self.assertTrue(err.retryable)

    def test_normalize_403(self):
        err = normalize_trello_error(Exception("HTTP 403"), status_code=403)
        self.assertEqual(err.error_code, "PERMISSION_DENIED")

    def test_normalize_404(self):
        err = normalize_trello_error(Exception("HTTP 404"), status_code=404)
        self.assertEqual(err.error_code, "NOT_FOUND")

    def test_normalize_429(self):
        err = normalize_trello_error(Exception("HTTP 429"), status_code=429)
        self.assertEqual(err.error_code, "RATE_LIMIT")
        self.assertTrue(err.retryable)


class TestCredentials(unittest.TestCase):
    def test_missing_credentials(self):
        with self.assertRaises(TrelloError) as ctx:
            load_credentials_dict()
        self.assertEqual(ctx.exception.error_code, "CREDENTIALS_REQUIRED")

    def test_invalid_json(self):
        with self.assertRaises(TrelloError) as ctx:
            load_credentials_dict(credentials_json="{not-json")
        self.assertEqual(ctx.exception.error_code, "INVALID_CREDENTIALS")

    def test_missing_api_key_or_token(self):
        with self.assertRaises(TrelloError) as ctx:
            load_credentials_dict(credentials_json=json.dumps({"api_key": "k"}))
        self.assertEqual(ctx.exception.error_code, "INVALID_CREDENTIALS")

    def test_valid_credentials_json(self):
        creds = load_credentials_dict(
            credentials_json=json.dumps({"api_key": "key123", "token": "tok456"})
        )
        self.assertEqual(creds["api_key"], "key123")
        self.assertEqual(creds["token"], "tok456")

    def test_key_token_aliases(self):
        creds = load_credentials_dict(
            credentials_json=json.dumps({"key": "k", "access_token": "t"})
        )
        self.assertEqual(creds["api_key"], "k")
        self.assertEqual(creds["token"], "t")

    def test_credentials_from_file(self):
        payload = {"api_key": "file_key", "token": "file_token"}
        with tempfile.NamedTemporaryFile("w", suffix=".json", delete=False) as f:
            json.dump(payload, f)
            path = f.name
        os.environ["TRELLO_CREDENTIALS_DIR"] = str(Path(path).parent)
        self.addCleanup(lambda: os.environ.pop("TRELLO_CREDENTIALS_DIR", None))
        creds = load_credentials_dict(credentials_path=Path(path).name)
        self.assertEqual(creds["api_key"], "file_key")

    def test_path_jail_rejects_escape(self):
        os.environ["TRELLO_CREDENTIALS_DIR"] = tempfile.mkdtemp()
        self.addCleanup(lambda: os.environ.pop("TRELLO_CREDENTIALS_DIR", None))
        with self.assertRaises(TrelloError) as ctx:
            load_credentials_dict(credentials_path="/etc/passwd")
        self.assertEqual(ctx.exception.error_code, "INVALID_CREDENTIALS")


class TestTrelloService(unittest.TestCase):
    def _service(self) -> TrelloService:
        return TrelloService(
            credentials_json=json.dumps({"api_key": "k", "token": "t"})
        )

    @patch("app.services.trello_service.requests.request")
    def test_get_me(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"id":"u1","username":"user_a"}'
        mock_resp.json.return_value = {"id": "u1", "username": "user_a"}
        mock_request.return_value = mock_resp

        result = self._service().get_me()
        self.assertEqual(result["username"], "user_a")
        args, kwargs = mock_request.call_args
        self.assertEqual(args[0], "GET")
        self.assertIn("/members/me", args[1])

    @patch("app.services.trello_service.requests.request")
    def test_create_card_dry_run(self, mock_request):
        result = self._service().create_card(
            list_id="list1",
            name="Test card",
            dry_run=True,
        )
        self.assertTrue(result["dry_run"])
        self.assertEqual(result["request_body"]["name"], "Test card")
        mock_request.assert_not_called()

    def test_list_cards_requires_scope(self):
        with self.assertRaises(TrelloValidationError):
            self._service().list_cards()

    def test_list_cards_rejects_both_ids(self):
        with self.assertRaises(TrelloValidationError):
            self._service().list_cards(list_id="l1", board_id="b1")

    @patch("app.services.trello_service.requests.request")
    def test_update_card_http_error(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.text = "not found"
        mock_resp.reason = "Not Found"
        mock_request.return_value = mock_resp

        with self.assertRaises(TrelloError) as ctx:
            self._service().update_card("card1", name="x")
        self.assertEqual(ctx.exception.error_code, "NOT_FOUND")

    @patch("app.services.trello_service.requests.request")
    def test_search_cards_scopes_board_ids(self, mock_request):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.content = b'{"cards":[]}'
        mock_resp.json.return_value = {"cards": []}
        mock_request.return_value = mock_resp

        self._service().search_cards("login", board_ids=["board1"], limit=10)
        _, kwargs = mock_request.call_args
        self.assertEqual(kwargs["params"]["idBoards"], "board1")


class TestSearchCardsInBoardTool(unittest.TestCase):
    """MCP tool wrapper: scalar board_id → service.search_cards(board_ids=[...])."""

    @patch("app.mcp_server._get_trello_service")
    def test_search_cards_in_board_wraps_board_id(self, mock_get_service):
        from app.mcp_server import search_cards_in_board

        mock_svc = MagicMock()
        mock_svc.search_cards.return_value = [{"id": "c1", "name": "Login"}]
        mock_get_service.return_value = mock_svc

        result = search_cards_in_board.fn(
            board_id="sample",
            query="login",
            credentials_json=json.dumps({"api_key": "k", "token": "t"}),
            limit=5,
        )
        self.assertTrue(result.success)
        self.assertEqual(result.total_count, 1)
        mock_svc.search_cards.assert_called_once_with(
            "login", board_ids=["sample"], limit=5
        )

    @patch("app.mcp_server._get_trello_service")
    def test_search_cards_in_board_trims_board_id(self, mock_get_service):
        from app.mcp_server import search_cards_in_board

        mock_svc = MagicMock()
        mock_svc.search_cards.return_value = []
        mock_get_service.return_value = mock_svc

        result = search_cards_in_board.fn(
            board_id="  sample  ",
            query="login",
            credentials_json=json.dumps({"api_key": "k", "token": "t"}),
            limit=20,
        )
        self.assertTrue(result.success)
        mock_svc.search_cards.assert_called_once_with(
            "login", board_ids=["sample"], limit=20
        )

    @patch("app.mcp_server._get_trello_service")
    def test_search_cards_in_board_rejects_empty_board_id(self, mock_get_service):
        from app.mcp_server import search_cards_in_board

        result = search_cards_in_board.fn(
            board_id="  ",
            query="login",
            credentials_json=json.dumps({"api_key": "k", "token": "t"}),
        )
        self.assertFalse(result.success)
        self.assertEqual(result.error["error_code"], "VALIDATION_ERROR")
        mock_get_service.assert_not_called()


if __name__ == "__main__":
    unittest.main()
