#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
OUT_DIR="$ROOT_DIR/out"
DEST_DIR="$ROOT_DIR/abis"

mkdir -p "$DEST_DIR"

# Copy AIFlashLoanExecutor ABI from Foundry build output
SRC="$OUT_DIR/AIFlashLoanExecutor.sol/AIFlashLoanExecutor.json"
if [ ! -f "$SRC" ]; then
  echo "Build output not found at $SRC. Run 'forge build' first."
  exit 1
fi

# Extract only the 'abi' and rewrap to a simple JSON with 'abi' for Python
# If jq is available, we can clean it up; else copy as-is
if command -v jq >/dev/null 2>&1; then
  jq '{abi: .abi}' "$SRC" > "$DEST_DIR/AIFlashLoanExecutor.json"
else
  cp "$SRC" "$DEST_DIR/AIFlashLoanExecutor.json"
fi

echo "Exported ABI to $DEST_DIR/AIFlashLoanExecutor.json"
