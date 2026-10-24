#!/bin/bash
# install.sh — Install specific skills from the Skillforge repo
#
# Usage:
#   ./install.sh <group/skill>              # install a single skill
#   ./install.sh <group>                    # install all skills in a group
#   ./install.sh --list                     # list available groups and skills
#   ./install.sh --all                      # install everything
#   ./install.sh --platform cursor <group>  # install to Cursor's skill dir
#
# Environment variables:
#   SKILLS_INSTALL_DIR  — target directory (overrides --platform)
#
# Examples:
#   ./install.sh google-drive/gdrive-save
#   ./install.sh thinking-patterns
#   ./install.sh --platform cursor thinking-patterns
#   ./install.sh --all
#   SKILLS_INSTALL_DIR=./my-skills ./install.sh thinking-patterns

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SKILLS_SRC="$SCRIPT_DIR/skills"
PLATFORM="claude-code"

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

detect_os() {
  case "$(uname -s)" in
    Darwin)  echo "macOS" ;;
    Linux)   echo "Linux" ;;
    MINGW*|MSYS*|CYGWIN*)
      echo -e "${YELLOW}⚠${NC}  Detected Windows shell ($(uname -s)). This script works best under WSL or Git Bash." >&2
      echo "Windows"
      ;;
    *)
      echo -e "${YELLOW}⚠${NC}  Unrecognized OS: $(uname -s). Proceeding anyway." >&2
      echo "Unknown"
      ;;
  esac
}

resolve_install_dir() {
  if [ -n "${SKILLS_INSTALL_DIR:-}" ]; then
    echo "$SKILLS_INSTALL_DIR"
    return
  fi

  case "$PLATFORM" in
    claude-code) echo "$HOME/.claude/skills" ;;
    cursor)      echo "$HOME/.cursor/skills" ;;
    claude-ai)
      echo ""
      return
      ;;
    *)
      echo -e "${RED}✗${NC}  Unknown platform: $PLATFORM" >&2
      echo -e "   Supported: claude-code, cursor, claude-ai" >&2
      exit 1
      ;;
  esac
}

show_claude_ai_instructions() {
  echo ""
  echo -e "${BOLD}claude.ai — Manual Upload Instructions${NC}"
  echo ""
  echo "  claude.ai requires uploading skills as ZIP files."
  echo "  Requires a Pro, Max, Team, or Enterprise plan with code execution enabled."
  echo ""
  echo -e "  ${BOLD}Step 1: Package the skill as a ZIP${NC}"
  echo ""
  echo "    cd skills/<group>"
  echo "    zip -r <skill-name>.zip <skill-name>/"
  echo ""
  echo "    The ZIP must contain the skill folder as its root:"
  echo ""
  echo -e "      ${GREEN}Correct:${NC}  analogy-engine.zip → analogy-engine/SKILL.md"
  echo -e "      ${RED}Wrong:${NC}    analogy-engine.zip → SKILL.md (files directly in root)"
  echo ""
  echo -e "  ${BOLD}Step 2: Upload to claude.ai${NC}"
  echo ""
  echo "    1. Open https://claude.ai"
  echo -e "    2. Click ${CYAN}Customize${NC} (left sidebar)"
  echo -e "    3. Click ${CYAN}Skills${NC} at the top"
  echo -e "    4. Click the ${CYAN}+${NC} button → ${CYAN}Upload a skill${NC}"
  echo "    5. Select your .zip file"
  echo "    6. Toggle the skill on to activate it"
  echo ""
  echo -e "  Skill folders are located under: ${CYAN}$SKILLS_SRC/<group>/<skill>/${NC}"
  echo ""
}

usage() {
  echo "Usage: $0 [--platform <platform>] <group/skill|group|--all|--list>"
  echo ""
  echo "Options:"
  echo "  --platform <p>  Target platform: claude-code (default), cursor, claude-ai"
  echo "  --list          List available groups and skills"
  echo "  --all           Install all skills"
  echo "  --help          Show this help"
  echo ""
  echo "Arguments:"
  echo "  <group>         Install all skills in a group (e.g., obsidian)"
  echo "  <group/skill>   Install a specific skill (e.g., google-drive/gdrive-save)"
  echo ""
  echo "Environment:"
  echo "  SKILLS_INSTALL_DIR  Target directory (overrides --platform)"
  echo ""
  echo "Examples:"
  echo "  $0 google-drive/gdrive-save"
  echo "  $0 thinking-patterns"
  echo "  $0 --platform cursor obsidian"
  echo "  $0 --all"
  echo ""
  echo "Available skills:"
  list_skills
}

list_skills() {
  for group_dir in "$SKILLS_SRC"/*/; do
    [ -d "$group_dir" ] || continue
    local group_name
    group_name=$(basename "$group_dir")
    local has_skills=false

    for skill_dir in "$group_dir"/*/; do
      [ -f "$skill_dir/SKILL.md" ] || continue
      if [ "$has_skills" = false ]; then
        echo ""
        echo -e "  ${BOLD}${group_name}/${NC}"
        has_skills=true
      fi
      local skill_name
      skill_name=$(basename "$skill_dir")
      local desc
      desc=$(awk '/^description:/{
        sub(/^description: *>? */, "");
        if ($0 != "") { print; exit }
        getline; sub(/^ +/, ""); print; exit
      }' "$skill_dir/SKILL.md" 2>/dev/null)
      printf "    ${GREEN}%-30s${NC} %s\n" "$skill_name" "$desc"
    done
  done
}

install_skill() {
  local group="$1"
  local skill="$2"
  local src="$SKILLS_SRC/$group/$skill"
  local dest="$3"

  if [ ! -d "$src" ]; then
    echo -e "  ${RED}✗${NC}  Skill '${group}/${skill}' not found"
    return 1
  fi

  if [ ! -f "$src/SKILL.md" ]; then
    echo -e "  ${YELLOW}⚠${NC}  Skill '${group}/${skill}' has no SKILL.md — skipping"
    return 1
  fi

  echo -e "  Installing ${GREEN}${group}/${skill}${NC} → $dest/$skill/"
  mkdir -p "$dest/$skill"
  cp -r "$src"/* "$dest/$skill/"
  echo -e "  ${GREEN}✓${NC}  $group/$skill installed"
}

install_group() {
  local group="$1"
  local dest="$2"
  local group_dir="$SKILLS_SRC/$group"

  if [ ! -d "$group_dir" ]; then
    echo -e "  ${RED}✗${NC}  Group '${group}' not found in skills/"
    return 1
  fi

  local found=false
  for skill_dir in "$group_dir"/*/; do
    [ -f "$skill_dir/SKILL.md" ] || continue
    found=true
    install_skill "$group" "$(basename "$skill_dir")" "$dest"
  done

  if [ "$found" = false ]; then
    echo -e "  ${YELLOW}⚠${NC}  Group '${group}' has no installable skills"
    return 1
  fi
}

# --- Parse arguments ---

ARGS=()
while [ $# -gt 0 ]; do
  case "$1" in
    --platform)
      PLATFORM="$2"
      shift 2
      ;;
    *)
      ARGS+=("$1")
      shift
      ;;
  esac
done
set -- "${ARGS[@]+"${ARGS[@]}"}"

OS=$(detect_os)

if [ "$PLATFORM" = "claude-ai" ]; then
  show_claude_ai_instructions
  exit 0
fi

if [ $# -eq 0 ]; then
  usage
  exit 1
fi

SKILLS_DIR=$(resolve_install_dir)

case "$1" in
  --help|-h)
    usage
    exit 0
    ;;
  --list|-l)
    echo "Available skills:"
    list_skills
    echo ""
    exit 0
    ;;
  --all)
    echo -e "Platform: ${CYAN}${PLATFORM}${NC}  |  OS: ${CYAN}${OS}${NC}"
    echo "Installing all skills to: $SKILLS_DIR"
    echo ""
    mkdir -p "$SKILLS_DIR"
    for group_dir in "$SKILLS_SRC"/*/; do
      [ -d "$group_dir" ] || continue
      group_name=$(basename "$group_dir")
      for skill_dir in "$group_dir"/*/; do
        [ -f "$skill_dir/SKILL.md" ] || continue
        install_skill "$group_name" "$(basename "$skill_dir")" "$SKILLS_DIR"
      done
    done
    ;;
  *)
    echo -e "Platform: ${CYAN}${PLATFORM}${NC}  |  OS: ${CYAN}${OS}${NC}"
    echo "Installing skills to: $SKILLS_DIR"
    echo ""
    mkdir -p "$SKILLS_DIR"
    for target in "$@"; do
      if [[ "$target" == */* ]]; then
        # group/skill format
        group="${target%%/*}"
        skill="${target#*/}"
        install_skill "$group" "$skill" "$SKILLS_DIR"
      else
        # group-only — install all skills in the group
        install_group "$target" "$SKILLS_DIR"
      fi
    done
    ;;
esac

echo ""
echo -e "${GREEN}Done.${NC} Skills installed to: $SKILLS_DIR"
