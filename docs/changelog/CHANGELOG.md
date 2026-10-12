## 2026-10-12

### Added

- `list_workspaces` returns Trello workspace ids (`GET /members/me/organizations`).

### Changed

- `list_boards` accepts `workspace_id` and reads `GET /organizations/{workspace_id}/boards`. Each board includes `idOrganization`. When `workspace_id` is omitted, boards are collected from every workspace instead of the first workspace returned by `GET /members/me/boards`.
- `search_cards` accepts `workspace_id` and sends it as `idOrganizations` when no board list is given. `search_cards_in_board` uses `workspace_id` when resolving a board name or shortLink.

Redeploy `trello-mcp` and publish the tool again so the registry picks up the new arguments.

## 2026-07-24

### Changed
- `create_card` / `update_card` `due` accepts common calendar dates (`dd/MM/yyyy`, `dd-MM-yyyy`, `yyyy-MM-dd`, `yyyy/MM/dd`) and ISO 8601; values are normalized to Trello ISO before the API call. Relative prose still returns `VALIDATION_ERROR`.

## 2026-07-23

### Added

- `search_cards_in_board` — search cards scoped to a single `board_id` string (prefer over `search_cards` + `board_ids` list when the workflow already selected one board)
- Board ref resolution for search: `board_id` / `board_ids` accept ObjectId, shortLink, or exact board name (resolved before `/search` `idBoards`)

### Fixed

- Clearer `VALIDATION_ERROR` when Trello returns HTTP 400 Invalid objectId (was `UNKNOWN_ERROR`)
- `create_card` rejects non-ISO `due` with `VALIDATION_ERROR` (relative prose no longer becomes opaque `UNKNOWN_ERROR`); HTTP 422 / invalid-date mapped to `VALIDATION_ERROR`; create/move error logs include message text

## 2026-07-22

### Changed

- Hardened `k8s/deployment.yaml`: non-root UID/GID 1000, `readOnlyRootFilesystem`, drop all capabilities, RuntimeDefault seccomp, writable `/tmp` emptyDir only
- Raised container UID/GID to `10001` (Dockerfile + Deployment) to avoid host user-table conflicts
- Moved `CREDENTIAL_VAULT_API_URL` out of ConfigMap into Secret; ConfigMap keeps only non-sensitive knobs

## 2026-07-21

### Added

- Initial Trello MCP server with FastMCP + Streamable HTTP transport
- Tools: `get_me`, `list_boards`, `get_board`, `list_lists`, `list_cards`, `get_card`, `search_cards`, `create_card`, `update_card`, `move_card`, `archive_card`, `add_comment`, `create_list`
- API key + token credential model with path jail
- Side-effect guard (`confirm=true`) and `dry_run` preview on write tools
- Docker image, test helpers, manual MCP call script, test UI
- Kubernetes deployment (`k8s/deployment.yaml`, `k8s-deploy.sh`)
- DatumBridge Studio Integrations: OAuth 1.0a vault provider `trello` via trello-mcp deployment (credentials env on MCP, not datumbridge-mcp)
