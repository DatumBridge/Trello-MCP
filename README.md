# Trello MCP Server

DatumBridge **tool-server** that exposes Trello board, list, and card management over Streamable HTTP MCP. Sibling to `google-drive-mcp` / `linkedin-mcp`.

**Class:** Python FastMCP tool-server. See [`docs/`](docs/README.md).

## Tools

| Area | Tools |
|------|--------|
| Profile | `get_me` |
| Boards | `list_boards`, `get_board` |
| Lists | `list_lists`, `create_list` |
| Cards | `list_cards`, `get_card`, `search_cards`, `search_cards_in_board`, `create_card`, `update_card`, `move_card`, `archive_card` |
| Comments | `add_comment` |

Every tool requires **`credentials_path`** or **`credentials_json`** with `api_key` and `token`.

Side-effect tools require **`confirm=true`**. Use **`dry_run=true`** to preview without calling Trello.

Registry id: **`mcpServer=trello`** (when registered in DatumBridge MCP).

## Setup

1. Get your API key from [Trello Power-Up admin](https://trello.com/app-key).
2. Generate a token (authorize with `read,write` scope):

   ```
   https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=TrelloMCP&key=YOUR_API_KEY
   ```

3. Save credentials as `token.json`:

   ```json
   {
     "api_key": "your_api_key",
     "token": "your_token"
   }
   ```

```bash
cp .env.example .env
python -m venv .venv && source .venv/bin/activate
pip install -r requirements_mcp.txt
chmod +x mcp_server_entrypoint.sh
./mcp_server_entrypoint.sh
# or: uvicorn app.mcp_server:http_app --host 0.0.0.0 --port 8000
```

- Health: `GET http://localhost:8000/health`
- MCP: `POST http://localhost:8000/mcp/`
- Test UI: `http://localhost:8000/test`

Requires **Python 3.10+** (Docker image uses 3.11).

```bash
python scripts/test_helpers.py -v
```

## Manual testing

```bash
export TRELLO_CREDENTIALS_FILE=./token.json
./scripts/manual_mcp_call.sh get_me
./scripts/manual_mcp_call.sh list_boards
BOARD_ID=abc123 ./scripts/manual_mcp_call.sh list_lists
BOARD_ID=abc123 QUERY="login" ./scripts/manual_mcp_call.sh search_cards_in_board
LIST_ID=def456 DRY_RUN=true ./scripts/manual_mcp_call.sh create_card
```

## Docker

```bash
docker build -t trello-mcp .
docker run -p 8000:8000 trello-mcp
```

## Architecture

```text
Studio / LangGraph → POST /mcp → mcp_server tools → TrelloService → api.trello.com/1
```

- **app/mcp_server.py** – MCP server with FastMCP, tool definitions
- **app/services/trello_service.py** – Trello REST API wrapper
- **app/schemas/mcp_models.py** – Pydantic response models
- **app/core/exceptions.py** – Normalized error handling

## Security

- Credentials are passed per tool invocation (path jail via `TRELLO_CREDENTIALS_DIR`).
- Side-effect tools require explicit `confirm=true`.
- Card/board text is untrusted external content.

## Kubernetes (`mcp-tools`)

```bash
chmod +x k8s-deploy.sh
./k8s-deploy.sh
```

- Service: `http://trello-mcp-main.mcp-tools.svc.cluster.local:8000`
- MCP: `http://trello-mcp-main.mcp-tools.svc.cluster.local:8000/mcp/`

**Production (DatumBridge Studio):** connect Trello under Account → Integrations. Configure `TRELLO_API_KEY`, `TRELLO_API_SECRET`, and `STUDIO_PUBLIC_URL` on **this** deployment (not datumbridge-mcp). Register `/oauth/callback` from `/oauth/info` in Trello Power-Up admin.

Registry id: **`mcpServer=trello`**.

## Studio Integrations setup

1. Set in `.env`: `TRELLO_API_KEY`, `TRELLO_API_SECRET`, `STUDIO_PUBLIC_URL`, `MCP_SERVICE_API_KEY`.
2. `./k8s-deploy.sh` — auto-sets `OAUTH_REDIRECT_URI` from NodePort.
3. Register callback URL **`http://localhost:30080/api/mcp/api/v1/credentials/oauth/trello/callback`** at [trello.com/app-key](https://trello.com/app-key) (same Studio→MCP path as Gmail OAuth; avoids cross-namespace 502 on `/api/trello/`).
4. On `datumbridge-mcp`, set `TRELLO_MCP_URL` only when the in-cluster service name differs from registry defaults (optional if trello-mcp is registered in Tool Registry with a `baseURL`).

## License

DatumBridge Platform — internal use.
