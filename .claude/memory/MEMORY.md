# KN5000 Project — Central Memory Index

This is the central memory for the KN5000 project hub at `/mnt/shared/kn5000_project/`.
It indexes all subproject memories without duplicating their content.

## Subproject Memory Locations

Memory files are version-controlled in each repo under `.claude/memory/` and also
auto-loaded from `~/.claude/projects/`. The onboarding script (`scripts/onboard.sh`)
copies repo memory into the local Claude Code directory.

| Subproject | Repo Memory | Key Files |
|------------|------------|-----------|
| Central hub | `kn5000_project/.claude/memory/` | MEMORY.md, sound-subsystem-memory.md |
| Mines (homebrew) | `Mines/.claude/memory/` | MEMORY.md, llvm-encoding-bugs.md, workarounds.md |
| LLVM (compiler) | `llvm-project/.claude/memory/` | MEMORY.md, api-changes.md, encoding-reference.md |
| Custom ROMs | `custom-kn5000-roms/.claude/memory/` | MEMORY.md |
| Custom ROMs (AW) | `custom-kn5000-roms/anotherworld/.claude/memory/` | MEMORY.md, floppy-disc-research.md, codewheel-investigation.md |
| MAME | (none) | |

Roms-disasm and kn5000-docs do not have Claude Code memory directories.

## Knowledge Map — What's Where

### Hardware & Architecture
- Memory map, CPU details, boot sequence → `docs/` website pages
- TLCS-900 opcode encoding → LLVM memory (`encoding-reference.md`)
- Sound/tone gen addresses → Sound subsystem memory
- VGA/VRAM/display system → Mines memory

### LLVM Compiler Bugs & Workarounds
- Full bug list (11 bugs, all fixed/resolved) → Mines memory (`llvm-encoding-bugs.md`)
- C-level workarounds: ALL REMOVED (Feb 28) → Mines memory (`workarounds.md`)
- LLVM API changes (old→modern) → LLVM memory (`api-changes.md`)
- MCCodeEmitter fixup patterns → LLVM memory

### MAME Emulation
- Driver fixes (DMA, LDC, scheduling) → Sound subsystem memory
- SubCPU payload transfer status → Sound subsystem memory
- MAME testing commands (headless, Lua) → Mines memory
- Driver edit location policy → Sound subsystem memory
- **MAME dialog bypass flags (STRICT):** Use `-skip_gameinfo -seconds_to_run N` (N<300) to skip ALL startup dialogs. `-skip_gameinfo` skips system info screen, `-seconds_to_run <300` skips both info AND warnings dialogs. Add `-nothrottle` for fast automated runs.
- **Automated game testing:** Use Lua autoboot script to force-activate game (write 1 to 0x200000 GAME_ACTIVE), take screenshot (`manager.machine.video:snapshot()`), then exit. Full command: `mame kn5000 -rompath ... -extension hdae5000 -window -skip_gameinfo -seconds_to_run 120 -nothrottle -autoboot_script test.lua`
- **SNS NMI (power-off) emulation:** Two mechanisms in kn5000.cpp:
  (A) Boot-time write tap on DRAM[0xFFD4]: intercepts Boot_DisplayScreen's zero-write, computes correct payload checksums in C++ so SubCPU_Payload_Verify passes. (B) Exit-time 60Hz timer: pulses NMI when exit_pending=true, ROM handler NMI_StorePayloadChecksums (EF08D4) runs if guard is set. Both ensure DRAM[0xFFD4/0xFFD2] hold correct checksums at nvram_save().
- **SNS NMI key facts:** DRAM[0x0400] (NMI guard, written by Boot_DisplayScreen to 0x80) is in TLCS-900 INTERNAL CPU RAM, NOT on external bus → write taps cannot detect it. Lua read_u8(0x0400) reads external DRAM (different memory). ROM handler checks guard internally. Address 0x1000+ is external DRAM. Internal RAM is 0x000000-0x000FFF (on-chip, bypasses external bus).

### Homebrew Development
- HDAE5000 extension board interface → Mines memory + `docs/hdae5000-homebrew.md`
- DISK MENU activation events → Mines memory
- Display ownership / VRAM access → Mines memory
- Workspace pointer system → Mines CLAUDE.md
- ASL assembler patterns → Custom ROMs memory

### Issue Tracker (Beads)
- **Location:** `/mnt/shared/kn5000_project/.beads/issues.jsonl`
- **CLI:** `/mnt/shared/tools/bd` — must run from kn5000_project directory
- **Website sync:** `cd /mnt/shared/kn5000-roms-disasm && make issues` → exports to `/mnt/shared/kn5000-docs/issues.md`
- **Stats (Mar 3):** 257 issues (56 open, 199 closed)
- **Policy:** After meaningful work, update issues, sync website, pick next task (STRICT)

### Disassembly Documentation Policy (STRICT)
When converting .byte blocks to native instructions, ALWAYS:
1. Add documentation header comments to each routine explaining what the code does
2. Attempt to give meaningful/semantic labels to routines (rename LABEL_XXXXXX where purpose is clear)
3. Analyze control flow, register usage, and called functions to determine purpose

### LLVM Assembly Build (roms-disasm) — AUTHORITATIVE
- **Status:** LLVM .s files are the authoritative source (Feb 23, 2026). All 6 ROMs: 100% byte match.
- **Source layout:** `.s` files in ROM directories (maincpu/, subcpu/, etc.), ASL archived in `archive/asl/`
- **Build:** `make all` — no ASL dependency for standard builds
- **Converter:** `roms-disasm/scripts/asl_to_llvm.py` (~4550 lines) — converts ASL→LLVM, kept for future projects
- **Pipeline:** `llvm-mc -triple=tlcs900` → `ld.lld` → `llvm-objcopy` → raw binary
- **All ROMs:**
  | ROM | Native Instructions | .byte Fallbacks | Symbolic .long | Size |
  |-----|-------------------|----------------|----------------|------|
  | Maincpu | 239,683 | 0 | 15,683 | 2MB |
  | Subcpu payload | 35,721 | 0 | 14 | 192KB |
  | Subcpu boot | 1,357 | 0 | 0 | 128KB |
  | HDAE5000 | 502 | 0 | 12 | 512KB |
  | Table data | 1,678 | 0 | 9 | 2MB |
  | Custom data | 0 (data-only) | 0 | 0 | 1MB |
  | **Total** | **279,441** | **0** | **15,718** | **~8MB** |
- **Migration complete (all 6 phases):**
  - Phase 1: All 110 tmp94c241.inc macros → native LLVM instructions
  - Phase 2: db-encoded instruction conversion (+29 native)
  - Phase 3: Modular .include structure (30 includes for maincpu, 7 for table_data)
  - Phase 4: Block buffer scaffolding removed (-334 lines, fixed subcpu drift)
  - Phase 5: LLVM promoted to authoritative, ASL archived, directory restructured
  - Phase 6: Documentation updated
- **Extended addressing modes (Feb 23):** All 2,681 opaque `x_` wrapper instructions eliminated.
  - 198 old ExtAddrModeSuffix/OpImm defs removed, 126 new consolidated defs added
  - New encoder formats: ExtImmMod, RIImmMod (modifier added to sub-opcode at emit time)
  - ~15 remaining ExtAddrModeSuffix defs have proper semantic names (future cleanup)
- **.byte→native conversion (Feb 27):** ~11,000 .byte instructions converted to native mnemonics across all ROMs.
  - PrevBank (D7 prefix): 147 conversions (LLVM backend additions)
  - Register prefix (C8-EF): 2,680 reg-reg, 831 ALU+imm/LD+imm/BIT, 246 shifts/rotates/MUL/DIV
  - Memory addressing modes: 3,616 compact R/R+d8, 1,038 compact dst (CALL/JP/CPW/LD), 523 short LD
  - Branch instructions: 1,214 JR/JRL/CALR
  - Additional 684 (compact imm32 loads)
  - **Remaining multi-byte .byte in HDAE5000: ~4,663** — all remaining require LLVM backend additions:
    (R+d16) ~970, 16-bit direct ~470, 8-bit direct ~210, F2 imm stores ~400, complex addressing ~300
  - **d8 displacement is SIGNED:** Confirmed via MAME (int8_t cast). Range -128 to +127. LLVM is correct.
  - **LLVM short-form mnemonics:** `ldb` (8-bit LD 0x20+r), `ldw` (16-bit LD 0x30+r), `cpw` (16-bit CP mem)
- **String pointer table conversion (Mar 1):** 573 raw .byte pointer entries → `.long LABEL_` across 57 tables.
  - Script: `scripts/convert_string_pointer_tables.py` — ROM-binary-driven auto-detection + conversion
  - Multi-strategy label resolution: byte_count (572), string_match (390), byte_prefix_match (9), byte_block (26)
  - Position verification prevents false matches (verify_resolution_by_byte_count)
  - 19 tables (557 entries) safely skipped — labels in mixed code/data regions
  - **299-byte mismatch FIXED (Mar 2):** Was caused by 5 duplicate 0xFF pads after aligned_string + 1 lda_24 relocation bug. Now 100% byte-match on all 6 ROMs.
- **LLVM disassembler for .byte decoding (PREFERRED):** Use `llvm-mc --triple=tlcs900 --disassemble` instead of unidasm.
  - Pipe hex bytes: `echo "0xd8 0xaa 0x12" | /mnt/shared/llvm-project/build/bin/llvm-mc --triple=tlcs900 --disassemble`
  - Extract ROM bytes with `xxd -s <offset> -l <length> -i <rom>` then pipe to llvm-mc
  - Output is in exact LLVM syntax — no manual mnemonic translation needed (lds32, cps, incdi16_24, etc.)
  - Also: `llvm-objdump -d --triple=tlcs900 <elf>` for labeled disassembly of built ELF files
  - Round-trip verify: `llvm-mc --triple=tlcs900 --show-encoding` to check assembled bytes match original
  - Note: addresses/immediates in output are decimal (convert to hex for labels)
  - Known issue: `ldw (xsp + 0)` gets optimized to `ldw (xsp)` (4 bytes vs 5) — use `.byte` fallback
- **LLVM encoding pitfalls for .byte→native conversion:**
  - **Compact zero-load** (`d8 a8`=ld wa,0, `ea a8`=ld xde,0, etc.): NOT in LLVM. Use `.byte`.
  - **Compact load-1** (`e8 a9`=ld xwa,1): NOT in LLVM. Use `.byte 0xe8, 0xa9`.
  - **Compact ld wa,N** vs extended: `ldw wa, 10` → 3-byte compact `30 0a 00`. Plain `ld wa, 10` → 4-byte extended.
  - **push bc/de/wa** (2-byte extended) vs **pushw bc/de/wa** (1-byte compact `29/2A/28`). Always use `pushw`.
  - **ld (mem), imm** size: `ld (xsp+N), 0` = 8-bit store (4 bytes). `ldw (xsp+N), 0` = 16-bit store (5 bytes). Same for `cp` vs `cpw`.
  - **calr with numeric address BROKEN**: emits absolute bytes. Use label or `.byte 0x1e, lo, hi`.
  - **ld A, (R+d16) load BROKEN**: "displacement too large" error. Use `.byte` (C3 prefix).
  - **ld (R+d16), A store WORKS**: F3 prefix encoding. Asymmetric with load.
  - **ldcfm/stcfm** work with register-indirect `(xix)` and R+d16. Use `ldcfm` not `ldcf`.
  - **andmi8 (xhl), imm** works for AND mem with immediate.
  - **ld a, imm8** compact: `ld a, 0` → 3-byte extended (`c9 03 00`). Use `ldb a, 0` for 2-byte compact (`21 00`).
  - **push xreg** (32-bit): `push xde/xhl/xix/xiz` = 1-byte compact. Do NOT use `pushw` (that's for 16-bit regs only).
  - **dec/inc N, xsp** compact: `.byte 0xef, 0x6a` (dec 2) / `0xef, 0x62` (inc 2). Not in LLVM.
  - **cps qiz, 0** (prevbank compact compare): NOT in LLVM. Use `.byte 0xd7, 0xfa, 0xd8`.
  - **ld qiz, wa** / **ld wa, qiz** / **ld bc, qiz**: D7 prevbank ld WORKS in LLVM.
  - **Edit tool CORRUPTS Latin-1**: NEVER use Edit on kn5000_v10_program.s. Always use Python scripts with binary I/O.
- **Data formatting:** .zero/.fill directives (6,288 total), .ascii/.asciz for strings
- **Converter fix:** binclude path resolution for archive/asl/ layout, macro library search

### Git Force Push Policy (STRICT)
Before any `git push --force`, MUST:
1. Save the remote tip as a local tag: `git tag backup/<branch>_pre_force_push_YYYYMMDD <remote-tip-hash>`
2. Push that tag to the remote: `git push origin <tag-name>`
This prevents losing any work that was on the remote. Tags are immutable and survive force pushes.

### Cross-Project Policies
- All policies indexed in `/mnt/shared/kn5000_project/CLAUDE.md`
- Canonical definitions live in each subproject's CLAUDE.md
- **MAME driver integrity (STRICT):** Do not ever introduce hacks to MAME. The driver must represent the real hardware. No fake I/O ports, no shortcuts, no emulation-only features.
- **Scientific documentation (STRICT):** Whenever learning something new about how the system works (hardware, software, data formats, protocols), proactively document findings on the website (`docs/`). Behave like a scientist: explore, verify, document clearly.
- **Baseline verification (STRICT):** At session start, ALWAYS verify the build is clean (`make clean && make all` + `compare_roms.py`) BEFORE starting any work. If the baseline is broken, fix it as a separate committed step first. Never assume "it was already broken" — always ensure a known-good state before introducing changes so any issues can be attributed to the current work.
