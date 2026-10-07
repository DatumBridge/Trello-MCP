# list_lists

List lists on a Trello board.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `board_id` | yes | Trello board ID |
| `filter_type` | no | Filter: all or open |

## Cases

### Typical call

Input:

```json
{
  "board_id": "example-board"
}
```

Output:

```json
{
  "success": true,
  "lists": [],
  "total_count": "example"
}
```

### Missing `board_id`

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
    "error_message": "board_id is required",
    "retryable": false
  }
}
```
