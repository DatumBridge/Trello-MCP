## 2026-07-21

### Added

- Initial Trello MCP server with FastMCP + Streamable HTTP transport
- Tools: `get_me`, `list_boards`, `get_board`, `list_lists`, `list_cards`, `get_card`, `search_cards`, `create_card`, `update_card`, `move_card`, `archive_card`, `add_comment`, `create_list`
- API key + token credential model with path jail
- Side-effect guard (`confirm=true`) and `dry_run` preview on write tools
- Docker image, test helpers, manual MCP call script, test UI
- Kubernetes deployment (`k8s/deployment.yaml`, `k8s-deploy.sh`)
- DatumBridge Studio Integrations: OAuth 1.0a vault provider `trello` via `datumbridge-mcp`
