#!/usr/bin/env python3
"""
Create test floppy disk images for MAME KN5000 FDC testing.

Produces standard 1.44MB FAT12 disk images in raw .img format, matching
the format used by original Technics KN5000 firmware update discs.

MAME format notes:
  The KN5000 MAME driver uses default_mfm_floppy_formats, which accepts:
    MFI (.mfi)  - MAME's native floppy image format
    MFM (.mfm)  - HxCFloppyEmulator format
    TD0 (.td0)  - Teledisk format (read-only)
    IMD (.imd)  - ImageDisk format (read-only)
    86F (.86f)  - 86Box format
    D88 (.d88)  - Japanese format
    CQM (.cqm)  - CopyQM format
    DSK (.dsk)  - CPC DSK format (read-only)

  It does NOT include FLOPPY_PC_FORMAT (raw .img), so raw images must be
  converted to MFI using MAME's floptool:
    floptool flopconvert pc mfi input.img output.mfi

  floptool can also manipulate files on the raw image before conversion:
    floptool flopwrite pc pc_fat image.img localfile.txt DEST.TXT
    floptool flopdir pc pc_fat image.img

Usage:
    python scripts/make_test_floppy.py [options]

Options:
    --output PATH       Output raw .img file (default: test_floppy.img)
    --mfi               Also produce .mfi via floptool (requires MAME floptool)
    --floptool PATH     Path to floptool (default: /mnt/shared/mame/floptool)
    --add-file PATH     Add a file to the image (can be repeated)
    --volume-label LBL  FAT volume label (default: KN5000TEST)
    --technics          Use Technics-compatible OEM ID and boot sector format
    --empty             Create empty formatted disk (no test file)
"""

import argparse
import os
import struct
import subprocess
import sys

# ============================================================================
# Floppy disc parameters (standard 1.44MB 3.5" HD)
# ============================================================================
FLOPPY_SIZE = 1474560           # 2880 sectors x 512 bytes
SECTOR_SIZE = 512
SECTORS_PER_CLUSTER = 1
RESERVED_SECTORS = 1
NUM_FATS = 2
ROOT_ENTRIES = 224
TOTAL_SECTORS = 2880
SECTORS_PER_FAT = 9
SECTORS_PER_TRACK = 18
NUM_HEADS = 2
MEDIA_DESCRIPTOR = 0xF0         # 3.5" HD floppy

# Derived layout
FAT1_START = RESERVED_SECTORS * SECTOR_SIZE                             # 0x0200
FAT2_START = (RESERVED_SECTORS + SECTORS_PER_FAT) * SECTOR_SIZE         # 0x1400
ROOT_DIR_START = (RESERVED_SECTORS + NUM_FATS * SECTORS_PER_FAT) * SECTOR_SIZE  # 0x2600
ROOT_DIR_SECTORS = (ROOT_ENTRIES * 32 + SECTOR_SIZE - 1) // SECTOR_SIZE  # 14
DATA_START = ROOT_DIR_START + ROOT_DIR_SECTORS * SECTOR_SIZE            # 0x4200
FIRST_DATA_CLUSTER = 2


def make_boot_sector(oem_id=b"MSDOS5.0", volume_label=b"KN5000TEST ", technics=False):
    """Build a 512-byte FAT12 boot sector.

    Args:
        oem_id: 8-byte OEM identifier
        volume_label: 11-byte volume label (space-padded)
        technics: If True, use Technics-compatible format (EB 1C jump, no 0x55AA)
    """
    boot = bytearray(SECTOR_SIZE)

    if technics:
        # Technics format: short jump to 0x1E, no boot signature
        boot[0] = 0xEB          # JMP short
        boot[1] = 0x1C          # offset to 0x1E
        boot[2] = 0x90          # NOP
        oem_id = b"Technics"
    else:
        # Standard PC format
        boot[0] = 0xEB          # JMP short
        boot[1] = 0x3C          # offset to 0x3E
        boot[2] = 0x90          # NOP

    # OEM ID (8 bytes, space-padded)
    oem_padded = oem_id[:8].ljust(8, b' ')
    boot[3:11] = oem_padded

    # BIOS Parameter Block (BPB)
    struct.pack_into('<H', boot, 11, SECTOR_SIZE)           # Bytes per sector
    boot[13] = SECTORS_PER_CLUSTER                          # Sectors per cluster
    struct.pack_into('<H', boot, 14, RESERVED_SECTORS)      # Reserved sectors
    boot[16] = NUM_FATS                                     # Number of FATs
    struct.pack_into('<H', boot, 17, ROOT_ENTRIES)          # Root dir entries
    struct.pack_into('<H', boot, 19, TOTAL_SECTORS)         # Total sectors (16-bit)
    boot[21] = MEDIA_DESCRIPTOR                             # Media descriptor
    struct.pack_into('<H', boot, 22, SECTORS_PER_FAT)       # Sectors per FAT
    struct.pack_into('<H', boot, 24, SECTORS_PER_TRACK)     # Sectors per track
    struct.pack_into('<H', boot, 26, NUM_HEADS)             # Number of heads
    struct.pack_into('<I', boot, 28, 0)                     # Hidden sectors
    struct.pack_into('<I', boot, 32, 0)                     # Total sectors (32-bit, 0 = use 16-bit)

    if technics:
        # Technics: minimal extended BPB
        boot[37] = 0x01         # Reserved byte (matches original discs)
        # Boot code at 0x1E: infinite loop (x86: JMP $)
        boot[0x1E] = 0xEB
        boot[0x1F] = 0xFE
    else:
        # Standard extended BPB (FAT12/16)
        boot[36] = 0x00         # Drive number (0 = floppy)
        boot[37] = 0x00         # Reserved
        boot[38] = 0x29         # Extended boot signature
        struct.pack_into('<I', boot, 39, 0x12345678)    # Volume serial number
        # Volume label (11 bytes, space-padded)
        label = volume_label[:11].ljust(11, b' ')
        boot[43:54] = label
        # File system type
        boot[54:62] = b"FAT12   "
        # Boot code at 0x3E: infinite loop
        boot[0x3E] = 0xEB
        boot[0x3F] = 0xFE
        # Boot signature
        boot[510] = 0x55
        boot[511] = 0xAA

    return bytes(boot)


def fat12_set_entry(fat, cluster, value):
    """Write a 12-bit value into a FAT12 table at the given cluster index."""
    byte_offset = (cluster * 3) // 2
    if cluster % 2 == 0:
        fat[byte_offset] = value & 0xFF
        fat[byte_offset + 1] = (fat[byte_offset + 1] & 0xF0) | ((value >> 8) & 0x0F)
    else:
        fat[byte_offset] = (fat[byte_offset] & 0x0F) | ((value & 0x0F) << 4)
        fat[byte_offset + 1] = (value >> 4) & 0xFF


def make_fat_table(file_sizes):
    """Build a FAT12 table for the given list of file sizes.

    Files are allocated contiguously starting at cluster 2.
    Returns a bytearray of SECTORS_PER_FAT * SECTOR_SIZE bytes.
    """
    fat = bytearray(SECTORS_PER_FAT * SECTOR_SIZE)

    # Cluster 0: media descriptor + 0xFF padding
    fat12_set_entry(fat, 0, 0xFF0 | MEDIA_DESCRIPTOR)
    # Cluster 1: end-of-chain marker
    fat12_set_entry(fat, 1, 0xFFF)

    cluster = FIRST_DATA_CLUSTER
    for size in file_sizes:
        if size == 0:
            # Zero-length file: still needs 1 cluster allocated
            fat12_set_entry(fat, cluster, 0xFFF)
            cluster += 1
        else:
            num_clusters = (size + SECTOR_SIZE * SECTORS_PER_CLUSTER - 1) // (SECTOR_SIZE * SECTORS_PER_CLUSTER)
            for i in range(num_clusters):
                if i == num_clusters - 1:
                    fat12_set_entry(fat, cluster, 0xFFF)    # EOF
                else:
                    fat12_set_entry(fat, cluster, cluster + 1)
                cluster += 1

    return fat


def make_dir_entry(name_8, ext_3, size, first_cluster, attr=0x20):
    """Build a 32-byte FAT directory entry.

    Args:
        name_8: Filename (up to 8 chars, will be space-padded)
        ext_3: Extension (up to 3 chars, will be space-padded)
        size: File size in bytes
        first_cluster: First cluster number
        attr: File attributes (0x20 = archive)
    """
    entry = bytearray(32)
    entry[0:8] = name_8.encode('ascii')[:8].ljust(8, b' ')
    entry[8:11] = ext_3.encode('ascii')[:3].ljust(3, b' ')
    entry[11] = attr
    # Bytes 12-21: reserved, creation time, access date (leave as 0)
    # Write time/date could be set but firmware doesn't check them
    struct.pack_into('<H', entry, 26, first_cluster)
    struct.pack_into('<I', entry, 28, size)
    return bytes(entry)


def make_volume_label_entry(label):
    """Build a 32-byte volume label directory entry."""
    entry = bytearray(32)
    padded = label.encode('ascii')[:11].ljust(11, b' ')
    entry[0:11] = padded
    entry[11] = 0x08    # Volume label attribute
    return bytes(entry)


def create_floppy_image(files=None, volume_label="KN5000TEST", technics=False):
    """Create a 1.44MB FAT12 floppy disk image.

    Args:
        files: List of (filename, content_bytes) tuples. Filenames should be
               in 8.3 format (e.g., "TEST.TXT"). If None, creates empty disk.
        volume_label: Volume label string (max 11 chars)
        technics: Use Technics-compatible boot sector format

    Returns:
        bytes: 1474560-byte raw disk image
    """
    image = bytearray(FLOPPY_SIZE)

    # Parse files into (name_8, ext_3, content) tuples
    parsed_files = []
    if files:
        for filename, content in files:
            if '.' in filename:
                name, ext = filename.rsplit('.', 1)
            else:
                name, ext = filename, ''
            parsed_files.append((name.upper(), ext.upper(), content))

    # 1. Boot sector
    label_bytes = volume_label.encode('ascii')[:11].ljust(11, b' ')
    image[0:SECTOR_SIZE] = make_boot_sector(
        volume_label=label_bytes,
        technics=technics
    )

    # 2. FAT tables
    file_sizes = [len(f[2]) for f in parsed_files]
    fat = make_fat_table(file_sizes)
    image[FAT1_START:FAT1_START + len(fat)] = fat
    image[FAT2_START:FAT2_START + len(fat)] = fat

    # 3. Root directory
    dir_offset = ROOT_DIR_START
    # Volume label entry
    image[dir_offset:dir_offset + 32] = make_volume_label_entry(volume_label)
    dir_offset += 32

    cluster = FIRST_DATA_CLUSTER
    for name_8, ext_3, content in parsed_files:
        entry = make_dir_entry(name_8, ext_3, len(content), cluster)
        image[dir_offset:dir_offset + 32] = entry
        dir_offset += 32
        num_clusters = max(1, (len(content) + SECTOR_SIZE - 1) // SECTOR_SIZE)
        cluster += num_clusters

    # 4. File data
    data_offset = DATA_START
    for name_8, ext_3, content in parsed_files:
        image[data_offset:data_offset + len(content)] = content
        num_clusters = max(1, (len(content) + SECTOR_SIZE - 1) // SECTOR_SIZE)
        data_offset += num_clusters * SECTOR_SIZE

    return bytes(image)


def make_test_content():
    """Create test file content for FDC verification."""
    lines = [
        "KN5000 FDC Test Floppy\r\n",
        "======================\r\n",
        "\r\n",
        "This is a test floppy image for verifying the MAME KN5000\r\n",
        "floppy disk controller (UPD72068) emulation.\r\n",
        "\r\n",
        "Format: 1.44MB FAT12 (2880 sectors, 18 s/t, 80 tracks, 2 heads)\r\n",
        "FDC: UPD72068GF-3B9 at IC208 (UPD765-compatible)\r\n",
        "FDC I/O: MSR at 0x110008, FIFO at 0x11000A, DMA at 0x120000\r\n",
        "\r\n",
        "Sector layout:\r\n",
        "  Sector  0      : Boot sector (BPB)\r\n",
        "  Sectors 1-9    : FAT #1\r\n",
        "  Sectors 10-18  : FAT #2\r\n",
        "  Sectors 19-32  : Root directory (224 entries)\r\n",
        "  Sectors 33+    : Data area\r\n",
        "\r\n",
        "Note: KN5000 firmware reads from sector 33 (0x21) onwards.\r\n",
        "It never reads the boot sector or parses the BPB.\r\n",
    ]
    return ''.join(lines).encode('ascii')


def main():
    parser = argparse.ArgumentParser(
        description="Create test floppy disk images for MAME KN5000 FDC testing."
    )
    parser.add_argument(
        '--output', '-o',
        default=os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                             'test_floppy.img'),
        help='Output raw .img file path (default: ../test_floppy.img)'
    )
    parser.add_argument(
        '--mfi', action='store_true',
        help='Also produce .mfi file via MAME floptool'
    )
    parser.add_argument(
        '--floptool',
        default='/mnt/shared/mame/floptool',
        help='Path to MAME floptool (default: /mnt/shared/mame/floptool)'
    )
    parser.add_argument(
        '--add-file', action='append', dest='add_files', metavar='PATH',
        help='Add a local file to the image (can be repeated)'
    )
    parser.add_argument(
        '--volume-label', default='KN5000TEST',
        help='FAT volume label (default: KN5000TEST)'
    )
    parser.add_argument(
        '--technics', action='store_true',
        help='Use Technics-compatible boot sector (OEM ID "Technics", no 0x55AA)'
    )
    parser.add_argument(
        '--empty', action='store_true',
        help='Create empty formatted disk (no default test file)'
    )
    args = parser.parse_args()

    # Build file list
    files = []

    if not args.empty:
        # Add default test file
        files.append(("README.TXT", make_test_content()))

    if args.add_files:
        for filepath in args.add_files:
            basename = os.path.basename(filepath).upper()
            # Truncate to 8.3 format
            if '.' in basename:
                name, ext = basename.rsplit('.', 1)
                fat_name = f"{name[:8]}.{ext[:3]}"
            else:
                fat_name = basename[:8]
            with open(filepath, 'rb') as f:
                content = f.read()
            files.append((fat_name, content))
            print(f"  Adding: {fat_name} ({len(content):,} bytes)")

    # Check total data fits
    total_data = sum(len(f[1]) for f in files)
    data_capacity = FLOPPY_SIZE - DATA_START
    if total_data > data_capacity:
        print(f"ERROR: Total file data ({total_data:,} bytes) exceeds "
              f"data area capacity ({data_capacity:,} bytes)", file=sys.stderr)
        return 1

    # Create the image
    image = create_floppy_image(
        files=files,
        volume_label=args.volume_label,
        technics=args.technics
    )

    # Write raw .img
    with open(args.output, 'wb') as f:
        f.write(image)
    print(f"Created raw floppy image: {args.output}")
    print(f"  Size: {len(image):,} bytes ({len(image) // SECTOR_SIZE} sectors)")
    print(f"  Format: FAT12, {SECTORS_PER_TRACK} sectors/track, "
          f"{NUM_HEADS} heads, 80 tracks")
    print(f"  Volume: {args.volume_label}")
    if files:
        print(f"  Files: {len(files)}")
        for fname, content in files:
            print(f"    {fname}: {len(content):,} bytes")
    else:
        print(f"  Files: (empty)")

    # Convert to MFI if requested
    if args.mfi:
        mfi_path = os.path.splitext(args.output)[0] + '.mfi'
        if not os.path.exists(args.floptool):
            print(f"\nWARNING: floptool not found at {args.floptool}", file=sys.stderr)
            print("  Cannot convert to MFI. Use --floptool to specify path.", file=sys.stderr)
            print(f"\n  Manual conversion:", file=sys.stderr)
            print(f"  {args.floptool} flopconvert pc mfi {args.output} {mfi_path}",
                  file=sys.stderr)
            return 1

        print(f"\nConverting to MFI format...")
        result = subprocess.run(
            [args.floptool, 'flopconvert', 'pc', 'mfi', args.output, mfi_path],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            print(f"ERROR: floptool conversion failed: {result.stderr}", file=sys.stderr)
            return 1
        mfi_size = os.path.getsize(mfi_path)
        print(f"Created MFI floppy image: {mfi_path}")
        print(f"  Size: {mfi_size:,} bytes")

    # Print usage instructions
    print(f"\n--- MAME Usage ---")
    print(f"The KN5000 driver uses default_mfm_floppy_formats (NOT raw PC format).")
    print(f"Raw .img files must be converted to .mfi before loading in MAME:")
    print(f"")
    print(f"  # Convert to MAME native format:")
    print(f"  /mnt/shared/mame/floptool flopconvert pc mfi {args.output} "
          f"{os.path.splitext(args.output)[0]}.mfi")
    print(f"")
    print(f"  # Load in MAME:")
    print(f"  mame kn5000 -flop1 {os.path.splitext(args.output)[0]}.mfi")
    print(f"")
    print(f"  # Or use floptool to manipulate files on the raw image first:")
    print(f"  /mnt/shared/mame/floptool flopdir pc pc_fat {args.output}")
    print(f"  /mnt/shared/mame/floptool flopwrite pc pc_fat {args.output} file.bin DEST.BIN")

    return 0


if __name__ == "__main__":
    sys.exit(main())
