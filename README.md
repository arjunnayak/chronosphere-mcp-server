# Chronosphere MCP Server

A simple MCP server that can query Chronosphere logs.

## Setup Instructions

### 1. Install `uv`
If you don't have `uv` installed, you can install it with:
```sh
curl -LsSf https://astral.sh/uv/install.sh | sh
```
See [docs](https://docs.astral.sh/uv/getting-started/installation/#standalone-installer) for other installation methods.

### 2. Install dependencies
From the root of the repository, run:
```sh
uv pip install -r pyproject.toml
```
Or, if you want to use the lockfile for reproducible installs:
```sh
uv pip install -r uv.lock
```

### 3. Set your Chronosphere API token
Export your API token as an environment variable:
```sh
export CHRONOSPHERE_API_TOKEN="<YOUR_API_TOKEN>"
```

### 4. Run the MCP server
From the root directory, start the server with:
```sh
uv run server.py
```

### 5. (Optional) Use with Cursor
If you are using Cursor, ensure your `.cursor/mcp.json` is configured as follows:
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

## Tools
- `query_logs`

TODO:
- query metrics
- get alerts
- query traces
- query change events