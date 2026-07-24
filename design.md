# Design: Trello MCP Server for DatumBridge

## Objective

Production-ready MCP Server integrating Trello into the DatumBridge platform.

The MCP Server must:

- Act as an abstraction layer between the Execution Engine and Trello REST API.
- Expose standardized MCP tools for boards, lists, and cards.
- Support multi-tenant credential injection via `credentials_json`.
- Be secure, auditable, and enterprise-ready.

## Architectural Principles

1. **Separation of concerns** — Trello API logic lives only in `TrelloService`.
2. **Tool-based interaction** — Each capability is an independent MCP tool.
3. **Stateless execution** — No workflow state stored in the MCP server.
4. **Multi-tenant isolation** — Credentials passed per invocation; path jail for file-based creds.

## MCP Tools

### Read-only

| Tool | Trello API | Description |
|------|------------|-------------|
| `get_me` | `GET /members/me` | Authenticated member profile |
| `list_boards` | `GET /members/me/boards` | List member boards |
| `get_board` | `GET /boards/{id}` | Board details |
| `list_lists` | `GET /boards/{id}/lists` | Lists on a board |
| `list_cards` | `GET /lists/{id}/cards` or `/boards/{id}/cards` | Cards on list or board |
| `get_card` | `GET /cards/{id}` | Card details |
| `search_cards` | `GET /search` | Search cards by query (`board_ids` optional; ObjectId / shortLink / exact name resolved) |
| `search_cards_in_board` | `GET /search` | Search cards within one board (`board_id` ObjectId / shortLink / exact name) |

### Write (require `confirm=true`)

| Tool | Trello API | Description |
|------|------------|-------------|
| `create_card` | `POST /cards` | Create card on list |
| `update_card` | `PUT /cards/{id}` | Update card fields |
| `move_card` | `PUT /cards/{id}` | Move card to another list |
| `archive_card` | `PUT /cards/{id}` | Archive (close) card |
| `add_comment` | `POST /cards/{id}/actions/comments` | Add comment |
| `create_list` | `POST /lists` | Create list on board |

All write tools support `dry_run=true` to preview request payloads.

## Credentials

JSON format:

```json
{
  "api_key": "<from trello.com/app-key>",
  "token": "<user-authorized token>"
}
```

Aliases accepted: `key` / `access_token`.

## Error Model

Standardized error structure:

- `error_code` — e.g. `AUTH_ERROR`, `NOT_FOUND`, `VALIDATION_ERROR`
- `error_message` — human-readable message
- `retryable` — boolean
- `original_provider_error` — provider detail when available

## Non-goals

- Trello webhooks / real-time sync
- Power-Ups or custom fields (future extension)
- OAuth redirect flow (token obtained manually or via Studio vault)

## Deployment

- HTTP/SSE via `uvicorn app.mcp_server:http_app`
- Docker image on port 8000
- Health: `GET /health`
