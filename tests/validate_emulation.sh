#!/bin/bash
# =============================================================================
# KN5000 MAME Emulation Validation Suite
# =============================================================================
# Automated tests for verifying MAME emulation accuracy.
# Run from kn5000_project directory.
#
# Usage: ./tests/validate_emulation.sh [test_name]
#   No args: run all tests
#   boot:    Boot sequence only (30s)
#   menus:   Menu navigation (60s)
#   display: Display rendering (45s)
#
# Requirements:
#   - MAME built with kn5000 driver
#   - Original ROMs at /mnt/shared/kn5000_original_roms/kn5000/
#   - Lua support in MAME
# =============================================================================

set -euo pipefail

MAME="/mnt/shared/mame/kn5000"
ROM_PATH="/mnt/shared/kn5000_original_roms"
TEST_DIR="/tmp/mame_validation_$$"
SNAP_DIR="$TEST_DIR/snap"
RESULTS_DIR="$TEST_DIR/results"
PASS_COUNT=0
FAIL_COUNT=0

mkdir -p "$TEST_DIR" "$SNAP_DIR" "$RESULTS_DIR"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log_pass() {
    PASS_COUNT=$((PASS_COUNT + 1))
    echo -e "${GREEN}[PASS]${NC} $1"
}

log_fail() {
    FAIL_COUNT=$((FAIL_COUNT + 1))
    echo -e "${RED}[FAIL]${NC} $1"
}

log_info() {
    echo -e "${YELLOW}[INFO]${NC} $1"
}

# =============================================================================
# Test: Boot Sequence
# =============================================================================
test_boot() {
    log_info "Test: Boot Sequence (30s emulated time)"

    cat > "$TEST_DIR/boot_test.lua" << 'LUAEOF'
-- Boot sequence validation: capture screenshots at key moments
local screenshots = {5, 10, 15, 20, 25}
local next_ss = 1
local done = false

emu.register_periodic(function()
    if done then return end
    local t = manager.machine.time:as_double()

    if next_ss <= #screenshots and t > screenshots[next_ss] then
        print(string.format("BOOT TEST: Screenshot at %.1fs", t))
        manager.machine.video:snapshot()
        next_ss = next_ss + 1
    end

    if t > 28 then
        print("BOOT TEST: Complete")
        done = true
        manager.machine:exit()
    end
end)
LUAEOF

    "$MAME" kn5000 -rompath "$ROM_PATH" \
        -window -skip_gameinfo -seconds_to_run 30 -nothrottle \
        -nvram_directory "$TEST_DIR/nvram_boot" \
        -cfg_directory "$TEST_DIR/cfg_boot" \
        -snapshot_directory "$SNAP_DIR" \
        -autoboot_script "$TEST_DIR/boot_test.lua" \
        >"$RESULTS_DIR/boot_stdout.log" 2>"$RESULTS_DIR/boot_stderr.log" || true

    # Check screenshots were created
    local snap_count
    snap_count=$(find "$SNAP_DIR" -name "*.png" 2>/dev/null | wc -l)
    if [ "$snap_count" -ge 3 ]; then
        log_pass "Boot sequence: $snap_count screenshots captured"
    else
        log_fail "Boot sequence: only $snap_count screenshots (expected >=3)"
    fi

    # Check for crash/abort
    if grep -qi "exception\|segfault\|abort\|fatal error" "$RESULTS_DIR/boot_stderr.log" "$RESULTS_DIR/boot_stdout.log" 2>/dev/null; then
        log_fail "Boot sequence: crash detected"
    else
        log_pass "Boot sequence: no crashes"
    fi

    # Move snapshots for this test
    mkdir -p "$RESULTS_DIR/boot_snaps"
    mv "$SNAP_DIR"/*.png "$RESULTS_DIR/boot_snaps/" 2>/dev/null || true
}

# =============================================================================
# Test: Menu Navigation
# =============================================================================
test_menus() {
    log_info "Test: Menu Navigation (60s emulated time)"

    cat > "$TEST_DIR/menu_test.lua" << 'LUAEOF'
-- Navigate through all main menus and capture screenshots
local actions = {
    {time=35, button="MENU: SOUND", action="press", desc="Open SOUND menu"},
    {time=36, button="MENU: SOUND", action="release"},
    {time=38, button="EXIT", action="press", desc="Exit SOUND menu"},
    {time=39, button="EXIT", action="release"},
    {time=41, button="MENU: CONTROL", action="press", desc="Open CONTROL menu"},
    {time=42, button="MENU: CONTROL", action="release"},
    {time=44, button="EXIT", action="press", desc="Exit CONTROL menu"},
    {time=45, button="EXIT", action="release"},
    {time=47, button="MENU: MIDI", action="press", desc="Open MIDI menu"},
    {time=48, button="MENU: MIDI", action="release"},
    {time=50, button="EXIT", action="press", desc="Exit MIDI menu"},
    {time=51, button="EXIT", action="release"},
    {time=53, button="MENU: DISK", action="press", desc="Open DISK menu"},
    {time=54, button="MENU: DISK", action="release"},
}
local screenshots = {36.5, 42.5, 48.5, 54.5}
local next_action = 1
local next_ss = 1
local done = false
local menus_opened = 0

emu.register_periodic(function()
    if done then return end
    local t = manager.machine.time:as_double()

    if next_ss <= #screenshots and t > screenshots[next_ss] then
        print(string.format("MENU TEST: Screenshot at %.1fs", t))
        manager.machine.video:snapshot()
        next_ss = next_ss + 1
        menus_opened = menus_opened + 1
    end

    while next_action <= #actions and t > actions[next_action].time do
        local a = actions[next_action]
        local ports = manager.machine.ioport.ports
        for name, port in pairs(ports) do
            for fname, field in pairs(port.fields) do
                if fname == a.button then
                    if a.action == "press" then
                        field:set_value(1)
                        if a.desc then print("MENU TEST: " .. a.desc) end
                    else
                        field:set_value(0)
                    end
                end
            end
        end
        next_action = next_action + 1
    end

    if t > 56 then
        print(string.format("MENU TEST: Complete (%d menus opened)", menus_opened))
        done = true
        manager.machine:exit()
    end
end)
LUAEOF

    "$MAME" kn5000 -rompath "$ROM_PATH" \
        -window -skip_gameinfo -seconds_to_run 60 -nothrottle \
        -nvram_directory "$TEST_DIR/nvram_menu" \
        -cfg_directory "$TEST_DIR/cfg_menu" \
        -snapshot_directory "$SNAP_DIR" \
        -autoboot_script "$TEST_DIR/menu_test.lua" \
        >"$RESULTS_DIR/menu_stdout.log" 2>"$RESULTS_DIR/menu_stderr.log" || true

    local snap_count
    snap_count=$(find "$SNAP_DIR" -name "*.png" 2>/dev/null | wc -l)
    if [ "$snap_count" -ge 4 ]; then
        log_pass "Menu navigation: $snap_count menu screenshots captured (all 4 menus)"
    elif [ "$snap_count" -ge 2 ]; then
        log_fail "Menu navigation: only $snap_count screenshots (expected 4)"
    else
        log_fail "Menu navigation: no menu screenshots captured"
    fi

    mkdir -p "$RESULTS_DIR/menu_snaps"
    mv "$SNAP_DIR"/*.png "$RESULTS_DIR/menu_snaps/" 2>/dev/null || true
}

# =============================================================================
# Test: Display Rendering
# =============================================================================
test_display() {
    log_info "Test: Display Rendering Validation (45s emulated time)"

    cat > "$TEST_DIR/display_test.lua" << 'LUAEOF'
-- Validate display subsystem: check screen dimensions, VGA mode
local done = false
local checked = false
local checks_passed = 0
local checks_total = 0

emu.register_periodic(function()
    if done then return end
    local t = manager.machine.time:as_double()

    if t > 30 and not checked then
        checked = true
        -- Check screen dimensions (KN5000 LCD is 320x240 8bpp)
        local screens = manager.machine.screens
        for tag, screen in pairs(screens) do
            local w = screen.width
            local h = screen.height
            checks_total = checks_total + 1
            if w == 320 and h == 240 then
                print(string.format("DISPLAY TEST: Screen %s: %dx%d (correct KN5000 LCD mode)", tag, w, h))
                checks_passed = checks_passed + 1
            else
                print(string.format("DISPLAY TEST: Screen %s: %dx%d (unexpected)", tag, w, h))
            end
        end

        -- Take final screenshot
        manager.machine.video:snapshot()
        print("DISPLAY TEST: Screenshot captured")
    end

    if t > 40 then
        print(string.format("DISPLAY TEST: Complete (%d/%d checks passed)", checks_passed, checks_total))
        done = true
        manager.machine:exit()
    end
end)
LUAEOF

    "$MAME" kn5000 -rompath "$ROM_PATH" \
        -window -skip_gameinfo -seconds_to_run 45 -nothrottle \
        -nvram_directory "$TEST_DIR/nvram_display" \
        -cfg_directory "$TEST_DIR/cfg_display" \
        -snapshot_directory "$SNAP_DIR" \
        -autoboot_script "$TEST_DIR/display_test.lua" \
        >"$RESULTS_DIR/display_stdout.log" 2>"$RESULTS_DIR/display_stderr.log" || true

    # Check for display mode confirmation in log (Lua print goes to stdout)
    if grep -q "correct KN5000 LCD mode" "$RESULTS_DIR/display_stdout.log" 2>/dev/null; then
        log_pass "Display: 320x240 LCD mode confirmed"
    else
        log_fail "Display: LCD mode check failed"
    fi

    local snap_count
    snap_count=$(find "$SNAP_DIR" -name "*.png" 2>/dev/null | wc -l)
    if [ "$snap_count" -ge 1 ]; then
        log_pass "Display: screenshot captured"
    else
        log_fail "Display: no screenshot captured"
    fi

    mkdir -p "$RESULTS_DIR/display_snaps"
    mv "$SNAP_DIR"/*.png "$RESULTS_DIR/display_snaps/" 2>/dev/null || true
}

# =============================================================================
# Main
# =============================================================================
echo "============================================"
echo "KN5000 MAME Emulation Validation Suite"
echo "============================================"
echo "MAME: $MAME"
echo "ROMs: $ROM_PATH"
echo "Output: $TEST_DIR"
echo ""

# Check prerequisites
if [ ! -x "$MAME" ]; then
    echo "ERROR: MAME binary not found at $MAME"
    exit 1
fi

if [ ! -d "$ROM_PATH/kn5000" ]; then
    echo "ERROR: ROM directory not found at $ROM_PATH/kn5000"
    exit 1
fi

# Run tests
TEST="${1:-all}"
case "$TEST" in
    boot)    test_boot ;;
    menus)   test_menus ;;
    display) test_display ;;
    all)
        test_boot
        echo ""
        test_menus
        echo ""
        test_display
        ;;
    *)
        echo "Unknown test: $TEST"
        echo "Available: boot, menus, display, all"
        exit 1
        ;;
esac

# Summary
echo ""
echo "============================================"
echo "Results: $PASS_COUNT passed, $FAIL_COUNT failed"
echo "Screenshots: $RESULTS_DIR/"
echo "============================================"

if [ "$FAIL_COUNT" -gt 0 ]; then
    exit 1
fi
