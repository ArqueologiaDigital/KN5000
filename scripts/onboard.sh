#!/usr/bin/env bash
#
# KN5000 Project — Contributor Onboarding Script
#
# This script clones all project repositories and sets up the Claude Code
# memory files so that new contributors (and their AI agents) can start
# with full project context instead of learning everything from scratch.
#
# Usage:
#   curl -sL <raw-github-url>/scripts/onboard.sh | bash
#   # — or —
#   bash scripts/onboard.sh [TARGET_DIR]
#
# The script is idempotent: running it again updates everything.
#

set -euo pipefail

# ---------- Configuration ----------

TARGET="${1:-/mnt/shared}"
GITHUB_ORG="ArqueologiaDigital"

# Repository map: local_dir -> github_repo
declare -A REPOS=(
  [kn5000_project]="kn5000_project"
  [kn5000-roms-disasm]="kn5000-roms-disasm"
  [llvm-project]="llvm-project"
  [mame]="mame"
  [Mines]="Mines"
  [custom-kn5000-roms]="custom-kn5000-roms"
  [kn5000-docs]="kn5000-docs"
)

# Memory file map: repo_dir -> claude_projects_key
# The key is how Claude Code encodes the working directory into
# ~/.claude/projects/<key>/memory/
declare -A MEMORY_KEYS=(
  [kn5000_project]="-mnt-shared-kn5000-project"
  [Mines]="-mnt-shared-Mines"
  [llvm-project]="-mnt-shared-llvm-project"
  [custom-kn5000-roms]="-mnt-shared-custom-kn5000-roms"
)

# ---------- Colors ----------

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info()  { echo -e "${BLUE}[INFO]${NC}  $*"; }
ok()    { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()  { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error() { echo -e "${RED}[ERROR]${NC} $*"; }

# ---------- Step 1: Clone Repositories ----------

echo ""
echo "=============================================="
echo "  KN5000 Project — Contributor Onboarding"
echo "=============================================="
echo ""
echo "Target directory: $TARGET"
echo ""

mkdir -p "$TARGET"

info "Step 1: Cloning repositories..."
echo ""

for dir in "${!REPOS[@]}"; do
  repo="${REPOS[$dir]}"
  dest="$TARGET/$dir"
  if [ -d "$dest/.git" ] || [ -f "$dest/.git" ]; then
    ok "$dir — already cloned, pulling latest..."
    (cd "$dest" && git pull --ff-only 2>/dev/null) || warn "$dir — pull failed (might have local changes)"
  else
    info "Cloning $repo..."
    git clone "https://github.com/$GITHUB_ORG/$repo.git" "$dest"
    ok "$dir — cloned"
  fi
done

echo ""

# ---------- Step 2: Set up symlinks in central hub ----------

info "Step 2: Verifying symlinks in central hub..."

HUB="$TARGET/kn5000_project"
declare -A SYMLINKS=(
  [roms-disasm]="$TARGET/kn5000-roms-disasm"
  [llvm]="$TARGET/llvm-project"
  [mame]="$TARGET/mame"
  [mines]="$TARGET/Mines"
  [custom-roms]="$TARGET/custom-kn5000-roms"
  [docs]="$TARGET/kn5000-docs"
)

for name in "${!SYMLINKS[@]}"; do
  link="$HUB/$name"
  target="${SYMLINKS[$name]}"
  if [ -L "$link" ]; then
    ok "  $name -> $(readlink "$link")"
  elif [ -e "$target" ]; then
    ln -s "$target" "$link"
    ok "  Created $name -> $target"
  else
    warn "  $name — target $target not found, skipping"
  fi
done

echo ""

# ---------- Step 3: Install Claude Code memory files ----------

info "Step 3: Installing Claude Code memory files..."
echo ""

CLAUDE_DIR="$HOME/.claude/projects"
mkdir -p "$CLAUDE_DIR"

install_memory() {
  local repo_dir="$1"
  local claude_key="$2"
  local src="$TARGET/$repo_dir/.claude/memory"
  local dest="$CLAUDE_DIR/$claude_key/memory"

  if [ ! -d "$src" ]; then
    warn "  $repo_dir — no .claude/memory/ in repo, skipping"
    return
  fi

  mkdir -p "$dest"

  local count=0
  for f in "$src"/*.md; do
    [ -f "$f" ] || continue
    local basename
    basename=$(basename "$f")
    cp "$f" "$dest/$basename"
    count=$((count + 1))
  done

  if [ $count -gt 0 ]; then
    ok "  $repo_dir — installed $count memory file(s) to $dest"
  else
    warn "  $repo_dir — .claude/memory/ exists but is empty"
  fi
}

for dir in "${!MEMORY_KEYS[@]}"; do
  install_memory "$dir" "${MEMORY_KEYS[$dir]}"
done

# Handle the special case: Another World subproject has its own memory
# stored under custom-kn5000-roms/anotherworld/.claude/memory/
AW_SRC="$TARGET/custom-kn5000-roms/anotherworld/.claude/memory"
AW_DEST="$CLAUDE_DIR/-mnt-shared-custom-kn5000-roms-anotherworld/memory"
if [ -d "$AW_SRC" ]; then
  mkdir -p "$AW_DEST"
  cp "$AW_SRC"/*.md "$AW_DEST/" 2>/dev/null && \
    ok "  custom-roms/anotherworld — installed memory files" || \
    warn "  custom-roms/anotherworld — no memory files found"
fi

echo ""

# ---------- Step 4: Verify Beads issue tracker ----------

info "Step 4: Checking Beads issue tracker..."

BEADS_DIR="$HUB/.beads"
if [ -f "$BEADS_DIR/issues.jsonl" ]; then
  issue_count=$(wc -l < "$BEADS_DIR/issues.jsonl")
  ok "  Issue tracker present: $issue_count issues"
else
  warn "  Issue tracker not found at $BEADS_DIR/issues.jsonl"
fi

# Check for bd CLI
BD="$TARGET/tools/bd"
if [ -x "$BD" ]; then
  ok "  Beads CLI found at $BD"
else
  warn "  Beads CLI not found at $BD"
  warn "  Install from: https://github.com/beads-ai/beads"
fi

echo ""

# ---------- Step 5: Verify LLVM toolchain ----------

info "Step 5: Checking LLVM toolchain (needed for ROM builds)..."

LLVM_BIN="$TARGET/llvm-project/build/bin"
if [ -x "$LLVM_BIN/llvm-mc" ] && [ -x "$LLVM_BIN/ld.lld" ]; then
  ok "  LLVM tools found (llvm-mc, ld.lld)"
else
  warn "  LLVM tools not built yet"
  warn "  To build: cd $TARGET/llvm-project && bash build_tlcs900.sh"
  warn "  This adds the custom TLCS-900 backend (required for ROM assembly)"
fi

echo ""

# ---------- Step 6: Verify ROM build ----------

info "Step 6: Checking ROM disassembly build..."

ROMS_DIR="$TARGET/kn5000-roms-disasm"
if [ -f "$ROMS_DIR/Makefile" ]; then
  if [ -x "$LLVM_BIN/llvm-mc" ]; then
    info "  Attempting build verification (make all)..."
    if (cd "$ROMS_DIR" && make all 2>&1 | tail -1 | grep -q "100.00%"); then
      ok "  ROM build: SUCCESS (100% byte match)"
    else
      warn "  ROM build: check output manually with 'cd $ROMS_DIR && make all'"
    fi
  else
    warn "  Skipping build check (LLVM not built)"
  fi
else
  warn "  ROM disassembly Makefile not found"
fi

echo ""

# ---------- Summary ----------

echo "=============================================="
echo "  Onboarding Complete"
echo "=============================================="
echo ""
echo "Repositories cloned to: $TARGET/"
echo "Claude Code memory installed to: $CLAUDE_DIR/"
echo ""
echo "Next steps:"
echo "  1. cd $HUB"
echo "  2. Read CLAUDE.md for project policies"
echo "  3. Run 'bd ready' to see available work"
echo "  4. Start Claude Code: 'claude' or 'claude-code'"
echo ""
echo "Key commands:"
echo "  Build ROMs:    cd $ROMS_DIR && make all"
echo "  Compare ROMs:  cd $ROMS_DIR && python3 scripts/compare_roms.py"
echo "  Issue tracker: cd $HUB && bd list"
echo ""
echo "To update memory files after upstream changes:"
echo "  git pull (in each repo) && bash $HUB/scripts/onboard.sh"
echo ""
