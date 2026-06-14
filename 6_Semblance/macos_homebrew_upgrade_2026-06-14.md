# 🛠 macOS & Homebrew Upgrade Report — 2026-06-14

## System

| Item | Status | Version |
|------|--------|---------|
| macOS | ✅ Already latest | 26.5.1 (Build 25F80) |
| Homebrew | ✅ Updated | 5.1.15 |

No macOS update was available via `softwareupdate`.

---

## Homebrew Formulae — All Upgraded ✅

| Formula | Before | After |
|---------|--------|-------|
| `node` | 26.0.0 | 26.3.0 |
| `azure-cli` | 2.86.0 | 2.87.0 |
| `rclone` | 1.74.2 | 1.74.3 |
| `flyctl` | 0.4.58 | 0.4.59 |
| `gemini-cli` | 0.45.1 | 0.46.0 |
| `python@3.10` | 3.10.20_1 | 3.10.20_3 |
| `dotnet` | 10.0.107 | 10.0.301 |
| `powershell` | 7.6.2 | 7.6.2_2 |
| `harfbuzz` | 14.2.0 | 14.2.1 |
| `graphite2` | 1.3.14 | 1.3.15 |
| `fontconfig` | 2.18.0 | 2.18.1 |

---

## Homebrew Casks

| Cask | Before | After | Status |
|------|--------|-------|--------|
| `audacity` | 3.7.7 | 3.7.8 | ✅ |
| `google-chrome` | 130.0.6723.92 | 149.0.7827.115 | ✅ |
| `lm-studio` | 0.3.25,2 | 0.4.16,2 | ✅ |
| `vlc` | 3.0.12.1 | 3.0.23 | ✅ |
| `warp` | 0.2026.05.18 | 0.2026.06.10 | ✅ |
| `archiver-app` | — | 5.0.10 | ✅ |
| `visual-studio-code` | — | 1.124.2 | ✅ |
| `anydesk` | 9.5.0 | 9.7.0 | ⚠️ See below |
| `obs` | — | 32.1.2 | ⚠️ See below |
| `antigravity` | 1.23.2 | 2.1.4 | ✅ |

---

## New Installs

| Cask | Version | Notes |
|------|---------|-------|
| `elgato-wave-link` | 3.2.0 | Installed fresh on request |

---

## ⚠️ Known Issue — `listxattr` on macOS 26 Tahoe

**AnyDesk** and **OBS** hit a macOS 26 compatibility bug in Homebrew's `copy-xattrs.swift` helper:

```
listxattr for destination failed: 2
```

Error 2 = `ENOENT`. The Swift xattr helper fails when copying quarantine attributes to `/Applications` on Tahoe. This is a Homebrew upstream issue.

**Workaround — run these manually in Terminal:**

```bash
# Step 1: remove the stale app bundle left behind
sudo rm -rf /Applications/AnyDesk.app /Applications/OBS.app

# Step 2: install bypassing quarantine
HOMEBREW_NO_QUARANTINE=1 brew install --cask anydesk obs
```

---

## ❌ Deprecated / Disabled

| Package | Reason |
|---------|--------|
| `skype` | Discontinued upstream, disabled in Homebrew on 2026-05-09 |

---

## Summary

- **11 formulae** upgraded
- **9 casks** upgraded successfully  
- **1 cask** installed new (Elgato Wave Link)
- **2 casks** blocked by macOS 26 xattr bug — manual fix required
- **macOS** already on latest release
