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

## Issue Tracker

This project uses [Beads](https://github.com/beads-ai/beads) for issue tracking. See `AGENTS.md` for the workflow.

## License

See individual subproject repositories for licensing details.
