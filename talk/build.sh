#!/usr/bin/env bash
# Export the Marp deck to PDF (and optionally PPTX/HTML).
set -euo pipefail
cd "$(dirname "$0")"

npx --yes @marp-team/marp-cli@latest slides.md -o slides.pdf --allow-local-files

if [ "${1:-}" = "--pptx" ]; then
  npx --yes @marp-team/marp-cli@latest slides.md -o slides.pptx --allow-local-files
fi

echo "Built talk/slides.pdf"
