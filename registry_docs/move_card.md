# move_card

Move a card to another list. Requires confirm=true.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `card_id` | yes | Card ID to move |
| `list_id` | yes | Destination list ID |
| `pos` | no | Position in destination list: top, bottom, or positive float |
| `confirm` | no | Must be true to move (side effect). Use dry_run to preview. |
| `dry_run` | no | If true, return the request payload without calling Trello |

## Cases

### Typical call

Input:

```json
{
  "card_id": "example-card",
  "list_id": "example-list",
  "dry_run": true
}
```

Output:

```json
{
  "success": true,
  "message": "example",
  "card_id": "example-card",
  "list_id": "example-list",
  "comment_id": "example-id",
  "dry_run": false,
  "request_body": "example"
}
```

### Missing `card_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "list_id": "example-list",
  "dry_run": true
}
```

Output:

```json
{
  "success": false,
  "error": {
    "error_code": "invalid_argument",
    "error_message": "card_id is required",
    "retryable": false
  }
}
```

### Preview the write

Set `dry_run` to true. The tool returns the planned change and does not send it.

Input:

```json
{
  "card_id": "example-card",
  "list_id": "example-list",
  "dry_run": true
}
```

### Confirmed write

Set `confirm` to true. Omit `dry_run`.

Input:

```json
{
  "card_id": "example-card",
  "list_id": "example-list",
  "confirm": true
}
```

### Write without confirm or dry_run

Input:

```json
{
  "card_id": "example-card",
  "list_id": "example-list"
}
```

Output:

```json
{
  "success": false,
  "error_message": "confirm=true required for write tools (or dry_run=true to preview)"
}
```
