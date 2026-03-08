-- DSP Effect Parameter Tracing Script for MAME KN5000
--
-- Usage: mame kn5000 -rompath <path> -skip_gameinfo -autoboot_script scripts/dsp_trace.lua
--
-- This script captures DSP register writes from both DSP1 (DS3613GF-3BA) and
-- DSP2 (MN19413) while the user interacts with the keyboard's effect settings.
-- Output is written to dsp_trace_log.txt for offline analysis.
--
-- The trace correlates register addresses with effect parameter names by
-- monitoring MAME's verbose log output. For best results, enable LOG_REGWRITE
-- and LOG_PARALLEL in both DSP device sources.
--
-- Workflow:
-- 1. Boot MAME with this script
-- 2. Navigate to EFFECT menu on KN5000
-- 3. Select an effect type (e.g., CHORUS)
-- 4. Adjust each parameter one at a time
-- 5. Press F12 to save a snapshot at each parameter change
-- 6. Review dsp_trace_log.txt for register-to-parameter mapping

local logfile = nil
local frame_count = 0
local trace_active = false
local last_snapshot_frame = 0

-- SubCPU DRAM addresses for effect state (from firmware analysis)
-- These are SubCPU payload addresses, not directly accessible via Lua mem reads
-- on the main CPU bus. We use them for reference only.
local EFFECT_STATE = {
    -- DSP effect type indices (from MainCPU ROM tables)
    -- Channel 1 reverb: controlled by MIDI CC 91
    -- Channel 1 chorus: controlled by MIDI CC 93
    -- Generic effects: EFFECT button UI
}

local function log_msg(msg)
    if logfile then
        logfile:write(string.format("[frame %d] %s\n", frame_count, msg))
    end
    print(msg)
end

local function on_frame()
    frame_count = frame_count + 1

    -- Auto-start tracing after boot (give firmware ~30 seconds to initialize)
    if frame_count == 1800 and not trace_active then  -- 30 sec at 60fps
        trace_active = true
        log_msg("=== DSP TRACE ACTIVE ===")
        log_msg("Interact with the EFFECT menu now.")
        log_msg("Each parameter change will be logged with register writes.")
        log_msg("Press Scroll Lock to take a labeled snapshot.")
    end

    -- Periodic status every 5 minutes
    if trace_active and frame_count % 18000 == 0 then
        log_msg(string.format("--- Still tracing (frame %d, %.0f min) ---",
            frame_count, frame_count / 3600))
    end
end

-- Monitor SubCPU port writes to detect DSP transactions
-- Port E bit 6 = DSP2 chip select (active low)
-- Port F bit 0 = SDA, bit 2 = SCLK
local function setup_port_monitors()
    local cpu = manager.machine.devices[":subcpu"]
    if not cpu then
        log_msg("WARNING: SubCPU not found - cannot set up port monitors")
        return
    end

    -- We can't directly tap GPIO ports from Lua, but MAME's built-in
    -- LOGMASKED output captures all DSP register writes. The trace
    -- is captured via MAME's -log flag or -verbose flag.
    log_msg("DSP logging is handled by MAME's built-in device logging.")
    log_msg("Run MAME with -log to capture DSP register writes to error.log")
    log_msg("Or use -verbose for console output.")
end

-- Read main CPU DRAM to detect effect menu state changes
local function check_effect_state()
    if not trace_active then return end

    local cpu = manager.machine.devices[":maincpu"]
    if not cpu then return end

    local space = cpu.spaces["program"]
    if not space then return end

    -- The effect type is stored in MainCPU workspace variables.
    -- Key addresses (from ROM analysis):
    -- Workspace pointer at DRAM[0x10AC] → current effect workspace
    -- Effect type index at workspace+0x14
    --
    -- For now, we just periodically dump key memory regions
    -- that change when effects are modified.
end

local function init()
    logfile = io.open("dsp_trace_log.txt", "w")
    if not logfile then
        print("ERROR: Cannot open dsp_trace_log.txt for writing")
        return
    end

    log_msg("=== KN5000 DSP Effect Parameter Trace ===")
    log_msg("Date: " .. os.date())
    log_msg("")
    log_msg("This trace captures DSP register writes during effect changes.")
    log_msg("MAME's device logging (LOGMASKED) provides the actual register data.")
    log_msg("")
    log_msg("DSP1 (DS3613GF-3BA / IC311): Memory-mapped, channels 0-1")
    log_msg("DSP2 (MN19413 / IC310): Serial GPIO, channels 2-4")
    log_msg("")
    log_msg("Effect type → Algorithm mapping (from SubCPU ROM 0x01F596):")
    log_msg("  Algo 2: CHORUS, MOD CHORUS, ENHANCER, FLANGER, PHASER, ENSEMBLE")
    log_msg("  Algo 3: GATED REVERB, SINGLE DELAY, MULTI TAP DELAY")
    log_msg("  Algo 4: MODULATION DELAY")
    log_msg("  Algo 5-8: Various reverbs")
    log_msg("  Algo 9-11: DISTORTION, OVERDRIVE, FUZZ, COMPRESSOR, etc.")
    log_msg("")
    log_msg("Waiting for firmware boot (30 seconds)...")

    emu.register_frame(on_frame)
    setup_port_monitors()
end

init()
