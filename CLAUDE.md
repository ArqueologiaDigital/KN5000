# KN5000 Project — Central Hub

This directory is the unified entry point for the Technics KN5000 reverse engineering and homebrew project. It aggregates 7 subprojects spanning ROM disassembly, MAME emulation, LLVM compiler development, homebrew games, and documentation.

## Meta-Rules (MANDATORY)

These rules govern how Claude Code operates from this central directory:

1. **Read subproject CLAUDE.md files before working.** When given a task, identify which subproject(s) it involves and read their CLAUDE.md files first. Subproject policies are binding, not advisory.
2. **Respect ALL subproject policies.** Policies defined in any subproject CLAUDE.md apply when working in that subproject's scope. Key policies are indexed in the Cross-Project Policies section below.
3. **Update the correct CLAUDE.md.** When policies change, update the subproject's own CLAUDE.md (the authoritative source). Update this file only for cross-project or meta-level changes.
4. **Navigate to subproject directories for builds.** Each subproject has its own build system. Use the symlinks in this directory for quick access.
5. **Consult subproject memories.** Each subproject may have its own Claude Code memory directory with accumulated knowledge. The central MEMORY.md indexes them all.

## Subproject Registry

| Symlink | Path | Purpose | CLAUDE.md | Build |
|---------|------|---------|-----------|-------|
| `mines/` | `/mnt/shared/Mines` | Minesweeper homebrew game (KN5000 port) | Yes | `cd mines/platforms/kn5000 && make` |
| `roms-disasm/` | `/mnt/shared/kn5000-roms-disasm` | ROM disassembly & byte-matching reconstruction | Yes (823 lines) | `cd roms-disasm && make all` |
| `llvm/` | `/mnt/shared/llvm-project` | Custom LLVM with TLCS-900 backend | Yes | `cd llvm && ninja -Cbuild` (user builds) |
| `mame/` | `/mnt/shared/mame` | MAME emulator (KN5000 driver development) | Yes (1 line) | User builds externally |
| `custom-roms/` | `/mnt/shared/custom-kn5000-roms` | Custom ROM experiments (Another World port) | Yes | `cd custom-roms/anotherworld && make` |
| `docs/` | `/mnt/shared/kn5000-docs` | Documentation website (Jekyll) | Yes | `cd docs && bundle exec jekyll serve` |
| `original-roms/` | `/mnt/shared/kn5000_original_roms` | Original firmware ROM dumps | No | N/A (read-only reference) |

### Additional Paths (no symlink)

| Path | Purpose |
|------|---------|
| `/mnt/shared/custom_kn5000_roms` | Modified ROM data for MAME testing |
| `/mnt/shared/tools/` | Shared tools (`asl/`, `bd`, `unidasm`) |

## Cross-Project Policies

These policies originate from specific subprojects but apply globally. The canonical definition lives in the listed CLAUDE.md.

### Frequent Commits & Clean Working Directory
**Source:** `roms-disasm/CLAUDE.md`

Commit immediately after each logical change. Never leave uncommitted work. `git status` should always show a clean tree. Applies to ALL repos.

### No AI Attribution on MAME PR Branches
**Source:** `mame/CLAUDE.md`

Do NOT include "Co-Authored-By: Claude" in commits on `kn5000_pr*` branches (destined for upstream MAME PRs). All other repos/branches SHOULD include the attribution as usual.

### Assembly Edit Verification
**Source:** `roms-disasm/CLAUDE.md`

Every assembly edit must be verified: (1) ROMs still build, (2) byte-matching score does not degrade (`python scripts/compare_roms.py`). Never commit assembly changes without both checks passing.

### Documentation Freshness
**Source:** `mines/CLAUDE.md`, `roms-disasm/CLAUDE.md`

When firmware understanding improves (new event codes, dispatch behavior, handler protocols), ALL of the following must be updated:
1. Event codes reference (`docs/event-codes.md`)
2. HDAE5000 homebrew page (`docs/hdae5000-homebrew.md`)
3. ROM disassembly (`roms-disasm/` — `EVT_*` EQU constants)
4. Website deployment (commit + push `docs/`)
5. Relevant CLAUDE.md files

### Policy Storage
**Source:** `roms-disasm/CLAUDE.md`

All policies MUST be saved in CLAUDE.md files (not just memory). CLAUDE.md is the canonical, version-controlled source of truth. Use progressive disclosure: concise summaries at top level, details in sub-sections.

### MAME Driver Edits
**Source:** `mame/CLAUDE.md`

Edit MAME driver files in `/mnt/shared/mame/src/mame/matsushita/`. Do not create copies elsewhere. User builds MAME manually.

### MAME Code Style (for upstream PR branches)
**Source:** Central hub (this file) — applies to `kn5000_pr*` branches.

- Use `BIT(value, bit)` instead of `(value & (1 << bit))` for single-bit tests.
- Use `logmacro.h` with categorized `LOGMASKED()` channels instead of raw `logerror()`.
- Follow existing MAME coding conventions visible in surrounding code.

### Accurate Hardware Emulation
**Source:** `roms-disasm/CLAUDE.md`

All emulator code must describe actual hardware behavior. No HLE shortcuts when ROM dumps are available. HLE is acceptable ONLY for undumped MCU ROMs (control panel MCU, LED controller).

### LLVM: Build Allowed
**Source:** `llvm/CLAUDE.md`

Agents may build LLVM using `ninja -Cbuild` in the LLVM directory. Reconfigure with `bash build_tlcs900.sh` only if needed. Run specific targets (e.g., `ninja -Cbuild llc`) for faster incremental builds. Run tests with `build/bin/llvm-lit llvm/test/CodeGen/TLCS900/`.

### Issue Tracker Discipline (STRICT POLICY)
**Source:** Central hub (this file) — applies to ALL subprojects.

Project issues are tracked using [Beads](https://github.com/beads-ai/beads) in `.beads/issues.jsonl` (in this directory). The `bd` CLI is at `/mnt/shared/tools/bd`. **NEVER edit `issues.jsonl` directly** — always use `bd` commands.

**Issue-First Workflow (MANDATORY):**
When the user reports a bug or requests a task, the agent MUST:
1. **Register it in Beads first** — create an issue with `bd create` before starting any work.
2. **Then work on it** — fix the bug, plan, or execute the task.
3. If the user gives multiple bugs/tasks at once, register each as a **separate issue**, pick the most important (or viable) one to work on first, and resume the others later by reading them from the tracker.

**Claim/Release Issues (MANDATORY — prevents duplicate work):**
When an agent starts working on an issue, it MUST immediately add a comment like `CLAIMED: Starting work on this issue.` When it stops working (finished, blocked, or moving to another task), it MUST add a comment like `RELEASED: <reason>.` Before picking up an issue, check its comments — if another agent has a `CLAIMED` without a subsequent `RELEASED`, do NOT work on that issue. This prevents multiple concurrent agents from duplicating effort on the same issue.

**At the end of any meaningful work, agents MUST:**
1. **Update the issue tracker** — add progress comments to relevant issues, close completed issues (following Issue Closure Requirements in `roms-disasm/CLAUDE.md`), and open new issues for any additional work identified.
2. **Sync the website** — run `make issues` in `roms-disasm/` and commit the updated `issues.md` to `docs/`.
3. **Pick the next task** — proactively select a reasonable next issue from the tracker (`bd ready` or `bd list`) and begin working on it.

**Quick reference:**
```bash
BD=/mnt/shared/tools/bd
cd /mnt/shared/kn5000_project  # bd must run from this directory
$BD list                       # List all issues
$BD show <id>                  # Show issue details
$BD create "title"             # Create new issue
$BD comments add <id> "text"   # Add progress comment
$BD close <id>                 # Close an issue
$BD ready                      # Find unblocked, unassigned work
$BD sync                       # Sync with git
make issues                    # Export to website
```

This policy ensures the issue tracker is the single source of truth for project progress and that the public website always reflects current status.

## Shared Architecture Reference

### Target Hardware
- **CPU:** TMP94C241F (Toshiba TLCS-900/H2 series)
- **Clock:** 16 MHz (main CPU), Sub CPU also TMP94C241F
- **Architecture:** 32-bit CISC, 24-bit address bus, 16-bit external data bus
- **Instructions:** Variable-length 1-7 bytes, prefix-based encoding

### Key Memory Map
| Range | Size | Contents |
|-------|------|----------|
| `0x000000-0x000FFF` | 4KB | Internal RAM |
| `0x100000-0x15FFFF` | 384KB | Sound/Tone gen hardware |
| `0x1A0000-0x1DFFFF` | 256KB | VRAM (320x240 8bpp LCD) |
| `0x200000-0x27FFFF` | 256KB | Extension DRAM |
| `0x280000-0x2FFFFF` | 512KB | Extension ROM (HDAE5000) |
| `0x800000-0x9FFFFF` | 2MB | Table Data ROM |
| `0xE00000-0xFFFFFF` | 2MB | Main CPU Program ROM |

### Key Documentation
- Hardware architecture: `docs/hardware-architecture.md`
- Complete memory map: `docs/memory-map.md`
- CPU subsystem: `docs/cpu-subsystem.md`
- Boot sequence: `docs/boot-sequence.md`
- Control panel protocol: `docs/control-panel-protocol.md`
- Inter-CPU protocol: `docs/inter-cpu-protocol.md`
- Event codes: `docs/event-codes.md`
- HDAE5000 homebrew: `docs/hdae5000-homebrew.md`
- Display subsystem: `docs/display-subsystem.md`
- ROM reconstruction progress: `docs/rom-reconstruction.md`

### LLVM TLCS-900 Backend Bugs
No active bugs. All previously reported bugs have been fixed or resolved. All C-level workarounds have been removed from the Mines codebase (commit `8b1d85e`).

See `mines/` memory files for full bug documentation.

### MAME Automated Testing (STRICT POLICY)
When running MAME automatically (without user interaction), you MUST skip startup dialogs to prevent the emulator from blocking on "press any key" screens:

```bash
# Skip ALL startup dialogs (system info + emulation warnings):
mame kn5000 ... -skip_gameinfo -seconds_to_run 120 -nothrottle

# For Mines game testing with Lua screenshot:
mame kn5000 -rompath /mnt/shared/custom_kn5000_roms/mines \
  -extension hdae5000 -window -skip_gameinfo \
  -seconds_to_run 120 -nothrottle \
  -autoboot_script /tmp/mame_screenshot.lua
```

**How it works:**
- `-skip_gameinfo` skips the system information screen
- `-seconds_to_run N` (where N < 300) skips ALL dialogs including severe emulation warnings. MAME exits after N emulated seconds.
- `-nothrottle` runs emulation at maximum speed (no frame rate cap)
- `-skip_warnings` (requires `skip_warnings 1` in `~/.mame/ui.ini` AND a local MAME patch in `ui.cpp`) skips warnings without requiring `-seconds_to_run`

**Local MAME patch (NOT for upstream PRs):** In `src/frontend/mame/ui/ui.cpp`, `display_startup_screens()`, change `bool show_warnings = true;` to `bool show_warnings = !options().skip_warnings();`. This makes `-skip_warnings` work for all warning types including severe "THIS SYSTEM DOESN'T WORK" warnings.

**Mines game activation:** The game requires DISK MENU activation (event `0x01C00008`). For automated tests, use Lua to write 1 to `GAME_ACTIVE` at address 0x200000 after the firmware has booted (~30s of emulated time).

## How to Work From Here

1. **Check the issue tracker.** Run `cd /mnt/shared/kn5000_project && /mnt/shared/tools/bd ready` to see available work, or `bd list` for all issues.
2. **Identify the subproject.** What does the task involve? ROM disassembly? MAME driver? Homebrew game? LLVM compiler? Documentation?
3. **Read the CLAUDE.md.** Navigate to the subproject (use symlinks) and read its CLAUDE.md before making any changes.
4. **Check memories.** If the task involves accumulated knowledge (bug workarounds, hardware findings, API patterns), check the relevant subproject memory.
5. **Build in the subproject.** Navigate to the subproject directory for builds. Don't try to build from this central directory.
6. **Cross-project changes.** If a discovery affects multiple subprojects (e.g., new event code), follow the Documentation Freshness policy — update all relevant locations.
7. **Commit per subproject.** Each git repo gets its own commit(s). Don't mix changes across repos in one conceptual "save."
8. **Update the issue tracker.** After meaningful work, update issues with progress, close completed ones, open new ones for next steps, sync to website, and pick the next task.
