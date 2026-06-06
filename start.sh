#!/bin/bash
# Start the webdev MCP server as a background HTTP service
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
LOG=/tmp/webdev-mcp.log

# Kill any existing instance
pkill -f "server.py --http" 2>/dev/null

# Start fresh
nohup "$SCRIPT_DIR/.venv/bin/python" "$SCRIPT_DIR/server.py" --http --port 7771 > "$LOG" 2>&1 &
echo "✅ webdev-mcp started (PID $!) on http://127.0.0.1:7771/mcp"
echo "   Logs: $LOG"
