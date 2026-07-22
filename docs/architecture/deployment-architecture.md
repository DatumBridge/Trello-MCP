# Deployment Architecture

```text
┌─────────────────┐     POST /mcp/      ┌──────────────────┐
│ DatumBridge     │ ──────────────────► │ trello-mcp       │
│ LangGraph /     │   credentials_json  │ (FastMCP)        │
│ Studio          │ ◄────────────────── │                  │
└─────────────────┘   structured JSON   └────────┬─────────┘
                                                   │ HTTPS
                                                   ▼
                                          ┌──────────────────┐
                                          │ api.trello.com/1 │
                                          └──────────────────┘
```

## Components

| Component | Role |
|-----------|------|
| `app/mcp_server.py` | MCP tool surface, HTTP app, health endpoint |
| `app/services/trello_service.py` | Trello REST client |
| `app/core/exceptions.py` | Error normalization |
| `app/schemas/mcp_models.py` | Pydantic response models |

## Runtime modes

- **stdio** — `python -m app.mcp_server` (Claude Desktop / Cursor)
- **HTTP/SSE** — `uvicorn app.mcp_server:http_app` (DatumBridge platform)
- **Docker** — port 8000, health check on `/health`

## Security boundaries

- Credentials never logged
- Write tools require `confirm=true`
- `credentials_path` restricted to `TRELLO_CREDENTIALS_DIR`
- Kubernetes pod/container security context: non-root UID/GID `10001` (matches Dockerfile `appuser`; IDs > 10000), `readOnlyRootFilesystem: true`, `allowPrivilegeEscalation: false`, drop all capabilities, `RuntimeDefault` seccomp; only `/tmp` is writable via `emptyDir`
- ConfigMap holds non-sensitive knobs only (`PORT`, `LOG_LEVEL`, `TRELLO_HTTP_TIMEOUT_SEC`); service URLs and credentials are in Secret (`trello-mcp-main-secret`)
