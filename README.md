# KN5000

Reverse engineering and homebrew development for the **Technics KN5000** arranger keyboard.

**Website:** [arqueologiadigital.github.io/kn5000-docs](https://arqueologiadigital.github.io/kn5000-docs/) — hardware docs, memory maps, progress tracking

**Discussion:** [Technics KN5000 Homebrew Development](https://forum.fiozera.com.br/t/technics-kn5000-homebrew-development/321) on the Fiozera forum

## Subprojects

This repository is the central hub aggregating all related work. Each subproject lives in its own git repository:

| Directory | Repository | Description |
|-----------|------------|-------------|
| `roms-disasm/` | [kn5000-roms-disasm](https://github.com/ArqueologiaDigital/kn5000-roms-disasm) | ROM disassembly & byte-matching reconstruction |
| `mame/` | [mame](https://github.com/felipesanches/mame) | MAME emulator — KN5000 driver development |
| `llvm/` | [llvm-project](https://github.com/felipesanches/llvm-project) | Custom LLVM backend for the TLCS-900 CPU |
| `mines/` | [Mines](https://github.com/ArqueologiaDigital/Mines) | Minesweeper homebrew game (KN5000 port) |
| `custom-roms/` | [custom-kn5000-roms](https://github.com/ArqueologiaDigital/custom-kn5000-roms) | Custom ROM experiments (Another World port) |
| `docs/` | [KN5000-docs](https://github.com/ArqueologiaDigital/KN5000-docs) | Documentation website (Jekyll) |
| `original-roms/` | — | Original firmware ROM dumps (read-only reference) |

## Target Hardware

- **CPU:** TMP94C241F (Toshiba TLCS-900/H2 series) — 32-bit CISC, 16 MHz
- **Architecture:** 24-bit address bus, 16-bit external data bus
- **Display:** 320x240 8bpp LCD
- **Program ROM:** 2 MB main + 2 MB table data
- **RAM:** 4 KB internal + 256 KB extension DRAM

## Getting Started (New Contributors)

An onboarding script clones all repositories, installs Claude Code memory files (accumulated project knowledge), and verifies the toolchain:

```bash
# 1. Clone this hub repo (pick any directory you like)
git clone https://github.com/ArqueologiaDigital/KN5000.git ~/kn5000/kn5000_project

# 2. Run the onboarding script (clones all subproject repos + sets up context)
bash ~/kn5000/kn5000_project/scripts/onboard.sh ~/kn5000
```

Replace `~/kn5000` with any directory. The script is idempotent — run it again anytime to pull updates and refresh memory files.

### What the onboarding script does

1. **Clones all 7 repositories** (or pulls if already cloned)
2. **Sets up symlinks** in the central hub so all subprojects are accessible
3. **Installs Claude Code memory files** from each repo into `~/.claude/projects/` so AI agents start with full project context (LLVM encoding pitfalls, MAME emulation quirks, ROM disassembly pipeline, etc.)
4. **Verifies the Beads issue tracker** and CLI
5. **Checks the LLVM toolchain** (needed for ROM assembly builds)
6. **Runs a test build** of the ROM disassembly if the toolchain is available

### Prerequisites

- Git
- Python 3
- [Claude Code](https://docs.anthropic.com/en/docs/claude-code) (for AI-assisted development)
- LLVM build dependencies (for building the custom TLCS-900 backend): cmake, ninja, clang

### Building the LLVM toolchain

The ROM disassembly uses a custom LLVM backend for the Toshiba TLCS-900 CPU. To build it:

```bash
cd /mnt/shared/llvm-project
bash build_tlcs900.sh
```

### Building the ROMs

Once LLVM is built, verify the ROM disassembly:

```bash
cd /mnt/shared/kn5000-roms-disasm
make all                          # Build all 6 ROMs
python3 scripts/compare_roms.py   # Verify 100% byte match
```

### Key commands

```bash
cd /mnt/shared/kn5000_project
bd ready                          # See available work (Beads issue tracker)
bd list                           # List all issues
bd show <id>                      # View issue details
```

## Issue Tracker

This project uses [Beads](https://github.com/beads-ai/beads) for issue tracking. The CLI is at `/mnt/shared/tools/bd`. See `AGENTS.md` for the AI agent workflow and `CLAUDE.md` for project policies.

## License

See individual subproject repositories for licensing details.
