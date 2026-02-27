#!/usr/bin/env bash
# Launch Cursor with lower memory limits (for 8GB machines).
# Use this instead of opening Cursor from Dock/Spotlight to reduce crashes.
#
# Usage: ./scripts/launch_cursor_low_memory.sh
# Or from anywhere: open -a "Cursor" --env NODE_OPTIONS="--max-old-space-size=2048"
# (macOS may not pass NODE_OPTIONS to the app; this script uses the CLI.)

# Cap Node/Electron heap for Cursor's processes (2GB). Adjust if still crashing: try 1536.
export NODE_OPTIONS="${NODE_OPTIONS:-} --max-old-space-size=2048"

# Use Cursor CLI if available (e.g. "Cursor" shell command: Install from Command Palette)
if command -v cursor &>/dev/null; then
  cursor "$@"
else
  # Fallback: open the app (env may not apply to all child processes)
  open -a "Cursor" --args "$@"
fi
