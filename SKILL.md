---
name: mac-deep-clean
description: >
  Deep disk space analysis, developer cache reclamation (npm, Gradle, uv, pip,
  Homebrew, Go, Codex runtimes), and orphaned application leftover detection &
  cleanup on macOS. Use when asked to free disk space, analyze storage hogs,
  inspect cleanable files, scan/clean leftovers from uninstalled apps, or prune
  stale developer caches and build artifacts.
---

# Mac Deep Clean, Developer Cache & App Leftover Reclaimer

Safe, reproducible workflow and automated toolset for macOS deep storage analysis, developer cache reclamation, and orphaned app leftover cleanup.

---

## 🛡️ Safety Architecture & Confirmation Policy

To guarantee zero accidental data loss or system instability, this skill adheres to a strict 4-layer safety policy:

1. **Zero Silent Deletion (Default Read-Only)**:
   - All tools run in scan/preview mode by default.
   - Deletion commands (`--clean-user`, `clean-dev-caches.sh`) require interactive prompt `[y/N]` or explicit `-y` / `--confirm`.
   - Running in non-interactive mode without `--confirm` aborts automatically with zero files touched.

2. **Mandatory Tree Review**:
   - Before requesting deletion confirmation, the agent must output an itemized ASCII tree with path, size, and category.

3. **Safe Trash Policy (Put-Back Enabled)**:
   - `scan-app-leftovers.py` moves user-space files to macOS Trash (`~/.Trash/`) by default instead of permanent `rm -rf`.
   - Any accidentally moved item can be restored instantly via Finder ("Put Back").

4. **Hard Protected Whitelist**:
   - The following paths are strictly immune to scanning and cleanup:
     - User personal folders: `~/Documents`, `~/Desktop`, `~/Pictures`, `~/Movies`, `~/Music`
     - System keychains and identity stores: `~/Library/Keychains`
     - System data: `~/Library/Mail`, `~/Library/Messages`, `~/Library/Photos`, `~/Library/Safari`
     - Cloud storage: `~/Library/CloudStorage`, `~/Library/Mobile Documents`
     - System roots: `/System`, `/usr`, `/bin`, `/sbin`, `/var`, `/private`
     - Protected ecosystem services: Windows App / Remote Desktop (`UBF8T346G9.com.microsoft.rdc`), To Do (`UBF8T346G9.com.microsoft.to-do-mac`), OneDrive

---

## Capabilities & Architecture

```text
mac-deep-clean/
├── SKILL.md                          # Workflow rules, safety policies & triage
└── scripts/
    ├── analyze-disk.sh               # Native disk storage & cache inspector (Read-only)
    ├── clean-dev-caches.sh           # Safe developer cache reclaimer (Dry-run / Confirmation guarded)
    └── scan-app-leftovers.py         # Orphaned app leftover scanner & safe cleaner (Trash-first)
```

---

## Workflow 1: Storage Analysis & Developer Cache Reclamation

### Phase 1: Storage Analysis & Triage (Read-Only)
```bash
# 1. Available disk space
df -h /

# 2. Mole inspection (if installed)
mo analyze --json
mo clean --dry-run

# 3. Native inspection fallback
bash "<skill-dir>/scripts/analyze-disk.sh"
```

### Phase 2: Tree Review
Present the discovered cleanable items in a categorized tree for user review.

### Phase 3: Safe Cleanup Execution
```bash
# Preview mode (no changes made):
bash "<skill-dir>/scripts/clean-dev-caches.sh" --dry-run

# Interactive execution (prompts [y/N]):
bash "<skill-dir>/scripts/clean-dev-caches.sh"

# Pre-confirmed execution (when user explicitly approved in chat):
bash "<skill-dir>/scripts/clean-dev-caches.sh" --confirm
```

---

## Workflow 2: Orphaned App Leftovers Scanning & Cleaning

### Target Locations
- `~/Library/Application Support/` & `/Library/Application Support/`
- `~/Library/Containers/`
- `~/Library/Group Containers/`
- `~/Library/Saved Application State/`
- `~/Library/LaunchAgents/` & `/Library/LaunchDaemons/`
- `/Library/PrivilegedHelperTools/`
- `~/Library/Preferences/`

### Execution Steps
1. **Scan and generate Tree review (Read-only)**:
   ```bash
   python3 "<skill-dir>/scripts/scan-app-leftovers.py"
   ```
   Cross-references installed applications against bundles and names. Evaluates safety against the protected whitelist.

2. **Clean user-space leftovers (Safe Trash Mode)**:
   ```bash
   # Prompts [y/N] in terminal, moves items to ~/.Trash/:
   python3 "<skill-dir>/scripts/scan-app-leftovers.py" --clean-user

   # With pre-approved confirmation:
   python3 "<skill-dir>/scripts/scan-app-leftovers.py" --clean-user --confirm
   ```

3. **System-level remnants (Daemons & Helper Tools)**:
   Root-level files under `/Library/LaunchDaemons` and `/Library/PrivilegedHelperTools` are NEVER deleted automatically. The script outputs the exact `sudo rm -rf ...` line for user inspection and manual execution.

---

## Post-Verification
```bash
df -h /
```
Compare before/after disk metrics and report total reclaimed gigabytes.
