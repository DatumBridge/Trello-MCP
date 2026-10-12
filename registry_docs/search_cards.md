# search_cards

Search Trello cards by query string across one or more boards (or one workspace). Pass workspace_id so the search is not limited to the first workspace.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `query` | yes | Search query string |
| `workspace_id` | no | Trello workspace id (organization id from list_workspaces). Scopes the search to that workspace when board_ids is omitted. |
| `board_ids` | no | Optional list of board IDs to scope search |
| `limit` | no | Max cards to return (1-1000) |

## Cases

### Typical call

Input:

```json
{
  "query": "quarterly report"
}
```

Output:

```json
{
  "success": true,
  "cards": [],
  "total_count": "example"
}
```

### Missing `query`

The tool rejects the call and does not guess the missing value.

Input:

```json
{}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "query is required",
    "retryable": false
  }
}
```
