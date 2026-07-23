# Configuration

## Deployment env (trello-mcp)

| Variable | Required | Description |
|----------|----------|-------------|
| `TRELLO_API_KEY` | Yes | Trello Power-Up API key |
| `TRELLO_API_SECRET` | Yes | Trello API secret |
| `STUDIO_PUBLIC_URL` | Yes | Post-OAuth redirect base — must match Studio URL (K8s NodePort default `http://localhost:30080`) |
| `OAUTH_REDIRECT_URI` | Recommended | **`{STUDIO_PUBLIC_URL}/api/mcp/api/v1/credentials/oauth/trello/callback`** (Studio→datumbridge-mcp→trello-mcp; same as Gmail) |
| `TRELLO_MCP_PUBLIC_URL` | Optional | Public base URL if `OAUTH_REDIRECT_URI` unset |
| `CREDENTIAL_VAULT_API_URL` | Yes (Secret) | datumbridge-mcp base URL — use `http://datumbridge-mcp.datumbridge-adk-db.svc.cluster.local:8081` from `mcp-tools` |
| `DATUMBRIDGE_MCP_NAMESPACE` | Optional | Fallback vault host namespace (default `datumbridge-adk-db`) |
| `MCP_SERVICE_API_KEY` | Yes (Secret) | Must match datumbridge-mcp `MCP_SERVICE_API_KEY` |
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
      → trello-mcp /oauth/start (service key + X-User-ID; pending saved on datumbridge-mcp)
      → Trello authorize
      → browser → Studio /api/mcp/…/credentials/oauth/trello/callback
      → datumbridge-mcp → trello-mcp /oauth/callback → vault save
      → redirect STUDIO_PUBLIC_URL/account/integrations?trello=connected
```

Register **trello-mcp** callback URL in Trello Power-Up admin (`GET /oauth/info`).
