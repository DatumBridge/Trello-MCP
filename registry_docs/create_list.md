# create_list

Create a list on a Trello board. Requires confirm=true.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `board_id` | yes | Board ID to add the list to |
| `name` | yes | List name |
| `pos` | no | Position: top, bottom, or positive float |
| `confirm` | no | Must be true to create (side effect). Use dry_run to preview. |
| `dry_run` | no | If true, return the request payload without calling Trello |

## Cases

### Typical call

Input:

```json
{
  "board_id": "example-board",
  "name": "example-name",
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

### Missing `board_id`

The tool rejects the call and does not guess the missing value.

Input:

```json
{
  "name": "example-name",
  "dry_run": true
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

### Preview the write

Set `dry_run` to true. The tool returns the planned change and does not send it.

Input:

```json
{
  "board_id": "example-board",
  "name": "example-name",
  "dry_run": true
}
```

### Confirmed write

Set `confirm` to true. Omit `dry_run`.

Input:

```json
{
  "board_id": "example-board",
  "name": "example-name",
  "confirm": true
}
```

### Write without confirm or dry_run

Input:

```json
{
  "board_id": "example-board",
  "name": "example-name"
}
```

Output:

```json
{
  "success": false,
  "error_message": "confirm=true required for write tools (or dry_run=true to preview)"
}
```
