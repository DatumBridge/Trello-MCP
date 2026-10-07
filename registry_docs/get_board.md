# get_board

Get a Trello board by ID.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `board_id` | yes | Trello board ID |

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
  "board": "example"
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
