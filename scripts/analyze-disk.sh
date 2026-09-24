#!/usr/bin/env bash
#
# analyze-disk.sh - Comprehensive macOS Storage, Cache & System Bottleneck Analyzer
# Identifies space hogs across developer caches, hidden dotfiles, cloud storage,
# Spotlight bloat, and startup latency items.

set -euo pipefail

echo "========================================================"
echo " 1. macOS Disk Space Overview"
echo "========================================================"
df -h / | awk 'NR==1 || NR==2'
echo ""

echo "========================================================"
echo " 2. Developer & App Caches Status"
echo "========================================================"
check_cache() {
  local path="$1"
  local desc="$2"
  if [ -e "$path" ]; then
    local size
    size=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
    printf "  %-38s %10s (%s)\n" "$path" "$size" "$desc"
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

echo "========================================================"
echo " 3. Large Hidden Directories in Home (>100MB)"
echo "========================================================"
for d in "$HOME"/.[!.]*; do
  if [ -d "$d" ]; then
    size_kb=$(du -sk "$d" 2>/dev/null | awk '{print $1}' || echo "0")
    if [ "$size_kb" -gt 102400 ]; then # > 100MB
      size_human=$(du -sh "$d" 2>/dev/null | awk '{print $1}')
      printf "  %-38s %10s\n" "$d" "$size_human"
    fi
  fi
done
echo ""

echo "========================================================"
echo " 4. Spotlight Indexing Bloat Check"
echo "========================================================"
SPOTLIGHT_DIR="$HOME/Library/Metadata/CoreSpotlight"
if [ -d "$SPOTLIGHT_DIR" ]; then
  SPOT_SIZE_KB=$(du -sk "$SPOTLIGHT_DIR" 2>/dev/null | awk '{print $1}' || echo "0")
  SPOT_SIZE_H=$(du -sh "$SPOTLIGHT_DIR" 2>/dev/null | awk '{print $1}')
  echo "  CoreSpotlight size: $SPOT_SIZE_H ($SPOTLIGHT_DIR)"
  if [ "$SPOT_SIZE_KB" -gt 2097152 ]; then # > 2GB
    echo "  ⚠️  Spotlight metadata is bloated (>2GB). Rebuilding index can reclaim disk & speed up searches:"
    echo "     Command: sudo mdutil -E /"
  else
    echo "  [✓] Spotlight index size is healthy."
  fi
fi
echo ""

echo "========================================================"
echo " 5. Cloud Storage Local Eviction Opportunities (>100MB)"
echo "========================================================"
CLOUD_DIR="$HOME/Library/CloudStorage"
if [ -d "$CLOUD_DIR" ]; then
  FOUND_CLOUD=false
  while IFS= read -r line; do
    if [ -n "$line" ]; then
      FOUND_CLOUD=true
      echo "  $line"
    fi
  done < <(find "$CLOUD_DIR" -type f -size +100M -exec du -sh {} + 2>/dev/null | sort -hr | head -n 5)
  if [ "$FOUND_CLOUD" = true ]; then
    echo "  💡 Tip: Right-click large files in Finder and select 'Free Up Space' to keep them cloud-only."
  else
    echo "  [✓] No local files >100MB found in CloudStorage."
  fi
else
  echo "  [✓] No CloudStorage directory found."
fi
echo ""

echo "========================================================"
echo " 6. Startup Items & Input Latency Check"
echo "========================================================"
if command -v osascript >/dev/null 2>&1; then
  LOGIN_ITEMS=$(osascript -e 'tell application "System Events" to get name of every login item' 2>/dev/null || true)
  if [ -n "$LOGIN_ITEMS" ]; then
    echo "  Active Login Items: $LOGIN_ITEMS"
    ITEM_COUNT=$(echo "$LOGIN_ITEMS" | tr ',' '\n' | wc -l | tr -d ' ')
    if [ "$ITEM_COUNT" -gt 8 ]; then
      echo "  ⚠️  High login item count ($ITEM_COUNT apps). Background accessibility event-taps may introduce micro-latency."
      echo "     Review System Settings -> General -> Login Items & Extensions."
    fi
  else
    echo "  [✓] No auto-launch login items detected."
  fi
fi
echo ""

if command -v mo >/dev/null 2>&1; then
  echo "========================================================"
  echo " 7. Mole (mo) Integration"
  echo "========================================================"
  echo "  Mole CLI detected. You can run 'mo clean --dry-run' or 'mo purge --dry-run' for advanced inspection."
fi
