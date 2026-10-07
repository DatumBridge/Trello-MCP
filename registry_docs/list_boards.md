# list_boards

List boards for the authenticated member.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `filter_type` | no | Filter: all, closed, members, open, organization, pinned, public, starred, unpinned |
| `limit` | no | Max boards to return (1-1000) |

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
  "boards": [],
  "total_count": "example"
}
```
