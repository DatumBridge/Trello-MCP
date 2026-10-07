# get_card

Get a Trello card by ID.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `card_id` | yes | Trello card ID |

## Cases

### Typical call

Input:

```json
{
  "card_id": "example-card"
}
```

Output:

```json
{
  "success": true,
  "card": "example"
}
```

### Missing `card_id`

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
    "error_message": "card_id is required",
    "retryable": false
  }
}
```
