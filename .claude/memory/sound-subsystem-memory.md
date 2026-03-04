# Claude Code Memory - KN5000 fix_loading_of_subcpu_payload

## Strict Policies

### Policy Storage (USER-MANDATED)
**All policies MUST be saved in CLAUDE.md.** MEMORY.md alone is not sufficient. CLAUDE.md is the canonical source of truth. When editing CLAUDE.md, use progressive disclosure: concise summaries at top level, details in sub-sections or linked docs. No repetition.

### No AI Attribution in MAME PR Commits (USER-MANDATED)
**Do NOT include "Co-Authored-By: Claude" in commits on `kn5000_pr*` branches** (those destined for upstream MAME PRs). All other commits (roms-disasm repo, kn5000-docs repo, etc.) **should** still include the Co-Authored-By line as usual.

### Assembly Edit Verification (USER-MANDATED)
**Every time assembly source files are edited, MUST verify:**
1. ROMs still build: `make rebuilt_ROMs/<component>.rebuilt.rom`
2. Byte-matching score does not degrade: `python scripts/compare_roms.py`
Never commit assembly changes without both checks passing.

### MAME Driver Edit Location (USER-MANDATED)
Edit MAME driver files in `/mnt/shared/mame/src/mame/matsushita/`. No sync to `/mnt/shared/fix_payload/mame_driver/` needed. User builds MAME manually outside the VM. Do NOT create/edit copies at the repo root.

### Frequent Commits & Clean Working Directory (USER-MANDATED, HIGH PRIORITY)
**Commit immediately after completing each logical change.** Do NOT continue to the next task or respond to the user with uncommitted work. Always leave the working directory clean (`git status` should show nothing). This applies to ALL repos: MAME, roms-disasm, kn5000-docs. Failure to commit promptly has been flagged by the user as a recurring problem.

## Project State

### MAME Driver Fixes Applied (this branch)
1. LDC CR register mapping for TMP94C241 (900tbl.hxx, dasm900.cpp)
2. DMAM register encoding (switch-based, matching TMP95C061)
3. DMAR register implementation at SFR 0x109
4. HDMA priority over IRQs in check_irqs()
5. CPU scheduling via perfect_quantum in subcpu_latch_w()
6. **DMAR burst DMA** - software-triggered DMA does full block transfer without interrupt checks

### SubCPU Payload Status
- Payload transfer: WORKING (524K HDMA transfers, all 9 E1 blocks)
- Payload execution: CONFIRMED (PC=0x01F929 after load)
- Init sequence: Completes without hanging (all loops bounded)
- Inter-CPU responses: WORKING (MSTAT init via SFR table confirmed, bidirectional DMA verified)
- Sound Name Error: RESOLVED (was caused by earlier DMAR issues, now fixed)
- Emulation reaches 31s+ at ~99% speed with healthy inter-CPU traffic

### Key Addresses
- Tone gen registers: 0x100000/0x100002 (IC303, TC183C230002)
- Tone gen keyboard: 0x110000/0x110002
- Inter-CPU latch: 0x120000
- DSP registers: 0x130000/0x130002
- Serial port 1: ~500kHz UART to DAC/DSP control
