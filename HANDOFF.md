# Handoff Report — Feb 24, 2026

## What Just Happened

The **Mines homebrew game for KN5000** is now fully functional in MAME emulation. Three major issues were resolved in this session:

1. **Event loop death** (kn5000-qea) — Root cause: TLCS-900/H 16/32-bit INC/DEC instructions do NOT set flags. Assembly loops using `dec 1, xbc` + `jrl nz` created infinite loops. Fix: use `sub xbc, 1` instead.

2. **Display ownership** (kn5000-gaha) — Firmware rendering overwrites VRAM every frame. Fix: per-frame `load_palette()` + `clear_vram()` + `draw_minefield()` in `idle_update()` before yielding to firmware. Game draws AFTER firmware in the main loop, so our content wins.

3. **LLVM INC/DEC flag definitions** (kn5000-udw7) — Moved INC16/DEC16/INC32/DEC32 outside `let Defs = [SR]` blocks in `TLCS900InstrInfo.td` so the compiler won't generate dangerous DEC+branch patterns.

## Current State of the Game

**Everything works:** display (minefield visible on LCD), input (control panel buttons), game logic (flood fill, mines, flags, game over), cooperative multitasking (yield/resume between frames). Verified with MAME screenshots and Lua-injected button presses.

**Performance:** ~22 FPS at 99% MAME speed. Acceptable for minesweeper.

**Auto-activate** is enabled in `Boot_Init` (startup.s line 344-352) for headless testing — game starts immediately without navigating DISK MENU.

## Open Issues to Work On

Run `cd /mnt/shared/kn5000_project && /mnt/shared/tools/bd ready` for full list. Key ones:

### Low-hanging fruit
- **kn5000-dnsp** (P3): Game exit cleanup — QUIT button handling (return display to firmware), remove auto-activate for interactive builds, remove debug markers from startup.s and main.c. The debug markers are `DBG(0xD0)`-`DBG(0xDF)` in main.c and AudioMix writes in startup.s.

### Larger tasks available
- **kn5000-p2c** (P1): Document serial command bytes (control panel protocol)
- **kn5000-32b** (P1): Trace CPanel_SM_* state machine handlers
- **kn5000-kuu** (P1): Disassemble HDAE5000 ROM at 0x280000

## Critical Project Rules

1. **Read CLAUDE.md before working in any subproject.** The central CLAUDE.md at `/mnt/shared/kn5000_project/CLAUDE.md` indexes everything.
2. **Issue tracker discipline:** Create issues before working, claim/release, update when done, sync to website with `cd /mnt/shared/kn5000-roms-disasm && make issues`.
3. **Commit frequently.** Git status should always be clean.
4. **Assembly verification:** After any assembly edit in roms-disasm: `make all` must pass, `python scripts/compare_roms.py` must show 100%.
5. **No Co-Authored-By on `kn5000_pr*` branches** in the MAME repo.

## Key Build Commands

```bash
# Mines game
cd /mnt/shared/Mines/platforms/kn5000 && make

# Test in MAME (headless)
cd /mnt/shared/mame && SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy \
  ./mame kn5000 -rompath /mnt/shared/custom_kn5000_roms/mines \
  -extension hdae5000 -log -seconds_to_run 30 \
  -video soft -nowindow -sound none

# MAME screenshot via Lua
# Add: -autoboot_script /tmp/script.lua -snapname kn5000/name
# In Lua: manager.machine.video:snapshot()

# ROM disassembly
cd /mnt/shared/kn5000-roms-disasm && make all

# LLVM
cd /mnt/shared/llvm-project && ninja -Cbuild llc llvm-mc
# Tests: build/bin/llvm-lit llvm/test/CodeGen/TLCS900/

# Issue tracker
BD=/mnt/shared/tools/bd
$BD list          # all issues
$BD ready         # available work
$BD show <id>     # issue details
$BD create "title" -d "description"
$BD comments add <id> "text"
$BD close <id>
```

## Key File Locations

| What | Where |
|------|-------|
| Game startup assembly | `/mnt/shared/Mines/platforms/kn5000/startup.s` |
| Game video driver | `/mnt/shared/Mines/platforms/kn5000/video.c` |
| Game input driver | `/mnt/shared/Mines/platforms/kn5000/input.c` |
| Game main loop | `/mnt/shared/Mines/common/main.c` |
| Hardware constants | `/mnt/shared/Mines/platforms/kn5000/kn5000.h` |
| LLVM InstrInfo | `/mnt/shared/llvm-project/llvm/lib/Target/TLCS900/TLCS900InstrInfo.td` |
| Firmware disassembly | `/mnt/shared/kn5000-roms-disasm/maincpu/kn5000_v10_program.s` |
| MAME KN5000 driver | `/mnt/shared/mame/src/mame/matsushita/kn5000.cpp` |
| Issue tracker data | `/mnt/shared/kn5000_project/.beads/issues.jsonl` |

## Known Gotchas

- **LLVM bug #8** (8-bit register encoding): Use 32-bit operations for everything. Hand-written assembly AND compiler-generated code affected. Workarounds throughout video.c and input.c.
- **LLVM bug #10** (register x/y swap on inlining): Use `__attribute__((noinline))` on tile functions.
- **LLVM bug #11** (uint16_t for-loop exits after 1 iteration): Use do-while + uint32_t.
- **TLCS-900/H INC/DEC**: 16/32-bit versions don't set flags. Use SUB for counted loops. Now fixed in LLVM but assembly code still uses SUB (correct).
- **MAME headless**: Use `SDL_VIDEODRIVER=offscreen SDL_AUDIODRIVER=dummy` (not Qt env vars).
- **Firmware VRAM writes**: Come from an unidentified path, NOT gated by 0xD53 bit 3. The per-frame redraw in idle_update is the working solution.
