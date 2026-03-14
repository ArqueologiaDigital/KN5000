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
| `mame/` | `/mnt/shared/mame` | MAME emulator (KN5000 driver development) | Yes | `cd mame && make -j$(nproc) SOURCES=src/mame/matsushita/kn5000.cpp` |
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

Edit MAME driver files in `/mnt/shared/mame/src/mame/matsushita/`. Do not create copies elsewhere. Agents may build MAME using `make -j$(nproc) SOURCES=src/mame/matsushita/kn5000.cpp` for incremental builds.

### MAME Code Style (for upstream PR branches)
**Source:** Central hub (this file) — applies to `kn5000_pr*` branches.

- Use `BIT(value, bit)` instead of `(value & (1 << bit))` for single-bit tests.
- Use `logmacro.h` with categorized `LOGMASKED()` channels instead of raw `logerror()`.
- Follow existing MAME coding conventions visible in surrounding code.

### LABEL_XXXXXX Elimination (STRICT POLICY — MAJOR PROJECT GOAL)
**Source:** Central hub (this file) — applies to `roms-disasm`.

All `LABEL_XXXXXX` address-based labels in the ROM disassembly MUST be replaced with meaningful semantic names. This is a major project goal. Currently ~7,987 remain.

**Opportunistic renaming (MANDATORY):** Whenever you are working on any routine or file that contains `LABEL_XXXXXX` labels — for any reason (bug fix, analysis, documentation, other renames) — you MUST take the opportunity to rename them. Do not leave `LABEL_XXXXXX` labels in code you have read and understood. Every touch point is a chance to make progress.

**Naming quality:** Every label must reflect what the code actually does. Analyze control flow, register usage, callers, callees, and memory access patterns. Generic or placeholder names are not acceptable. See Policy 7 (Duplicate Symbol Detection) for disambiguation rules.

**Verification:** Every rename batch must pass `make clean && make all` with 100% byte match on all 6 ROMs before committing.

### Accurate Hardware Emulation
**Source:** `roms-disasm/CLAUDE.md`

All emulator code must describe actual hardware behavior. No HLE shortcuts when ROM dumps are available. HLE is acceptable ONLY for undumped MCU ROMs (control panel MCU, LED controller).

### LLVM: Build Allowed
**Source:** `llvm/CLAUDE.md`

Agents may build LLVM using `ninja -Cbuild` in the LLVM directory. Reconfigure with `bash build_tlcs900.sh` only if needed. Run specific targets (e.g., `ninja -Cbuild llc`) for faster incremental builds. Run tests with `build/bin/llvm-lit llvm/test/CodeGen/TLCS900/`.

### LLVM Toolchain Provenance Tracking (STRICT POLICY)
**Source:** Central hub (this file) — applies to `roms-disasm` and `llvm-project`.

**Rule 1: Record LLVM version in every roms-disasm commit.**
Every commit to `roms-disasm/` must include in its commit message a line:
`LLVM: <branch>@<short-hash> (<full-hash>)`
This records the exact LLVM source that the installed toolchain (`llvm-mc`, `ld.lld`, `clang`, `llvm-objcopy`) was built from. Obtain it via:
`cd /mnt/shared/llvm-project && git log -1 --format="%D @ %h (%H)"`

**Rule 2: Maintain a `TOOLCHAIN_VERSION` file in roms-disasm.**
The file records the current LLVM build's branch, commit hash, and build date. Update it whenever the LLVM toolchain is rebuilt from a different commit.

**Rule 3: Never rewrite LLVM history after use.**
Once an LLVM commit has been used to build toolchain binaries that produced verified, committed ROM artifacts, that commit is **immutable**. No `git commit --amend`, no `git rebase`, no `git push --force` that would destroy it. Further LLVM changes must be new commits on top. This ensures any ROM build can be reproduced from the exact compiler source.

**Scope:** All LLVM tools used in the roms-disasm build pipeline: `llvm-mc` (assembler), `ld.lld` (linker), `clang` (C compiler), `llvm-objcopy` (binary extraction).

### Proactive Unblocking (STRICT POLICY)
**Source:** Central hub (this file) — applies to ALL subprojects.

Be proactive and come up with new tasks to unlock blocked issues. Thoroughly work on them all. Make significant progress even if it means untying knots independently. When an issue is blocked:
1. **Identify the blocker** — read the dependency chain (`bd show <id>`, `bd blocked`).
2. **Create unblocking tasks** — if no issue exists for the blocker, create one with `bd create`.
3. **Work the blocker first** — resolve it, then return to the originally blocked issue.
4. **Chain unblocking** — if the blocker is itself blocked, recurse until you find actionable work.

Do not wait for user input to unblock issues. Do not report "this is blocked" without attempting to resolve the blocker. The goal is forward progress on every front.

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
mame kn5000 ... -skip_gameinfo -seconds_to_run 120

# For Mines game testing with Lua screenshot:
mame kn5000 -rompath /mnt/shared/custom_kn5000_roms/mines \
  -extension hdae5000 -window -skip_gameinfo \
  -seconds_to_run 120 \
  -autoboot_script /tmp/mame_screenshot.lua
```

**How it works:**
- `-skip_gameinfo` skips the system information screen
- `-seconds_to_run N` (where N < 300) skips ALL dialogs including severe emulation warnings. MAME exits after N emulated seconds.
- `-skip_warnings` (requires `skip_warnings 1` in `~/.mame/ui.ini` AND a local MAME patch in `ui.cpp`) skips warnings without requiring `-seconds_to_run`

**NEVER use `-nothrottle` (STRICT POLICY):** Running at accelerated speed can cause timing-dependent firmware issues. Always run MAME at real-time speed for accurate emulation behavior.

**Local MAME patch (NOT for upstream PRs):** In `src/frontend/mame/ui/ui.cpp`, `display_startup_screens()`, change `bool show_warnings = true;` to `bool show_warnings = !options().skip_warnings();`. This makes `-skip_warnings` work for all warning types including severe "THIS SYSTEM DOESN'T WORK" warnings.

**Mines game activation:** The game requires DISK MENU activation (event `0x01C00008`). For automated tests, use Lua to write 1 to `GAME_ACTIVE` at address 0x200000 after the firmware has booted (~30s of emulated time).

## Parallel Background Agent Safety (STRICT POLICIES)

These policies govern how background agents operate when multiple agents work concurrently in the same repository. They were established after the March 14, 2026 session where 8 parallel rename agents exposed critical coordination failures.

### Policy 1: No Destructive Git Commands in Background Agents

Background agents MUST NOT run any of the following git commands:
- `git reset --hard`
- `git checkout -- .` (whole-tree revert)
- `git clean -f`
- `git stash`
- `git rebase`
- `git push --force`

If a background agent encounters a dirty working tree or merge conflict, it must **stop and report the problem** rather than attempt cleanup. Only the orchestrating (main) agent or the user may run destructive git commands.

**Incident:** A background agent executed `git reset --hard`, destroying 5 commits by other agents. Recovery required manual `git reflog` intervention.

### Policy 2: Cross-File Reference Verification Before Commit

Every rename operation MUST, before committing:
1. `grep -r` across ALL maincpu/ files for both the old label name AND the new label name
2. Verify that every reference to the old name has been updated
3. Run `make all` (or at minimum the linker step) and confirm 0 undefined symbols

The rename script itself must take a mapping of `{old_name: new_name}` and apply it to ALL files in one pass, not just the target file. Cross-file reference updates are not optional — they are part of the rename operation.

**Incident:** 11 of 122 commits were fixes for broken cross-file references — agents renamed definitions in one file but missed references in other files, causing undefined symbol link errors.

### Policy 3: One Agent Per Git Repository at Commit Time

Background agents working in the same repository MUST coordinate commits through a lock file:
- Before staging/committing, create a lock file (`/tmp/kn5000_roms_disasm_git.lock`) containing the agent's task ID
- If the lock file exists and was created by a different agent, wait 10 seconds and retry (up to 6 retries)
- Hold the lock only during the stage → commit → verify cycle (seconds, not minutes)
- Remove the lock file after the commit succeeds or after any failure
- The orchestrating agent is responsible for cleaning stale locks at session start

**Incident:** Multiple agents staging and committing simultaneously created chaotic working tree states — files appearing/disappearing from `git status`, `MM` states from concurrent modifications.

### Policy 4: Atomic Rename Batches (No Partial Commits)

Each rename batch must be fully self-contained:
- Generate the complete rename mapping before starting any file edits
- Apply all renames (definition + all cross-file references) in one script execution
- Build-verify immediately after application
- Commit immediately after successful build
- If the script is interrupted (rate limit, timeout), the next invocation must detect partial state: either roll back with `git checkout -- <affected files>` or complete the partial batch

**Incident:** Agent rate limits caused partial rename work to be left uncommitted in the working tree, requiring manual intervention. Some agents produced duplicate commits for the same batch.

### Policy 5: Serialized Builds via Lock File

The roms-disasm Makefile does not track `.include` dependencies — `make all` without `make clean` silently skips reassembly of modified files. Therefore `make clean && make all` (~12 seconds) is the only valid build verification. Multiple agents running this concurrently causes corrupt intermediate files (one agent's `make clean` deletes another's in-flight `.o`/`.bin` files).

**Rule:** Agents MUST acquire a build lock before running `make clean && make all`:
- Lock file: `/tmp/kn5000_roms_disasm_build.lock` (separate from the git lock in Policy 3)
- Before building, create the lock file containing the agent's task ID
- If the lock file exists and was created by a different agent, wait 10 seconds and retry (up to 12 retries = 2 minutes max wait)
- Hold the lock for the entire `make clean && make all` cycle (~12 seconds)
- Remove the lock file after the build completes (success or failure)
- The orchestrating agent is responsible for cleaning stale locks at session start

**Note:** The filesystem is virtiofs (VM host↔guest), not NFS. The build failures initially attributed to "NFS race conditions" were actually caused by concurrent `make clean` runs deleting each other's intermediate files. The one genuine virtiofs issue (`dd` → `cat` write visibility in the subcpu build step) was fixed with an explicit `sync` in the Makefile (commit `c450bdc`).

**Incident:** 8 parallel agents running `make clean && make all` simultaneously produced corrupt `.o` files ("section header string table index does not exist"), 0-byte intermediate files, and disappearing `.bin` files.

### Policy 6: Agent Scope Boundaries (No File Overlap)

Before launching parallel agents, the orchestrating agent must assign non-overlapping file ownership:
- Each agent "owns" one primary file and may only modify that file + its direct cross-references
- If two agents need to modify the same cross-reference file, one must complete before the other starts
- The orchestrating agent maintains a manifest of `{agent_id: [owned_files]}`
- No agent may modify a file owned by another active agent

**Incident:** Multiple agents modifying the same cross-reference files concurrently caused changes to conflict or be silently overwritten.

### Policy 7: Duplicate Symbol Detection and Semantic Disambiguation

Every rename mapping must be validated before application:
1. All new names must be unique within the mapping
2. All new names must not already exist as labels anywhere in the codebase (`grep -r "^new_name:" maincpu/`)
3. If a collision is detected, do NOT use generic suffixes (`_2`, `_Alt`, `_Inner`). Instead, analyze the code at both addresses to understand what makes them semantically different, then choose names that reflect the actual distinction. Examples:
   - Two routines both doing "read param" but from different sources → `SeqData_ReadParamFromBuffer` / `SeqData_ReadParamFromDRAM`
   - Two entry points into the same logical operation → `FlashWrite_Start` / `FlashWrite_Resume`
   - A function and its inlined variant → `VoiceScan_Loop` / `VoiceScan_Unrolled`
4. Do NOT leave any label as `LABEL_XXXXXX`. If the semantic difference is not immediately obvious, invest additional effort: read the surrounding code more carefully, trace callers and callees, examine register usage, check what memory addresses are accessed, and compare the two routines side by side. There is always a meaningful difference — find it and express it in the name.

**Incident:** 4 fix commits were needed for duplicate symbol names — two different `LABEL_XXXXXX` addresses renamed to the same semantic name (`SeqData_ReadParamReturn`, `AudioCtrl_Epilogue`, `SeqScan_ProcessAllParts`).

### Policy 8: Agent Progress Checkpointing

Each background agent should write a progress file at batch boundaries:
- Path: `/tmp/rename_agent_{file}_progress.json`
- Contents: `{batch: N, labels_done: M, labels_total: T, last_commit: "hash", status: "in_progress|complete|failed"}`
- The orchestrating agent reads these files instead of polling git
- On completion or failure, the agent writes final status before exiting

**Incident:** When agents hit rate limits or timeouts, the orchestrating agent had no way to know how far they got without manually inspecting the working tree. Required repeated `git status` and `git log` polling.

## How to Work From Here

1. **Check the issue tracker.** Run `cd /mnt/shared/kn5000_project && /mnt/shared/tools/bd ready` to see available work, or `bd list` for all issues.
2. **Identify the subproject.** What does the task involve? ROM disassembly? MAME driver? Homebrew game? LLVM compiler? Documentation?
3. **Read the CLAUDE.md.** Navigate to the subproject (use symlinks) and read its CLAUDE.md before making any changes.
4. **Check memories.** If the task involves accumulated knowledge (bug workarounds, hardware findings, API patterns), check the relevant subproject memory.
5. **Build in the subproject.** Navigate to the subproject directory for builds. Don't try to build from this central directory.
6. **Cross-project changes.** If a discovery affects multiple subprojects (e.g., new event code), follow the Documentation Freshness policy — update all relevant locations.
7. **Commit per subproject.** Each git repo gets its own commit(s). Don't mix changes across repos in one conceptual "save."
8. **Update the issue tracker.** After meaningful work, update issues with progress, close completed ones, open new ones for next steps, sync to website, and pick the next task.
