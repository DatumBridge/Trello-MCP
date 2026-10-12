# list_workspaces

List Trello workspaces (organizations) for the authenticated member. Use a workspace id as workspace_id on list_boards and search_cards.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| — | — | This call takes no model arguments. |

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
  "workspaces": [],
  "total_count": "example"
}
```
