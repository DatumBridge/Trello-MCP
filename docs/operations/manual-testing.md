# Manual Testing

## Prerequisites

- `token.json` with `api_key` and `token`
- Server running: `./mcp_server_entrypoint.sh`

## Unit tests (no API)

```bash
python scripts/test_helpers.py -v
```

## CLI tool calls

```bash
export TRELLO_CREDENTIALS_FILE=./token.json

./scripts/manual_mcp_call.sh get_me
./scripts/manual_mcp_call.sh list_boards
BOARD_ID=<id> ./scripts/manual_mcp_call.sh list_lists
LIST_ID=<id> NAME="Test" DRY_RUN=true ./scripts/manual_mcp_call.sh create_card
LIST_ID=<id> NAME="Test" CONFIRM=true DRY_RUN=false ./scripts/manual_mcp_call.sh create_card
```

## Browser test UI

1. Open `http://localhost:8000/test`
2. Paste credentials JSON
3. Call `get_me`, then `list_boards`
4. Use dry run before confirm on write tools

## Health check

```bash
curl http://localhost:8000/health
```

Expected: `{"status":"ok","service":"trello-mcp"}`
