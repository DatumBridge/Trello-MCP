# Configuration

## Deployment env (trello-mcp)

| Variable | Required | Description |
|----------|----------|-------------|
| `TRELLO_API_KEY` | Yes | Trello Power-Up API key |
| `TRELLO_API_SECRET` | Yes | Trello API secret |
| `STUDIO_PUBLIC_URL` | Yes | Post-OAuth redirect base (e.g. `http://localhost:5173`) |
| `OAUTH_REDIRECT_URI` | Optional | Trello callback; default `{TRELLO_MCP_PUBLIC_URL}/oauth/callback` |
| `TRELLO_MCP_PUBLIC_URL` | Optional | Public base URL if `OAUTH_REDIRECT_URI` unset |
| `CREDENTIAL_VAULT_API_URL` | Yes | datumbridge-mcp base URL for vault save |
| `MCP_SERVICE_API_KEY` | Yes | Service auth for vault save + OAuth start proxy |
| `TRELLO_HTTP_TIMEOUT_SEC` | Optional | API timeout (default 30) |

## datumbridge-mcp (proxy only)

| Variable | Description |
|----------|-------------|
| `TRELLO_MCP_URL` | In-cluster trello-mcp URL (default `http://trello-mcp-main.mcp-tools.svc.cluster.local:8000`) |

Do **not** set `TRELLO_API_KEY` / `TRELLO_API_SECRET` on datumbridge-mcp.

## Credentials (per tool invocation)

Vault injects `credentials_json`:

```json
{
  "api_key": "...",
  "token": "..."
}
```

## OAuth flow

```text
Studio → datumbridge-mcp /credentials/oauth/trello/start (JWT)
      → trello-mcp /oauth/start (service key + X-User-ID)
      → Trello authorize
      → trello-mcp /oauth/callback
      → datumbridge-mcp /internal/credentials/trello (vault save)
      → redirect STUDIO_PUBLIC_URL/account/integrations?trello=connected
```

Register **trello-mcp** callback URL in Trello Power-Up admin (`GET /oauth/info`).
