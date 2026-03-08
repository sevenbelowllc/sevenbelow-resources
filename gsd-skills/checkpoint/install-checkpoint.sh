#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
GSD_COMMANDS="$HOME/.claude/commands/gsd"
GSD_SCRIPTS="$HOME/.claude/get-shit-done/scripts"

echo "Installing checkpoint files from $SCRIPT_DIR ..."

mkdir -p "$GSD_COMMANDS"
mkdir -p "$GSD_SCRIPTS"

cp "$SCRIPT_DIR/checkpoint.md" "$GSD_COMMANDS/checkpoint.md"
echo "  ✓ checkpoint.md → $GSD_COMMANDS/"

cp "$SCRIPT_DIR/verify-gsd-state.js" "$GSD_SCRIPTS/verify-gsd-state.js"
echo "  ✓ verify-gsd-state.js → $GSD_SCRIPTS/"

echo "Done. /gsd:checkpoint is ready."
