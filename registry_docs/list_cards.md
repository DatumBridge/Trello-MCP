# list_cards

List cards on a Trello list or board.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `list_id` | no | List ID to fetch cards from (mutually exclusive with board_id) |
| `board_id` | no | Board ID to fetch cards from (mutually exclusive with list_id) |
| `filter_type` | no | Filter: all, closed, none, open, visible |
| `limit` | no | Max cards to return (1-1000) |

## Cases

### Typical call

Input:

```json
{}
```

Output:

```json
{
  "success": true,
  "cards": [],
  "total_count": "example"
}
```
