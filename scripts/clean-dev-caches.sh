#!/usr/bin/env bash
#
# clean-dev-caches.sh - Standalone macOS Developer & Application Cache Cleaner
# Reclaims 10GB-30GB+ of stale developer caches, webview storages, and build artifacts.
# Safe: only removes recreatable caches, never touches source code, configs, or documents.

set -euo pipefail

DRY_RUN=false
CONFIRMED=false

for arg in "$@"; do
  case "$arg" in
    -n|--dry-run)
      DRY_RUN=true
      ;;
    -y|--confirm)
      CONFIRMED=true
      ;;
    -h|--help)
      echo "Usage: $0 [OPTIONS]"
      echo ""
      echo "Options:"
      echo "  -n, --dry-run   Preview items to be deleted without removing anything"
      echo "  -y, --confirm   Execute cleanup without interactive confirmation prompt"
      echo "  -h, --help      Show this help message"
      exit 0
      ;;
    *)
      echo "Unknown option: $arg"
      echo "Run with -h or --help for usage."
      exit 1
      ;;
  esac
done

echo "========================================================"
echo " macOS Developer & Cache Space Reclaimer"
echo "========================================================"

TARGETS=(
  "$HOME/.npm/_cacache:npm package cache"
  "$HOME/.npm/_npx:npx temporary execution cache"
  "$HOME/Library/Caches/node-gyp:node-gyp headers"
  "$HOME/.gradle/caches:Gradle dependencies & build transforms"
  "$HOME/.cache/uv:uv wheels & downloads"
  "$HOME/Library/Caches/pip:pip wheel cache"
  "$HOME/Library/Caches/go-build:Go build object cache"
  "$HOME/Library/Caches/Homebrew:Homebrew download bottles"
  "$HOME/.cache/codex-runtimes:Codex primary sandbox runtimes"
  "$HOME/.cache/opencode/npm:OpenCode npm cache"
  "$HOME/Library/Application Support/Notion/Partitions/notion/Service Worker/CacheStorage:Notion Service Worker Cache"
  "$HOME/Library/Caches/camoufox:Camoufox test browser cache"
  "$HOME/Library/Caches/zen:Zen browser web cache"
  "$HOME/Library/Caches/cherrystudio-updater:CherryStudio updater downloads"
  "$HOME/Library/Caches/gooeypi-updater:Gooeypi updater downloads"
  "$HOME/Library/Caches/notion-updater:Notion updater downloads"
  "$HOME/Library/Containers/com.tencent.xinWeChat/Data/.wxapplet/WMPF:WeChat mini-program fastload cache"
)

TOTAL_SIZE_KB=0
FOUND_TARGETS=()

for entry in "${TARGETS[@]}"; do
  path="${entry%%:*}"
  desc="${entry##*:}"
  if [ -e "$path" ]; then
    size_kb=$(du -sk "$path" 2>/dev/null | awk '{print $1}' || echo "0")
    if [ "$size_kb" -gt 0 ]; then
      size_human=$(du -sh "$path" 2>/dev/null | awk '{print $1}')
      TOTAL_SIZE_KB=$((TOTAL_SIZE_KB + size_kb))
      FOUND_TARGETS+=("$path|$desc|$size_human")
    fi
  fi
done

TOTAL_HUMAN=$(awk "BEGIN {printf \"%.2f GB\", $TOTAL_SIZE_KB / 1024 / 1024}")
echo "Discovered cleanable caches: ${#FOUND_TARGETS[@]} items (approx. $TOTAL_HUMAN)"
echo ""

for item in "${FOUND_TARGETS[@]}"; do
  IFS='|' read -r p d s <<< "$item"
  printf "  • %-32s : %8s (%s)\n" "$d" "$s" "$p"
done
echo ""

if [ "$DRY_RUN" = true ]; then
  echo "[i] Dry-run mode active. No files were modified."
  exit 0
fi

# Safety Gate: require confirmation
if [ "$CONFIRMED" = false ]; then
  if [ -t 0 ]; then
    read -r -p "⚠️  Are you sure you want to delete these caches? [y/N]: " choice
    case "$choice" in
      y|Y|yes|YES)
        ;;
      *)
        echo "[-] Aborted by user. No files were deleted."
        exit 0
        ;;
    esac
  else
    echo "[-] Error: Non-interactive session detected without --confirm flag."
    echo "    To preview:  $0 --dry-run"
    echo "    To execute:  $0 --confirm"
    exit 1
  fi
fi

echo "[-] Executing cleanup..."
BEFORE_AVAIL=$(df -k / | awk 'NR==2 {print $4}')

for item in "${FOUND_TARGETS[@]}"; do
  IFS='|' read -r p d s <<< "$item"
  echo "  Removing: $d ($s)..."
  rm -rf "$p"
done

# Run tool native cache clean commands if available
command -v uv >/dev/null 2>&1 && uv cache clean >/dev/null 2>&1 || true
command -v go >/dev/null 2>&1 && go clean -cache >/dev/null 2>&1 || true
command -v brew >/dev/null 2>&1 && brew cleanup -s >/dev/null 2>&1 || true
find "$HOME/Library/Containers/com.tencent.xinWeChat/Data/Documents/app_data/log" -name "*.xlog" -delete 2>/dev/null || true

AFTER_AVAIL=$(df -k / | awk 'NR==2 {print $4}')
FREED_KB=$((AFTER_AVAIL - BEFORE_AVAIL))
if [ "$FREED_KB" -gt 0 ]; then
  FREED_MB=$((FREED_KB / 1024))
  echo "========================================================"
  echo " [✓] Cleanup completed! Space reclaimed: ~${FREED_MB} MB"
  echo "========================================================"
else
  echo "========================================================"
  echo " [✓] Cleanup completed."
  echo "========================================================"
fi
