# create_card

Create a card on a Trello list. Requires confirm=true.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `list_id` | yes | Target list ID |
| `name` | yes | Card title |
| `desc` | no | Card description |
| `due` | no | Due date. Accepts dd/MM/yyyy, dd-MM-yyyy, yyyy-MM-dd, yyyy/MM/dd, or ISO 8601 (e.g. 2026-07-21T12:00:00.000Z); normalized for Trello. |
| `pos` | no | Position: top, bottom, or positive float |
| `confirm` | no | Must be true to create (side effect). Use dry_run to preview. |
| `dry_run` | no | If true, return the request payload without calling Trello |

## Cases

### Typical call

Input:

```json
{
  "list_id": "example-list",
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

### Missing `list_id`

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
    "error_message": "list_id is required",
    "retryable": false
  }
}
```

### Preview the write

Set `dry_run` to true. The tool returns the planned change and does not send it.

Input:

```json
{
  "list_id": "example-list",
  "name": "example-name",
  "dry_run": true
}
```

### Confirmed write

Set `confirm` to true. Omit `dry_run`.

Input:

```json
{
  "list_id": "example-list",
  "name": "example-name",
  "confirm": true
}
```

### Write without confirm or dry_run

Input:

```json
{
  "list_id": "example-list",
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
