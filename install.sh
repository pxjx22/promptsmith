#!/usr/bin/env bash
# Promptsmith installer and syncer
# Installs or syncs Promptsmith across Claude Code, Codex, and Antigravity (agy).

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
CP=/usr/bin/cp
[[ -x "$CP" ]] || CP=cp
MKDIR=/usr/bin/mkdir
[[ -x "$MKDIR" ]] || MKDIR=mkdir

DESTS=(
  "${HOME}/.claude/skills/promptsmith"
  "${HOME}/.codex/skills/promptsmith"
  "${HOME}/.gemini/config/skills/promptsmith"
)

echo "=== Promptsmith Installer (v2.1.0) ==="
echo "Source: $SCRIPT_DIR"
echo

installed_count=0
for dest in "${DESTS[@]}"; do
  parent="$(dirname "$dest")"
  # Check if parent harness directory exists or user wants all created
  if [[ -d "$parent" || "${1:-}" == "--all" ]]; then
    rm -rf "$dest"
    "$MKDIR" -p "$dest"
    "$CP" -a "$SCRIPT_DIR/SKILL.md" "$dest/"
    "$CP" -a "$SCRIPT_DIR/agents" "$dest/"
    "$CP" -a "$SCRIPT_DIR/references" "$dest/"
    [[ -d "$SCRIPT_DIR/tools" ]] && "$CP" -a "$SCRIPT_DIR/tools" "$dest/"
    echo "  [+] Installed to: $dest"
    installed_count=$((installed_count + 1))
  else
    echo "  [-] Skipped: $dest (harness directory $parent not found)"
  fi
done

# Legacy mirror for older agy discovery compatibility
if [[ -d "${HOME}/.gemini/skills" ]]; then
  rm -rf "${HOME}/.gemini/skills/promptsmith"
  "$CP" -a "${HOME}/.gemini/config/skills/promptsmith" "${HOME}/.gemini/skills/promptsmith"
  echo "  [+] Mirrored to: ${HOME}/.gemini/skills/promptsmith (legacy)"
fi

echo
if [[ $installed_count -gt 0 ]]; then
  echo "Done! Installed to $installed_count target harness(es)."
  echo "Usage:"
  echo "  - Claude Code:  /promptsmith"
  echo "  - Codex:        \$promptsmith"
  echo "  - Antigravity:  /promptsmith"
else
  echo "No active AI harness directories found in home folder."
  echo "Run with --all to force creation of all target skill directories."
fi
