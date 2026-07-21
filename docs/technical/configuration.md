# Configuration

## Environment variables

| Variable | Default | Description |
|----------|---------|-------------|
| `PORT` | `8000` | HTTP listen port (uvicorn) |
| `LOG_LEVEL` | `INFO` | Logging level |
| `TRELLO_HTTP_TIMEOUT_SEC` | `30` | Outbound API timeout |
| `TRELLO_CREDENTIALS_DIR` | project root | Path jail for `credentials_path` |

## Credentials (per tool invocation)

Pass either `credentials_path` or `credentials_json`:

```json
{
  "api_key": "your_api_key",
  "token": "your_token"
}
```

### Obtaining credentials

1. API key: https://trello.com/app-key
2. Token: authorize with read,write scope:

```
https://trello.com/1/authorize?expiration=never&scope=read,write&response_type=token&name=TrelloMCP&key=YOUR_API_KEY
```

## DatumBridge Studio

When registered in the platform credential vault, `credentials_json` is injected on tool execute. Do not map raw tokens in workflow parameters.
