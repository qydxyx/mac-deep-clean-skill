#!/usr/bin/env python3
"""
scan-app-leftovers.py - Orphaned Application Leftover Scanner & Safe Cleaner for macOS
Detects directories, files, and hidden nested .app bundles left behind by uninstalled applications across:
- ~/Library/Application Support & /Library/Application Support
- ~/Library/Containers & ~/Library/Group Containers
- ~/Library/Saved Application State
- ~/Library/LaunchAgents & /Library/LaunchDaemons
- /Library/PrivilegedHelperTools
- Hidden nested .app helpers & updaters (e.g. Logitech, Curse/Twitch, EdgeUpdater, Karabiner)
- Orphaned home dotfiles (~/.wxwork_local, ~/.omp/puppeteer, obsolete pyenv runtimes)

Safety Protocol:
- Default action is ALWAYS read-only scanning (dry-run).
- Explicit pre-flight risk & impact disclosure before any deletion.
- Protected paths whitelist prevents touching personal documents, cloud drives, or system roots.
- Cleanup moves user-space files to macOS Trash (~/.Trash/) rather than permanent rm -rf.
- Destructive cleanup requires explicit interactive [y/N] or --confirm flag.
"""

import os
import sys
import glob
import shutil
import plistlib
import subprocess
import argparse
from datetime import datetime
from collections import defaultdict

HARD_PROTECTED_PATHS = {
    os.path.expanduser('~/Documents'),
    os.path.expanduser('~/Desktop'),
    os.path.expanduser('~/Downloads'),
    os.path.expanduser('~/Pictures'),
    os.path.expanduser('~/Movies'),
    os.path.expanduser('~/Music'),
    os.path.expanduser('~/Library/Keychains'),
    os.path.expanduser('~/Library/Mail'),
    os.path.expanduser('~/Library/Messages'),
    os.path.expanduser('~/Library/Photos'),
    os.path.expanduser('~/Library/Safari'),
    os.path.expanduser('~/Library/CloudStorage'),
    os.path.expanduser('~/Library/Mobile Documents'),
}

APPLE_SYSTEM_IGNORE = {
    'apple', 'icloud', 'addressbook', 'dock', 'syncservices', 'quick look',
    'preview', 'crashreporter', 'callhistorydb', 'systemcenter', 'macstorage',
    'fileprovider', 'knowledge', 'accountpolicy', 'coreauth', 'soundanalysis',
    'speech', 'spelling', 'bluetooth', 'com.apple.', 'mobiledevice',
    'cloudstorage', 'notificationcenter', 'screentime', 'diskimages',
    'contextstore', 'session', 'tipkit', 'accountsd', 'identityservicesd',
    'dmd', 'icdd', 'syncdefaultsd', 'transparencyd', 'voicememod',
    'videosubscriptionsd', 'privatecloudcomputed', 'servicehubd', 'stickersd',
    'trustedpeershelper', 'caches', '__caches', '__logs', 'appstore', 'proapps',
    'script editor', 'btserver', 'livefsd', 'clouddocs', 'virtualenv',
    'intelligenceplatform', 'biome', 'statuskit', 'mediaanalysis',
    'frontboard', 'personalizationportrait', 'containermanager', '.ds_store',
    'zoxide', 'nushell', 'chrome-devtools-mcp', 'smithery', 'codex',
    'codexbar', 'codexcomputeruseauthorizationplugin'
}

PROTECTED_PREFIXES = [
    'ubf8t346g9.com.microsoft.rdc',
    'ubf8t346g9.com.microsoft.to-do-mac',
    'ubf8t346g9.onedrivestandalonesuite',
    'com.microsoft.rdc',
    'com.paragon-software'
]

SAFE_NESTED_APP_ROOTS = [
    '/library/application support/script editor',
    '/library/application support/apple',
    os.path.expanduser('~/library/cloudstorage')
]

def get_installed_apps():
    installed_names = set()
    installed_bids = set()

    search_dirs = [
        '/Applications',
        '/Applications/Utilities',
        '/System/Applications',
        '/System/Applications/Utilities',
        os.path.expanduser('~/Applications'),
        '/System/Library/CoreServices',
        '/System/Library/CoreServices/Applications'
    ]

    for d in search_dirs:
        if not os.path.exists(d):
            continue
        for root, dirs, files in os.walk(d):
            depth = root[len(d):].count(os.sep)
            if depth > 2:
                dirs.clear()
                continue
            for item in dirs[:]:
                if item.endswith('.app'):
                    dirs.remove(item)
                    app_name = item[:-4].lower()
                    installed_names.add(app_name)
                    plist_path = os.path.join(root, item, 'Contents', 'Info.plist')
                    if os.path.exists(plist_path):
                        try:
                            with open(plist_path, 'rb') as fp:
                                pl = plistlib.load(fp)
                                bid = pl.get('CFBundleIdentifier')
                                if bid:
                                    installed_bids.add(str(bid).lower())
                                bname = pl.get('CFBundleName')
                                if bname:
                                    installed_names.add(str(bname).lower())
                                bdname = pl.get('CFBundleDisplayName')
                                if bdname:
                                    installed_names.add(str(bdname).lower())
                        except Exception:
                            pass
    return installed_names, installed_bids

def get_dir_size_kb(path):
    try:
        res = subprocess.run(['du', '-sk', path], capture_output=True, text=True, timeout=5)
        if res.returncode == 0 and res.stdout:
            return int(res.stdout.split()[0])
    except Exception:
        pass
    return 0

def format_size(kb):
    if kb >= 1024 * 1024:
        return f"{kb / (1024 * 1024):.2f} GB"
    if kb >= 1024:
        return f"{kb / 1024:.1f} MB"
    return f"{kb} KB"

def is_matched(name, installed_names, installed_bids):
    name_lower = name.lower()
    if any(p in name_lower for p in PROTECTED_PREFIXES):
        return True
    for app in installed_names:
        if app == name_lower or app in name_lower or name_lower in app:
            return True
    for bid in installed_bids:
        if bid in name_lower or name_lower in bid:
            return True
        # Check reverse vendor prefix
        parts = bid.split('.')
        if len(parts) >= 2:
            prefix = '.'.join(parts[:2])
            if name_lower.startswith(prefix) or prefix in name_lower:
                return True
    return False

def is_path_safe(path):
    real_p = os.path.realpath(os.path.expanduser(path))
    for prot in HARD_PROTECTED_PATHS:
        if real_p == prot or real_p.startswith(prot + os.sep):
            return False
    if real_p in {'/', '/System', '/bin', '/sbin', '/usr', '/var', '/private', '/Library'}:
        return False
    return True

def check_binary_arch(app_path):
    macos_dir = os.path.join(app_path, 'Contents', 'MacOS')
    if os.path.exists(macos_dir):
        for f in os.listdir(macos_dir):
            bin_path = os.path.join(macos_dir, f)
            if os.path.isfile(bin_path) and not os.path.islink(bin_path):
                try:
                    res = subprocess.run(['file', bin_path], capture_output=True, text=True, timeout=2)
                    out = res.stdout.lower()
                    if 'x86_64' in out and 'arm64' not in out:
                        return 'Legacy Intel x86_64 only (Triggers Rosetta retirement alert)'
                    elif 'arm64' in out:
                        return 'Universal / Apple Silicon'
                except:
                    pass
    return 'Universal / Unknown'

def scan_leftovers():
    installed_names, installed_bids = get_installed_apps()
    leftovers = defaultdict(list)

    # 1. ~/Library/Application Support
    user_as = os.path.expanduser('~/Library/Application Support')
    if os.path.exists(user_as):
        for item in os.listdir(user_as):
            p = os.path.join(user_as, item)
            il = item.lower()
            if any(ign in il for ign in APPLE_SYSTEM_IGNORE):
                continue
            if not is_matched(il, installed_names, installed_bids) and is_path_safe(p):
                sz = get_dir_size_kb(p)
                if sz > 10:
                    leftovers[item].append((p, sz, 'User AppSupport', False, 'App configuration & cache. Clean resets app settings if reinstalled.'))

    # 2. /Library/Application Support
    sys_as = '/Library/Application Support'
    if os.path.exists(sys_as):
        for item in os.listdir(sys_as):
            p = os.path.join(sys_as, item)
            il = item.lower()
            if any(ign in il for ign in APPLE_SYSTEM_IGNORE):
                continue
            if not is_matched(il, installed_names, installed_bids):
                sz = get_dir_size_kb(p)
                if sz > 10:
                    leftovers[item].append((p, sz, 'System AppSupport', True, 'System-wide templates/licenses.'))

    # 3. ~/Library/Group Containers
    gc_dir = os.path.expanduser('~/Library/Group Containers')
    if os.path.exists(gc_dir):
        for item in os.listdir(gc_dir):
            if item.lower().startswith('com.apple.') or item.lower().startswith('group.com.apple.') or item == '.ds_store':
                continue
            il = item.lower()
            if not is_matched(il, installed_names, installed_bids):
                p = os.path.join(gc_dir, item)
                if is_path_safe(p):
                    sz = get_dir_size_kb(p)
                    if sz > 50:
                        leftovers[item].append((p, sz, 'Group Container', False, 'Shared sandbox database or cache.'))

    # 4. ~/Library/Containers
    c_dir = os.path.expanduser('~/Library/Containers')
    if os.path.exists(c_dir):
        for item in os.listdir(c_dir):
            if item.lower().startswith('com.apple.') or item == '.ds_store' or (len(item) == 36 and '-' in item):
                continue
            il = item.lower()
            if not is_matched(il, installed_names, installed_bids):
                p = os.path.join(c_dir, item)
                if is_path_safe(p):
                    sz = get_dir_size_kb(p)
                    if sz > 50:
                        leftovers[item].append((p, sz, 'Container', False, 'Application sandbox directory.'))

    # 5. Stale Daemons & LaunchAgents
    known_stale = [
        ('/Library/LaunchDaemons/io.github.clash-verge-rev.clash-verge-rev.service.plist', 'Clash Verge Rev', True, 'Orphaned daemon service; causes launchd loop errors.'),
        ('/Library/PrivilegedHelperTools/io.github.clash-verge-rev.clash-verge-rev.service.bundle', 'Clash Verge Rev', True, 'Privileged binary bundle.'),
        ('/Library/PrivilegedHelperTools/com.macpaw.CleanMyMac-setapp.Agent', 'CleanMyMac', True, 'Privileged background agent.'),
        ('/Library/PrivilegedHelperTools/com.bjango.istatmenus-setapp.installerhelper', 'iStat Menus', True, 'Unused installer helper.'),
        (os.path.expanduser('~/Library/LaunchAgents/ai.perplexity.xpc.plist'), 'Perplexity AI', False, 'Dead launch agent; binary missing.')
    ]
    for lp, app_name, needs_sudo, risk_info in known_stale:
        if os.path.exists(lp):
            sz = get_dir_size_kb(lp)
            leftovers[app_name].append((lp, sz, 'Daemon/LaunchAgent', needs_sudo, risk_info))

    # 6. Orphaned Dotfiles in Home
    wework_dir = os.path.expanduser('~/.wxwork_local')
    if os.path.exists(wework_dir) and not any('wework' in a or 'wxwork' in a for a in installed_names):
        sz = get_dir_size_kb(wework_dir)
        leftovers['WeWork (企业微信)'].append((
            wework_dir, sz, 'Home Dotfile', False,
            'Historical local chat media & cache. Risk: deletes offline chat records if not backed up on phone/cloud.'
        ))

    puppeteer_dir = os.path.expanduser('~/.omp/puppeteer')
    if os.path.exists(puppeteer_dir):
        sz = get_dir_size_kb(puppeteer_dir)
        leftovers['Puppeteer Browser Bundle (~/.omp)'].append((
            puppeteer_dir, sz, 'Home Dotfile', False,
            'Old headless Chromium binary. Safe to delete; re-downloads if tool is re-run.'
        ))

    py27_dir = os.path.expanduser('~/.pyenv/versions/2.7.18')
    if os.path.exists(py27_dir):
        sz = get_dir_size_kb(py27_dir)
        leftovers['Python 2.7 (pyenv 2.7.18)'].append((
            py27_dir, sz, 'Deprecated Runtime', False,
            'Python 2.7 is end-of-life. Safe to remove unless legacy scripts explicitly require it.'
        ))

    # 7. Deep Nested Helper & Updater .app Bundles
    # Discovers second-tier executables left by uninstalled apps (Logitech, Curse/Twitch, EdgeUpdater, Karabiner)
    nested_search_dirs = [
        ('/Library/Application Support', True),
        (os.path.expanduser('~/Library/Application Support'), False),
        (os.path.expanduser('~/Library'), False)
    ]
    already_tracked = {item[0] for sublist in leftovers.values() for item in sublist}

    for base_dir, is_sys in nested_search_dirs:
        if not os.path.exists(base_dir):
            continue
        for root, dirs, files in os.walk(base_dir):
            for d in dirs[:]:
                if d.endswith('.app'):
                    full_p = os.path.join(root, d)
                    dirs.remove(d) # do not descend inside bundle
                    fp_lower = full_p.lower()
                    if any(fp_lower.startswith(sp) for sp in SAFE_NESTED_APP_ROOTS):
                        continue
                    if full_p in already_tracked:
                        continue

                    app_clean_name = d[:-4].lower()
                    matched = any(ma in app_clean_name or app_clean_name in ma for ma in installed_names)
                    if not matched:
                        # Check bundle id & vendor prefix
                        plist_f = os.path.join(full_p, 'Contents', 'Info.plist')
                        if os.path.exists(plist_f):
                            try:
                                with open(plist_f, 'rb') as fp:
                                    pl = plistlib.load(fp)
                                    bid = str(pl.get('CFBundleIdentifier', '')).lower()
                                    if any(b in bid or bid in b for b in installed_bids):
                                        matched = True
                                    parts = bid.split('.')
                                    if len(parts) >= 2:
                                        vendor_pfx = '.'.join(parts[:2])
                                        if any(b.startswith(vendor_pfx) for b in installed_bids):
                                            matched = True
                            except:
                                pass
                    # Check parent folder name
                    if not matched:
                        parent_name = os.path.basename(root).lower()
                        grandparent = os.path.basename(os.path.dirname(root)).lower()
                        if any(ma in parent_name or ma in grandparent for ma in installed_names):
                            matched = True

                    if not matched:
                        sz = get_dir_size_kb(full_p)
                        if sz > 20:
                            arch_info = check_binary_arch(full_p)
                            leftovers[f"Nested Helper: {d[:-4]}"].append((
                                full_p, sz, 'Nested Helper .app', is_sys,
                                f"Arch: {arch_info}. Orphaned helper bundle from uninstalled software."
                            ))
                            already_tracked.add(full_p)

    return leftovers

def safe_move_to_trash(target_path):
    trash_dir = os.path.expanduser('~/.Trash')
    os.makedirs(trash_dir, exist_ok=True)
    base_name = os.path.basename(target_path)
    dest_path = os.path.join(trash_dir, base_name)
    if os.path.exists(dest_path):
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        dest_path = os.path.join(trash_dir, f"{base_name}_{timestamp}")
    shutil.move(target_path, dest_path)
    return dest_path

def main():
    parser = argparse.ArgumentParser(
        description="Safe scanner & cleaner for orphaned application leftovers on macOS."
    )
    parser.add_argument("--clean-user", action="store_true", help="Remove user-space leftovers (moves to ~/.Trash).")
    parser.add_argument("-y", "--confirm", action="store_true", help="Confirm execution without interactive prompt.")
    parser.add_argument("--permanent", action="store_true", help="Bypass ~/.Trash and delete permanently via rm -rf.")
    args = parser.parse_args()

    leftovers = scan_leftovers()
    if not leftovers:
        print("[✓] No orphaned application leftovers detected. Clean system!")
        return

    total_kb = 0
    user_items = []
    sudo_commands = []

    print("========================================================")
    print(" 🔍 Orphaned Application Leftovers & Nested Helpers")
    print("========================================================")
    for app, items in sorted(leftovers.items(), key=lambda x: sum(i[1] for i in x[1]), reverse=True):
        app_total_kb = sum(i[1] for i in items)
        total_kb += app_total_kb
        print(f"\n📦 {app} [{format_size(app_total_kb)}]")
        for path, sz, cat, needs_sudo, risk in items:
            sudo_str = " (requires sudo)" if needs_sudo else ""
            print(f"  └── [{cat}] {path} ({format_size(sz)}){sudo_str}")
            print(f"      ℹ️ Impact & Risk: {risk}")
            if needs_sudo:
                sudo_commands.append(path)
            else:
                user_items.append((app, path, sz, risk))

    print(f"\n========================================================")
    print(f" Total Identified Remnants: {len(leftovers)} items | Total: {format_size(total_kb)}")
    print(f"========================================================")

    if sudo_commands:
        print("\n[!] Root-level remnants detected. Review paths carefully before running:")
        quoted = " ".join(f'"{p}"' for p in sudo_commands)
        print(f"    sudo rm -rf {quoted}")

    if not args.clean_user:
        print("\n[i] Read-only preview mode. No files were modified.")
        print("    To safely move user leftovers to ~/.Trash: python3 scan-app-leftovers.py --clean-user")
        return

    # Safety confirmation gate with explicit risk acknowledgment
    if not args.confirm:
        if sys.stdin.isatty():
            print("\n⚠️  PRE-FLIGHT CONFIRMATION:")
            print("   • Files will be moved to macOS Trash (~/.Trash/) and can be restored.")
            print("   • Ensure you have reviewed the Impact & Risk notes above.")
            prompt = "   Do you confirm moving these orphaned items to Trash? [y/N]: "
            choice = input(prompt).strip().lower()
            if choice not in ('y', 'yes'):
                print("[-] Aborted by user. No files were modified.")
                return
        else:
            print("\n[-] Error: Non-interactive session requires explicit -y or --confirm flag.")
            sys.exit(1)

    print("\n[-] Processing user-space leftovers...")
    success_count = 0
    reclaimed_kb = 0

    for app, path, sz, risk in user_items:
        if os.path.exists(path):
            try:
                if args.permanent:
                    if os.path.isdir(path) and not os.path.islink(path):
                        shutil.rmtree(path)
                    else:
                        os.remove(path)
                else:
                    safe_move_to_trash(path)
                success_count += 1
                reclaimed_kb += sz
            except Exception as e:
                print(f"  [!] Failed to remove {path}: {e}")

    method_str = "permanently deleted" if args.permanent else "moved to macOS Trash (~/.Trash/)"
    print(f"[✓] Cleanup complete! {success_count} items {method_str}. Reclaimed ~{format_size(reclaimed_kb)}.")
    if not args.permanent:
        print("    (You can restore any item from macOS Trash if needed)")

if __name__ == '__main__':
    main()
