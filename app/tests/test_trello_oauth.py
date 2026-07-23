#!/usr/bin/env python3
"""Unit tests for Trello OAuth helpers (no live Trello API)."""

import os
import sys
import unittest
from unittest.mock import patch

ROOT = __import__("pathlib").Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.services import trello_oauth as oauth


class TestTrelloOAuthConfig(unittest.TestCase):
    def test_studio_public_url_default(self):
        os.environ.pop("STUDIO_PUBLIC_URL", None)
        os.environ.pop("OAUTH_REDIRECT_URI", None)
        self.assertEqual(oauth.studio_public_url(), "http://localhost:30080")

    def test_studio_public_url_from_oauth_redirect(self):
        os.environ.pop("STUDIO_PUBLIC_URL", None)
        os.environ["OAUTH_REDIRECT_URI"] = (
            "http://localhost:30080/api/mcp/api/v1/credentials/oauth/trello/callback"
        )
        self.assertEqual(oauth.studio_public_url(), "http://localhost:30080")

    def test_oauth_redirect_from_studio_public_url(self):
        os.environ["STUDIO_PUBLIC_URL"] = "http://localhost:30080"
        os.environ.pop("OAUTH_REDIRECT_URI", None)
        os.environ.pop("TRELLO_MCP_PUBLIC_URL", None)
        self.assertEqual(
            oauth.oauth_redirect_uri(),
            "http://localhost:30080/api/mcp/api/v1/credentials/oauth/trello/callback",
        )

    def test_oauth_redirect_from_public_url(self):
        os.environ["TRELLO_MCP_PUBLIC_URL"] = "http://127.0.0.1:30081"
        os.environ.pop("OAUTH_REDIRECT_URI", None)
        os.environ.pop("STUDIO_PUBLIC_URL", None)
        self.assertEqual(oauth.oauth_redirect_uri(), "http://127.0.0.1:30081/oauth/callback")

    def test_oauth_redirect_rejects_studio_root(self):
        os.environ["OAUTH_REDIRECT_URI"] = "http://localhost:30080"
        os.environ["STUDIO_PUBLIC_URL"] = "http://localhost:30080"
        with self.assertRaises(Exception):
            oauth.oauth_redirect_uri()

    def test_api_key_required(self):
        os.environ.pop("TRELLO_API_KEY", None)
        with self.assertRaises(Exception):
            oauth._api_key()


class TestOAuth1Signature(unittest.TestCase):
    def test_signature_is_deterministic_with_fixed_nonce(self):
        params = oauth._oauth1_params("key", "")
        params["oauth_callback"] = "http://example.com/cb"
        params["oauth_timestamp"] = "123"
        params["oauth_nonce"] = "abc"
        sig = oauth._oauth1_signature(
            "POST", oauth.TRELLO_REQUEST_TOKEN_URL, params, "secret&"
        )
        self.assertTrue(sig)


if __name__ == "__main__":
    unittest.main()
