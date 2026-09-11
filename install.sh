#!/usr/bin/env bash
# Promptsmith installer and syncer
# Installs or syncs Promptsmith across Claude Code, Codex, Antigravity (agy), and OpenCode.

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
  "${HOME}/.config/opencode/skills/promptsmith"
  "${HOME}/.opencode/skills/promptsmith"
)

echo "=== Promptsmith Installer (v2.3.0) ==="
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

# OpenCode slash command (/promptsmith)
if [[ -d "${HOME}/.config/opencode/commands" || "${1:-}" == "--all" ]]; then
  "$MKDIR" -p "${HOME}/.config/opencode/commands"
  cat <<EOF > "${HOME}/.config/opencode/commands/promptsmith.md"
---
description: Craft or improve a prompt for an LLM or coding agent following prompt-engineering best practices
argument-hint: "[--mode <brief|rules|general|compress>] <task or intent>"
tools:
  read: true
  write: true
  edit: true
  bash: true
---
<objective>
Invoke Promptsmith to craft, refine, compress, or audit a prompt or agent brief according to Promptsmith's 7-pillar rubric.
</objective>

<execution_context>
@\${HOME}/.config/opencode/skills/promptsmith/SKILL.md
</execution_context>

<context>
Arguments: \$ARGUMENTS
</context>

<process>
Read and follow @\${HOME}/.config/opencode/skills/promptsmith/SKILL.md with \$ARGUMENTS.
Use the tools and reference guides in \${HOME}/.config/opencode/skills/promptsmith/references/ and \${HOME}/.config/opencode/skills/promptsmith/tools/ to generate, audit, or refine the prompt.
</process>
EOF
  echo "  [+] Installed OpenCode command: ${HOME}/.config/opencode/commands/promptsmith.md"
fi

echo
if [[ $installed_count -gt 0 ]]; then
  echo "Done! Installed to $installed_count target harness(es)."
  echo "Usage:"
  echo "  - Claude Code:  /promptsmith"
  echo "  - Codex:        \$promptsmith"
  echo "  - Antigravity:  /promptsmith"
  echo "  - OpenCode:     /promptsmith"
else
  echo "No active AI harness directories found in home folder."
  echo "Run with --all to force creation of all target skill directories."
fi
