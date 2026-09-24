---
name: mac-deep-clean-skill
description: >
  Deep disk space analysis, developer cache reclamation (npm, Gradle, uv, pip,
  Homebrew, Go, Codex runtimes), orphaned app & dotfile leftover detection,
  Spotlight index optimization, and macOS system performance tuning.
  Use when asked to free disk space, analyze storage hogs, inspect cleanable
  files, scan/clean leftovers from uninstalled apps, or optimize Mac system speed.
---

# Mac Deep Clean, Developer Cache & App Leftover Reclaimer

Safe, reproducible workflow and automated toolset for macOS deep storage analysis, developer cache reclamation, orphaned app leftover cleanup, and system latency tuning.

---

## 🛡️ Mandatory Safety & Risk Disclosure Protocol

To maximize macOS storage reclamation while guaranteeing 100% stability of the operating system and active applications, this skill enforces a strict 4-layer protocol:

### 1. Four-Tier Risk Classification
Before requesting deletion confirmation, every candidate path **MUST** be classified and disclosed with its risk level:
- **🟢 Zero Risk**: Rebuildable developer caches (npm, uv, brew bottles), auto-update staging clones (`code_sign_clone`), unmounted/mounted update DMGs in `/var/folders/`, dead privileged helpers, and empty directories.
- **🟡 Low Risk**: Application configurations, databases, and sandboxes of apps confirmed uninstalled from `/Applications`. Impact: Resets user preferences if the app is ever reinstalled.
- **🟠 Medium Risk**: Historical local offline chats or tool caches (e.g. `~/.wxwork_local`). Impact: Permanently deletes offline media; user must ensure data is backed up on phone or cloud.
- **🔴 System Protected (Immune)**: Untouchable directories (see Hard Protected Whitelist below).

### 2. Mandatory Pre-Flight Risk & Data Disclosure
The agent **MUST** present an itemized ASCII tree / categorized list with paths, sizes, and risk levels before suggesting or executing any deletion.

### 3. Safe Trash Policy (Put-Back Enabled)
- `scan-app-leftovers.py` moves user-space files to macOS Trash (`~/.Trash/`) by default instead of permanent `rm -rf`.
- Any accidentally moved item can be restored instantly via Finder ("Put Back").

### 4. Hard Protected Whitelist
The following paths are strictly immune to scanning and cleanup:
- **Personal Directories**: `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Pictures`, `~/Movies`, `~/Music`
- **Identity & Credentials**: `~/Library/Keychains`
- **Native Communication / System Data**: `Mail`, `Messages`, `Photos`, `Safari`
- **Cloud Drives**: `~/Library/CloudStorage`, `~/Library/Mobile Documents` (iCloud)
- **Active Shared Services**: Windows App / Remote Desktop (`UBF8T346G9.com.microsoft.rdc`), Microsoft To Do, Paragon NTFS, etc.
- **System Roots**: `/System`, `/usr`, `/bin`, `/sbin`, `/var`, `/private`

---

## Capabilities & Architecture

```text
mac-deep-clean-skill/
├── SKILL.md                          # Workflow rules, safety policies & triage
├── README.md                         # Documentation & CLI usage
├── LICENSE                           # MIT License
├── .gitignore
└── scripts/
    ├── analyze-disk.sh               # Storage, caches, Spotlight, cloud & startup inspector (Read-only)
    ├── clean-dev-caches.sh           # Developer cache reclaimer (Dry-run & confirmation guarded)
    └── scan-app-leftovers.py         # Orphaned app & dotfile leftover scanner & safe cleaner (Trash-first)
```

---

## Workflow 1: Storage Analysis & Developer Cache Reclamation

### Phase 1: Storage & Bottleneck Analysis (Read-Only)
```bash
# 1. Available disk space
df -h /

# 2. Comprehensive storage, cache, dotfile, Spotlight & startup check:
bash "<skill-dir>/scripts/analyze-disk.sh"

# 3. Mole inspection (if installed)
mo analyze --json
mo clean --dry-run
```

### Phase 2: Tree Review & Risk Disclosure
Present discovered cleanable items in a categorized tree with 🟢 Zero Risk notes.
- *Impact*: Files will automatically re-download or re-compile on next build.

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

## Workflow 2: Orphaned App Leftovers & Home Dotfiles Safe Cleaner

Scans for remnants left behind when apps were deleted by dragging to Trash, plus orphaned home dotfiles and nested `.app` helpers.

### Target Locations
- `~/Library/Application Support/` & `/Library/Application Support/`
- `~/Library/Containers/` & `~/Library/Group Containers/`
- `~/Library/Saved Application State/`
- `~/Library/LaunchAgents/` & `/Library/LaunchDaemons/`
- `/Library/PrivilegedHelperTools/`
- Deep nested `.app` bundles (e.g. Logitech, Curse/Twitch, EdgeUpdater, Karabiner)
- `/private/var/folders/` orphaned update staging & mounted DMGs
- Kernel & DriverKit ghost extensions (`systemextensionsctl`)
- Orphaned dotfiles: `~/.wxwork_local` (WeWork chat data), `~/.omp/puppeteer`, `~/.pyenv/versions/2.7*`

### Execution Steps
1. **Scan and generate Tree review with Risk Notes (Read-only)**:
   ```bash
   python3 "<skill-dir>/scripts/scan-app-leftovers.py"
   ```

2. **Clean user-space leftovers (Safe Trash Mode)**:
   ```bash
   # Prompts [y/N] in terminal, moves items to ~/.Trash/:
   python3 "<skill-dir>/scripts/scan-app-leftovers.py" --clean-user

   # With pre-approved confirmation:
   python3 "<skill-dir>/scripts/scan-app-leftovers.py" --clean-user --confirm
   ```

3. **Clean confirmed system-level remnants (Root Mode with Sudo)**:
   ```bash
   # Cleans confirmed root /Library leftovers and garbage-collects ghost extensions:
   sudo python3 "<skill-dir>/scripts/scan-app-leftovers.py" --clean-system --confirm
   ```

---

## Workflow 3: Spotlight Index Optimization (Metadata Rebuild)

Over time, macOS CoreSpotlight accumulates fragmented journals and deleted file references (`~/Library/Metadata/CoreSpotlight` > 2GB~5GB).

- **Risk Disclosure**: Re-indexing consumes moderate `mdworker` CPU for 10-30 minutes after initiation. Spotlight searches may be temporarily incomplete during the re-index.
- **Action**:
  ```bash
  sudo mdutil -E /System/Volumes/Data
  ```

---

## Workflow 4: Cloud Storage Local Eviction & Autostart Latency Tuning

1. **Cloud Storage Local Eviction (`~/Library/CloudStorage`)**:
   - *Risk Disclosure*: Files are NOT deleted from cloud; only local SSD copies are evicted. Internet connection will be required to re-open evicted files.
   - *Action*: In Finder, select large files/folders and click **"Free Up Space"** (释放空间).

2. **Input & UI Latency Tuning (Login Items)**:
   - *Issue*: High counts of menu bar / accessibility utility apps introduce micro-latency in mouse/keyboard event dispatch via `CGEventTap`.
   - *Action*: Review `System Settings -> General -> Login Items & Extensions` to prune redundant background tools.

---

## Post-Verification
```bash
df -h /
```
Compare before/after disk metrics and report total reclaimed gigabytes.
