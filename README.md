# mac-deep-clean 🧹

> Safe, transparent, and reproducible macOS deep storage analysis, developer cache reclamation, and orphaned application leftover cleanup.

Works both as an **AI Agent Skill** (Pi, Codex, Claude Code, Cursor) and as a **standalone CLI toolkit** on any Mac.

---

## ✨ Features

- **🛡️ 4-Layer Safety Architecture**:
  - **Zero Silent Deletion**: All scripts run in read-only preview/dry-run mode by default.
  - **Interactive Confirmation Gate**: Destructive tasks require explicit terminal `[y/N]` prompt or `--confirm` flag.
  - **Safe Trash Policy**: Orphaned application files are moved to macOS Trash (`~/.Trash/`) rather than permanently deleted with `rm -rf`, enabling one-click "Put Back" restoration.
  - **Hard-Coded Protected Whitelist**: Immunizes user personal directories (`Documents`, `Desktop`, `Pictures`, `Movies`), CloudStorage, system roots (`/System`, `/usr`), and system credentials (`Keychains`).
- **⚡ Developer & Webview Cache Reclamation**:
  - Safely recovers 15GB~30GB+ of rebuildable caches: `npm` / `npx`, `Gradle`, `uv`, `pip`, `Homebrew` bottles, `Go` build cache, `Codex` sandbox runtimes, and Electron `CacheStorage`.
- **🔍 Orphaned App Leftover Scanner**:
  - Cross-references all registered `.app` bundles across `/Applications`, `/System/Applications`, `~/Applications`, and `CoreServices`.
  - Discovers forgotten containers, group containers, preferences, and lingering `LaunchDaemons` / `PrivilegedHelperTools` from apps deleted long ago.
- **📦 Zero External Dependencies**:
  - Pure Python 3 and Bash using macOS built-in tools. Optionally integrates with [Mole (`mo`)](https://mole.fit) if installed.

---

## 📁 Repository Structure

```text
mac-deep-clean/
├── SKILL.md                          # AI Agent skill definition & execution protocol
├── README.md                         # Documentation
├── .gitignore
└── scripts/
    ├── analyze-disk.sh               # Quick storage & cache size inspector (Read-only)
    ├── clean-dev-caches.sh           # Developer cache reclaimer (Dry-run & confirmation guarded)
    └── scan-app-leftovers.py         # Orphaned app leftover scanner & safe trash cleaner
```

---

## 🚀 Usage

### Option 1: Standalone CLI (Direct Terminal)

Clone the repository and run scripts directly:

```bash
git clone https://github.com/qydxyx/mac-deep-clean.git
cd mac-deep-clean
```

#### 1. Analyze Storage & Caches
```bash
bash scripts/analyze-disk.sh
```

#### 2. Clean Developer & App Caches (Reclaim 15GB+)
```bash
# Preview what would be cleaned (no changes made):
bash scripts/clean-dev-caches.sh --dry-run

# Interactive cleanup (prompts [y/N]):
bash scripts/clean-dev-caches.sh

# Non-interactive / CI / Pre-approved run:
bash scripts/clean-dev-caches.sh --confirm
```

#### 3. Scan & Clean Orphaned App Leftovers
```bash
# Scan system and output a categorized tree (read-only):
python3 scripts/scan-app-leftovers.py

# Safely move orphaned files to macOS Trash (prompts [y/N]):
python3 scripts/scan-app-leftovers.py --clean-user

# Clean with explicit confirmation:
python3 scripts/scan-app-leftovers.py --clean-user --confirm
```

> **Note for System Daemons**: If leftover `LaunchDaemons` or `PrivilegedHelperTools` are discovered under `/Library`, `scan-app-leftovers.py` outputs the exact `sudo rm -rf ...` line for you to review and run manually.

---

### Option 2: AI Agent Skill (Pi / Codex / Claude Code)

Install into your local or global agent skills directory:

```bash
# Install to global skills directory:
mkdir -p ~/.agents/skills
cp -R mac-deep-clean ~/.agents/skills/

# Or link for Pi coding agent:
mkdir -p ~/.pi/agent/skills
ln -s ~/.agents/skills/mac-deep-clean ~/.pi/agent/skills/mac-deep-clean
```

Trigger prompts you can use with your agent:
- *"Free up disk space on my Mac and show me a tree list of cleanable files first."*
- *"Scan for leftover files from uninstalled applications."*
- *"Clean my developer caches (npm, gradle, brew, python)."*

---

## 🛡️ Protected Whitelist

The cleaner will **never** touch:
- **Personal Directories**: `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Pictures`, `~/Movies`, `~/Music`
- **Identity & Credentials**: `~/Library/Keychains`
- **Native Communication / System Data**: `Mail`, `Messages`, `Photos`, `Safari`
- **Cloud Drives**: `~/Library/CloudStorage`, `~/Library/Mobile Documents` (iCloud)
- **Active Shared Services**: Windows App / Remote Desktop (`com.microsoft.rdc`), Microsoft To Do, Paragon NTFS, etc.

---

## 📄 License

MIT License. Free to use, modify, and distribute.
