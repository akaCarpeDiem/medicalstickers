#!/usr/bin/env bash
# Build a clean public dir (no tools/, functions source, .git, docs) and deploy it to Cloudflare Pages.
# Usage: tools/deploy.sh preview-<name>   (preview)   |   tools/deploy.sh main   (production)
# Run from anywhere; Pages Functions are compiled from ./functions at the repo root.
set -euo pipefail
BRANCH="${1:?branch: main or preview-<name>}"
ROOT="$(cd "$(dirname "$0")/.." && pwd)"; OUT=/tmp/ms-dist
rm -rf "$OUT"; mkdir -p "$OUT"
cd "$ROOT"
tar --exclude=./.git --exclude=./tools --exclude=./functions --exclude=./node_modules \
    --exclude='*.py' --exclude='*.md' --exclude='__pycache__' --exclude='.gitignore' --exclude='.wrangler' \
    -cf - . | tar -xf - -C "$OUT"
npx wrangler pages deploy "$OUT" --project-name medicalstickers --branch="$BRANCH" \
  --commit-hash "$(git rev-parse HEAD)" --commit-message "$(git log -1 --format=%s | cut -c1-200)" --commit-dirty=true
