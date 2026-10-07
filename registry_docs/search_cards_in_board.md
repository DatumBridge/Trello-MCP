# search_cards_in_board

Search Trello cards within a single board. Prefer this over ``search_cards`` when the workflow already selected one board (``boardId`` / ``board_id`` is a string, not a list). ``board_id`` should be the Trello ObjectId. Names/shortLinks are resolved when possible.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `board_id` | yes | Trello board ObjectId (24-char hex from list_boards/get_board .id). Also accepts shortLink or exact board name (resolved to ObjectId). |
| `query` | yes | Search query string |
| `limit` | no | Max cards to return (1-1000) |

## Cases

### Typical call

Input:

```json
{
  "board_id": "example-board",
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

### Missing `board_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "query": "quarterly report"
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "board_id is required",
    "retryable": false
  }
}
```
