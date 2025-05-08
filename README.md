A simple MCP server that can query chronosphere. 

## Tools
- `query_logs`

TODO:
- query metrics
- get alerts
- query traces
- query change events

## cursor mcp.json
To iterate in Cursor
```json
{
  "mcpServers": {
    "chronosphere-mcp": {
      "command": "uv",
      "args": [
        "--directory",
        "/PATH/TO/REPO",
        "run",
        "server.py"
      ],
      "env": {
        "CHRONOSPHERE_API_TOKEN": "<REPLACE_ME>"
      }
    }
  }
}
```