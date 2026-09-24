#!/usr/bin/env bash
#
# analyze-disk.sh - Quick macOS Storage & Cleanable Target Analyzer
# Identifies space hogs across user Library, developer caches, and downloads.

set -euo pipefail

echo "=== macOS Disk Space Overview ==="
df -h / | awk 'NR==1 || NR==2'
echo ""

echo "=== Developer Caches Status ==="
check_cache() {
  local path="$1"
  local desc="$2"
  if [ -e "$path" ]; then
    local size
    size=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
    printf "%-35s %10s (%s)\n" "$path" "$size" "$desc"
  fi
}

check_cache "$HOME/.npm" "npm & npx cache"
check_cache "$HOME/.gradle/caches" "Gradle dependencies"
check_cache "$HOME/.cache/uv" "Python uv cache"
check_cache "$HOME/.cache/codex-runtimes" "Codex runtimes"
check_cache "$HOME/Library/Caches/Homebrew" "Homebrew bottles"
check_cache "$HOME/Library/Caches/go-build" "Go build objects"
check_cache "$HOME/Library/Caches/pip" "pip wheel cache"
check_cache "$HOME/Library/Application Support/Notion/Partitions/notion/Service Worker/CacheStorage" "Notion webview cache"
echo ""

echo "=== Large Files in Downloads (>50MB) ==="
find "$HOME/Downloads" -maxdepth 2 -type f -size +50M -exec du -sh {} + 2>/dev/null | sort -hr | head -n 10 || echo "None found"
echo ""

if command -v mo >/dev/null 2>&1; then
  echo "=== Mole (mo) Available ==="
  echo "Mole CLI detected. You can run 'mo clean --dry-run' or 'mo purge --dry-run' for advanced inspection."
fi
