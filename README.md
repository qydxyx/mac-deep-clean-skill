# mac-deep-clean-skill

Storage analysis, developer cache cleanup, and orphaned file detection for macOS.

Works as a standalone command-line toolkit or as a skill for coding agents such as Pi, Codex, Claude Code, and Cursor.

## What it does

- **Developer and runtime cache cleanup**: Reclaims rebuildable caches from `npm`, `npx`, `Gradle`, `uv`, `pip`, `Homebrew`, `Go`, `Codex` sandbox runtimes, and Electron `CacheStorage`.
- **Orphaned application leftover detection**: Checks installed applications against `~/Library` and `/Library`. Identifies stranded containers, group containers, preferences, and lingering `LaunchDaemons` left behind after deleting apps.
- **Nested helper and updater detection**: Locates second-tier `.app` bundles hidden inside `Application Support` (for example, standalone updaters from software that was removed). Flags legacy Intel x86_64 binaries that trigger macOS Rosetta deprecation warnings.
- **Storage bottleneck diagnostics**: Checks for Spotlight index bloat, large local files inside cloud storage folders, and login items that hook into accessibility event taps.

## Safety model

1. **Read-only by default**: Running scripts without arguments performs a dry run. Nothing is modified until confirmed.
2. **Confirmation prompts**: Destructive actions require either an interactive `y/N` terminal prompt or the explicit `--confirm` flag.
3. **Trash instead of permanent deletion**: The leftover scanner moves user-space items to `~/.Trash` instead of using `rm -rf`, so files can be restored via Finder's Put Back feature if needed.
4. **Hard-coded protected whitelist**: System directories, user personal folders, keychains, and active shared services are never scanned or modified.

## Protected paths

The cleaner does not touch:

- Personal folders: `~/Documents`, `~/Desktop`, `~/Downloads`, `~/Pictures`, `~/Movies`, `~/Music`
- System keychains: `~/Library/Keychains`
- System application data: `Mail`, `Messages`, `Photos`, `Safari`
- Cloud storage roots: `~/Library/CloudStorage`, `~/Library/Mobile Documents` (iCloud)
- System roots: `/System`, `/usr`, `/bin`, `/sbin`, `/var`, `/private`
- Active shared services: Windows App / Remote Desktop (`com.microsoft.rdc`), Microsoft To Do, Paragon NTFS

## Project structure

```text
mac-deep-clean-skill/
├── SKILL.md                 # Agent skill instructions and rules
├── README.md                # Documentation
├── LICENSE                  # MIT License
├── .gitignore
└── scripts/
    ├── analyze-disk.sh      # Storage and system inspector (read-only)
    ├── clean-dev-caches.sh  # Developer cache cleaner
    └── scan-app-leftovers.py# Orphaned leftover and nested helper scanner
```

## Usage

### As a standalone CLI

Clone the repository:

```bash
git clone https://github.com/qydxyx/mac-deep-clean-skill.git
cd mac-deep-clean-skill
```

1. Inspect disk space, caches, and startup items:

```bash
bash scripts/analyze-disk.sh
```

2. Clean developer caches:

```bash
# Preview what would be cleaned:
bash scripts/clean-dev-caches.sh --dry-run

# Interactive cleanup (prompts for confirmation):
bash scripts/clean-dev-caches.sh

# Non-interactive cleanup:
bash scripts/clean-dev-caches.sh --confirm
```

3. Scan and remove application leftovers:

```bash
# Scan and print findings with risk levels (read-only):
python3 scripts/scan-app-leftovers.py

# Move user-space leftovers to ~/.Trash (prompts for confirmation):
python3 scripts/scan-app-leftovers.py --clean-user

# Skip prompt:
python3 scripts/scan-app-leftovers.py --clean-user --confirm

# Clean system-level leftovers under /Library (requires sudo):
sudo python3 scripts/scan-app-leftovers.py --clean-system --confirm
```

### As an agent skill

Install the directory into your agent skills path:

```bash
# Global skills directory
mkdir -p ~/.agents/skills
cp -R mac-deep-clean-skill ~/.agents/skills/

# Or symlink for Pi
mkdir -p ~/.pi/agent/skills
ln -s ~/.agents/skills/mac-deep-clean-skill ~/.pi/agent/skills/mac-deep-clean-skill
```

Example prompts:
- "Check disk space on my Mac and show cleanable files before deleting anything."
- "Scan for leftover files from uninstalled applications."
- "Clean developer caches for npm, gradle, and python."

## License

MIT License. See [LICENSE](LICENSE) for details.
