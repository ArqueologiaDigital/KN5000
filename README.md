# KN5000

Reverse engineering and homebrew development for the **Technics KN5000** arranger keyboard.

## What's Here

This repository is the central hub for a multi-pronged effort spanning ROM disassembly, emulation, compiler development, homebrew games, and documentation.

| Directory | Description |
|-----------|-------------|
| `roms-disasm/` | ROM disassembly & byte-matching reconstruction |
| `mame/` | MAME emulator — KN5000 driver development |
| `llvm/` | Custom LLVM backend for the TLCS-900 CPU |
| `mines/` | Minesweeper homebrew game (KN5000 port) |
| `custom-roms/` | Custom ROM experiments (Another World port) |
| `sound/` | Sound subsystem reverse engineering |
| `docs/` | [Documentation website](https://arqueologiadigital.github.io/kn5000-docs/) (Jekyll) |
| `original-roms/` | Original firmware ROM dumps (read-only reference) |

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
