#!/usr/bin/env bash
# Manual MCP tool invocation against a running trello-mcp HTTP server.
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
BASE_URL="${TRELLO_MCP_URL:-http://localhost:8000}"
TOOL="${1:-get_me}"
shift || true

CREDS_FILE="${TRELLO_CREDENTIALS_FILE:-$ROOT/token.json}"
CREDS_JSON=""
if [[ -f "$CREDS_FILE" ]]; then
  CREDS_JSON="$(cat "$CREDS_FILE")"
fi

build_args() {
  case "$TOOL" in
    get_me)
      echo '{}'
      ;;
    list_boards)
      echo '{"filter_type":"open","limit":20}'
      ;;
    get_board)
      echo "{\"board_id\":\"${BOARD_ID:?set BOARD_ID}\"}"
      ;;
    list_lists)
      echo "{\"board_id\":\"${BOARD_ID:?set BOARD_ID}\"}"
      ;;
    list_cards)
      if [[ -n "${LIST_ID:-}" ]]; then
        echo "{\"list_id\":\"$LIST_ID\"}"
      else
        echo "{\"board_id\":\"${BOARD_ID:?set BOARD_ID or LIST_ID}\"}"
      fi
      ;;
    get_card)
      echo "{\"card_id\":\"${CARD_ID:?set CARD_ID}\"}"
      ;;
    search_cards)
      echo "{\"query\":\"${QUERY:?set QUERY}\"}"
      ;;
    create_card)
      echo "{\"list_id\":\"${LIST_ID:?set LIST_ID}\",\"name\":\"${NAME:-MCP test card}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    update_card)
      echo "{\"card_id\":\"${CARD_ID:?set CARD_ID}\",\"name\":\"${NAME:-Updated}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    move_card)
      echo "{\"card_id\":\"${CARD_ID:?set CARD_ID}\",\"list_id\":\"${LIST_ID:?set LIST_ID}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    archive_card)
      echo "{\"card_id\":\"${CARD_ID:?set CARD_ID}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    add_comment)
      echo "{\"card_id\":\"${CARD_ID:?set CARD_ID}\",\"text\":\"${TEXT:-hello from trello-mcp}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    create_list)
      echo "{\"board_id\":\"${BOARD_ID:?set BOARD_ID}\",\"name\":\"${NAME:-MCP test list}\",\"confirm\":${CONFIRM:-false},\"dry_run\":${DRY_RUN:-true}}"
      ;;
    *)
      echo "Unknown tool: $TOOL" >&2
      exit 1
      ;;
  esac
}

ARGS="$(build_args)"
PAYLOAD=$(python3 - <<PY
import json
args = json.loads('''$ARGS''')
creds = json.loads('''${CREDS_JSON:-null}''')
if creds:
    args["credentials_json"] = json.dumps(creds)
print(json.dumps({
    "jsonrpc": "2.0",
    "id": 1,
    "method": "tools/call",
    "params": {"name": "$TOOL", "arguments": args},
}))
PY
)

echo "POST $BASE_URL/mcp/ tool=$TOOL"
curl -sS -X POST "$BASE_URL/mcp/" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json, text/event-stream" \
  -d "$PAYLOAD" | python3 -m json.tool 2>/dev/null || cat
