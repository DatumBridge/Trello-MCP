# list_boards

List boards for the authenticated member. Each board includes idOrganization, the workspace it belongs to. Pass workspace_id to read one workspace. Omitting it reads every workspace.

The gateway injects `credentials_json` from the connected account. Do not invent a token or paste a secret into the arguments.

## Parameters

| Name | Required | Meaning |
|---|---|---|
| `workspace_id` | no | Trello workspace id (organization id from list_workspaces). When set, only that workspace's boards are returned. When omitted, boards are read from every workspace, not the first one. |
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
  "total_count": "example",
  "workspace_id": "example-workspace"
}
```
