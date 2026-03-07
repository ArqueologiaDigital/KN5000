#!/usr/bin/env python3
"""
Parse and analyze KN5000 system update floppy disc images.

Reads a 1.44MB floppy disc image and extracts:
  - Boot sector / BPB analysis
  - FAT12 structure
  - Disc type signature detection
  - Payload extraction (raw ROM or SLIDE4K compressed)
  - SLIDE4K header analysis (for compressed types)

Usage:
    python scripts/parse_update_disc.py <disc_image>
    python scripts/parse_update_disc.py <disc_image> --extract <output_dir>
    python scripts/parse_update_disc.py <disc_image> --extract-rom <output_file>

Examples:
    python scripts/parse_update_disc.py kn5000_v10_disk.img
    python scripts/parse_update_disc.py kn5000_v10_disk.img --extract /tmp/disc_contents
    python scripts/parse_update_disc.py kn5000_v10_disk.img --extract-rom /tmp/program.rom
"""

import sys
import os
import struct
import argparse

# ============================================================================
# Constants
# ============================================================================

SECTOR_SIZE = 512
FLOPPY_SIZE = 1474560  # 2880 sectors

# Disc type signatures (38 bytes each)
DISC_SIGNATURES = {
    1: b'Technics KN5000 Program  DATA FILE 1/2',
    2: b'Technics KN5000 Program  DATA FILE 2/2',
    3: b'Technics KN5000 Table    DATA FILE 1/2',
    4: b'Technics KN5000 Table    DATA FILE 2/2',
    5: b'Technics KN5000 CMPCUSTOMDATA FILE    ',
    6: b'Technics KN5000 HD-AEPRG DATA FILE    ',
    7: b'Technics KN5000 Program  DATA FILE PCK',
    8: b'Technics KN5000 Table    DATA FILE PCK',
}

DISC_TYPE_NAMES = {
    1: 'Program ROM (uncompressed, disc 1/2)',
    2: 'Program ROM (uncompressed, disc 2/2)',
    3: 'Table Data ROM (uncompressed, disc 1/2)',
    4: 'Table Data ROM (uncompressed, disc 2/2)',
    5: 'Custom Data (compressed)',
    6: 'HDAE5000 Extension ROM (uncompressed)',
    7: 'Program ROM (SLIDE4K compressed)',
    8: 'Table Data ROM (SLIDE4K compressed)',
}

# FAT12 layout
RESERVED_SECTORS = 1
SECTORS_PER_FAT = 9
NUM_FATS = 2
ROOT_DIR_ENTRIES = 224
ROOT_DIR_SECTORS = (ROOT_DIR_ENTRIES * 32 + SECTOR_SIZE - 1) // SECTOR_SIZE
DATA_START_SECTOR = RESERVED_SECTORS + (SECTORS_PER_FAT * NUM_FATS) + ROOT_DIR_SECTORS
DATA_START_OFFSET = DATA_START_SECTOR * SECTOR_SIZE

# Known file positions in data area
SIG_FILE_SECTOR = 33   # Sector 33 = cluster 2
SIG_FILE_OFFSET = SIG_FILE_SECTOR * SECTOR_SIZE  # 0x4200
DATA_FILE_SECTOR = 36  # Sector 36 = cluster 5
DATA_FILE_OFFSET = DATA_FILE_SECTOR * SECTOR_SIZE  # 0x4800


def parse_bpb(data):
    """Parse BIOS Parameter Block from boot sector."""
    if len(data) < SECTOR_SIZE:
        return None

    bpb = {}
    bpb['jump'] = data[0:3]
    bpb['oem_id'] = data[3:11].decode('ascii', errors='replace').rstrip()
    bpb['bytes_per_sector'] = struct.unpack_from('<H', data, 0x0B)[0]
    bpb['sectors_per_cluster'] = data[0x0D]
    bpb['reserved_sectors'] = struct.unpack_from('<H', data, 0x0E)[0]
    bpb['num_fats'] = data[0x10]
    bpb['root_entries'] = struct.unpack_from('<H', data, 0x11)[0]
    bpb['total_sectors'] = struct.unpack_from('<H', data, 0x13)[0]
    bpb['media_descriptor'] = data[0x15]
    bpb['sectors_per_fat'] = struct.unpack_from('<H', data, 0x16)[0]
    bpb['sectors_per_track'] = struct.unpack_from('<H', data, 0x18)[0]
    bpb['num_heads'] = struct.unpack_from('<H', data, 0x1A)[0]
    bpb['hidden_sectors'] = struct.unpack_from('<I', data, 0x1C)[0]
    bpb['boot_code'] = data[0x1E:0x20]
    return bpb


def detect_disc_type(data):
    """Detect disc type by matching signature at sector 33."""
    if len(data) < SIG_FILE_OFFSET + 38:
        return None, None

    sig_data = data[SIG_FILE_OFFSET:SIG_FILE_OFFSET + 38]
    for type_id, sig in DISC_SIGNATURES.items():
        if sig_data == sig:
            return type_id, sig.decode('ascii')

    return None, sig_data.decode('ascii', errors='replace')


def parse_signature_file(data):
    """Parse the signature file (TECHNICS.PRP or TECHNICS.AE)."""
    sig_data = data[SIG_FILE_OFFSET:]
    # Find end of signature string (look for CR/LF or null)
    end = SIG_FILE_OFFSET
    for i in range(SIG_FILE_OFFSET, min(SIG_FILE_OFFSET + 128, len(data))):
        if data[i] == 0:
            end = i
            break
    else:
        # Look for double CR/LF
        for i in range(SIG_FILE_OFFSET, min(SIG_FILE_OFFSET + 128, len(data) - 1)):
            if data[i:i+2] == b'\r\n':
                # Check if followed by another CR/LF or null
                if i + 2 < len(data) and data[i+2:i+4] in (b'\r\n', b'\x00\x00'):
                    end = i + 4
                    break
                end = i + 2

    sig_text = data[SIG_FILE_OFFSET:end]
    return sig_text


def parse_slide4k_header(data, offset):
    """Parse SLIDE4K compression header."""
    if len(data) < offset + 11:
        return None

    magic = data[offset:offset + 8]
    if magic != b'SLIDE4K\x00':
        return None

    # 3-byte big-endian decompressed size
    size_bytes = data[offset + 8:offset + 11]
    decompressed_size = (size_bytes[0] << 16) | (size_bytes[1] << 8) | size_bytes[2]

    return {
        'magic': magic,
        'decompressed_size': decompressed_size,
        'header_size': 11,
        'data_offset': offset + 11,
    }


def parse_root_directory(data):
    """Parse FAT12 root directory entries."""
    root_offset = (RESERVED_SECTORS + SECTORS_PER_FAT * NUM_FATS) * SECTOR_SIZE
    entries = []

    for i in range(ROOT_DIR_ENTRIES):
        entry_offset = root_offset + i * 32
        if entry_offset + 32 > len(data):
            break

        entry = data[entry_offset:entry_offset + 32]
        first_byte = entry[0]

        # Skip empty/deleted entries
        if first_byte == 0x00:
            break
        if first_byte == 0xE5:
            continue

        name = entry[0:8].decode('ascii', errors='replace').rstrip()
        ext = entry[8:11].decode('ascii', errors='replace').rstrip()
        attrs = entry[11]
        cluster = struct.unpack_from('<H', entry, 26)[0]
        size = struct.unpack_from('<I', entry, 28)[0]

        filename = f"{name}.{ext}" if ext else name
        entries.append({
            'filename': filename,
            'attrs': attrs,
            'cluster': cluster,
            'size': size,
            'offset': entry_offset,
        })

    return entries


def print_analysis(filepath, data):
    """Print full analysis of disc image."""
    print(f"=== KN5000 Update Disc Analysis ===")
    print(f"File: {filepath}")
    print(f"Size: {len(data)} bytes ({len(data) // SECTOR_SIZE} sectors)")
    print()

    # BPB
    bpb = parse_bpb(data)
    if bpb:
        print("--- Boot Sector (BPB) ---")
        print(f"  OEM ID:            {bpb['oem_id']!r}")
        print(f"  Bytes/sector:      {bpb['bytes_per_sector']}")
        print(f"  Sectors/cluster:   {bpb['sectors_per_cluster']}")
        print(f"  Reserved sectors:  {bpb['reserved_sectors']}")
        print(f"  FAT count:         {bpb['num_fats']}")
        print(f"  Root entries:      {bpb['root_entries']}")
        print(f"  Total sectors:     {bpb['total_sectors']}")
        print(f"  Media descriptor:  0x{bpb['media_descriptor']:02X}")
        print(f"  Sectors/FAT:       {bpb['sectors_per_fat']}")
        print(f"  Sectors/track:     {bpb['sectors_per_track']}")
        print(f"  Heads:             {bpb['num_heads']}")
        print(f"  Boot code:         {bpb['boot_code'].hex()}")
        print()

    # Root directory
    entries = parse_root_directory(data)
    if entries:
        print("--- Root Directory ---")
        for entry in entries:
            attr_str = ""
            if entry['attrs'] & 0x08:
                attr_str = " [VOLUME LABEL]"
            elif entry['attrs'] & 0x10:
                attr_str = " [DIR]"
            print(f"  {entry['filename']:15s}  {entry['size']:8d} bytes  "
                  f"cluster {entry['cluster']:4d}  "
                  f"sector {DATA_START_SECTOR + entry['cluster'] - 2:4d}  "
                  f"offset 0x{(DATA_START_SECTOR + entry['cluster'] - 2) * SECTOR_SIZE:06X}"
                  f"{attr_str}")
        print()

    # Disc type detection
    type_id, sig = detect_disc_type(data)
    print("--- Disc Type Detection ---")
    if type_id:
        print(f"  Type:      {type_id}")
        print(f"  Name:      {DISC_TYPE_NAMES[type_id]}")
        print(f"  Signature: {sig!r}")
    else:
        print(f"  Type:      UNKNOWN")
        print(f"  Raw data:  {sig!r}")
    print()

    # Signature file
    sig_text = parse_signature_file(data)
    print("--- Signature File ---")
    print(f"  Offset:  0x{SIG_FILE_OFFSET:06X} (sector {SIG_FILE_SECTOR})")
    print(f"  Content: {sig_text!r}")
    print()

    # Payload analysis
    print("--- Payload ---")
    print(f"  Data offset: 0x{DATA_FILE_OFFSET:06X} (sector {DATA_FILE_SECTOR})")

    if type_id in (7, 8):
        # SLIDE4K compressed
        slide4k = parse_slide4k_header(data, DATA_FILE_OFFSET)
        if slide4k:
            compressed_size = len(data) - DATA_FILE_OFFSET
            # Find actual end (scan backwards for non-0xE5 fill)
            actual_end = len(data)
            while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
                actual_end -= 1
            compressed_size = actual_end - DATA_FILE_OFFSET
            ratio = compressed_size / slide4k['decompressed_size'] * 100

            print(f"  Format:          SLIDE4K compressed")
            print(f"  Magic:           {slide4k['magic']!r}")
            print(f"  Decompressed:    {slide4k['decompressed_size']:,} bytes "
                  f"(0x{slide4k['decompressed_size']:X})")
            print(f"  Compressed:      ~{compressed_size:,} bytes")
            print(f"  Ratio:           ~{ratio:.1f}%")
            print(f"  Data starts at:  0x{slide4k['data_offset']:06X}")
        else:
            print(f"  WARNING: Expected SLIDE4K header not found!")
            print(f"  First 16 bytes:  {data[DATA_FILE_OFFSET:DATA_FILE_OFFSET+16].hex()}")
    elif type_id == 6:
        # Uncompressed HDAE5000
        # Find actual payload size
        actual_end = len(data)
        while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
            actual_end -= 1
        payload_size = actual_end - DATA_FILE_OFFSET
        print(f"  Format:          Raw (uncompressed)")
        print(f"  Payload size:    {payload_size:,} bytes (0x{payload_size:X})")
        print(f"  Target:          HDAE5000 Extension ROM at 0x280000")
    elif type_id in (1, 2, 3, 4):
        actual_end = len(data)
        while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
            actual_end -= 1
        payload_size = actual_end - DATA_FILE_OFFSET
        print(f"  Format:          Raw (uncompressed, 2-disc set)")
        print(f"  Payload size:    {payload_size:,} bytes (0x{payload_size:X})")
    elif type_id == 5:
        actual_end = len(data)
        while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
            actual_end -= 1
        payload_size = actual_end - DATA_FILE_OFFSET
        print(f"  Format:          Compressed custom data")
        print(f"  Payload size:    {payload_size:,} bytes (0x{payload_size:X})")
        print(f"  Target:          Custom Data Flash at 0x300000")
    else:
        print(f"  Format:          Unknown")
        print(f"  First 16 bytes:  {data[DATA_FILE_OFFSET:DATA_FILE_OFFSET+16].hex()}")

    print()

    # Fill byte analysis
    fill_count = data.count(0xE5)
    print("--- Fill Bytes ---")
    print(f"  0xE5 fill bytes: {fill_count:,} ({fill_count / len(data) * 100:.1f}% of disc)")
    print()


def extract_files(data, output_dir):
    """Extract all files from the disc image."""
    os.makedirs(output_dir, exist_ok=True)

    entries = parse_root_directory(data)
    for entry in entries:
        if entry['attrs'] & 0x08:  # Volume label
            continue
        offset = (DATA_START_SECTOR + entry['cluster'] - 2) * SECTOR_SIZE
        file_data = data[offset:offset + entry['size']]
        filepath = os.path.join(output_dir, entry['filename'])
        with open(filepath, 'wb') as f:
            f.write(file_data)
        print(f"  Extracted: {entry['filename']} ({entry['size']} bytes)")


def extract_rom(data, output_file):
    """Extract the ROM payload (decompressed if SLIDE4K)."""
    type_id, _ = detect_disc_type(data)

    if type_id in (7, 8):
        slide4k = parse_slide4k_header(data, DATA_FILE_OFFSET)
        if not slide4k:
            print("ERROR: SLIDE4K header not found", file=sys.stderr)
            sys.exit(1)

        # Try to import the decompressor
        try:
            scripts_dir = os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                '..', 'roms-disasm', 'scripts'
            )
            sys.path.insert(0, os.path.abspath(scripts_dir))
            from compress_lzss import decompress_slide4k
            compressed_data = data[DATA_FILE_OFFSET:]
            rom_data = decompress_slide4k(compressed_data)
            with open(output_file, 'wb') as f:
                f.write(rom_data)
            print(f"Decompressed {len(rom_data):,} bytes to {output_file}")
        except ImportError:
            print("ERROR: Cannot import decompress_slide4k from roms-disasm/scripts/compress_lzss.py")
            print("Extracting raw compressed payload instead.")
            actual_end = len(data)
            while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
                actual_end -= 1
            with open(output_file, 'wb') as f:
                f.write(data[DATA_FILE_OFFSET:actual_end])
            print(f"Extracted {actual_end - DATA_FILE_OFFSET:,} bytes (compressed) to {output_file}")
    elif type_id in (1, 2, 3, 4, 5, 6):
        actual_end = len(data)
        while actual_end > DATA_FILE_OFFSET and data[actual_end - 1] == 0xE5:
            actual_end -= 1
        with open(output_file, 'wb') as f:
            f.write(data[DATA_FILE_OFFSET:actual_end])
        print(f"Extracted {actual_end - DATA_FILE_OFFSET:,} bytes to {output_file}")
    else:
        print("ERROR: Unknown disc type, cannot extract ROM", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description='Parse and analyze KN5000 system update floppy disc images'
    )
    parser.add_argument('disc_image', help='Path to floppy disc image (1.44MB)')
    parser.add_argument('--extract', metavar='DIR',
                        help='Extract all files to directory')
    parser.add_argument('--extract-rom', metavar='FILE',
                        help='Extract ROM payload (decompressed if SLIDE4K)')
    args = parser.parse_args()

    with open(args.disc_image, 'rb') as f:
        data = f.read()

    if len(data) != FLOPPY_SIZE:
        print(f"WARNING: File size {len(data)} != expected {FLOPPY_SIZE} (1.44MB)",
              file=sys.stderr)

    print_analysis(args.disc_image, data)

    if args.extract:
        print(f"--- Extracting files to {args.extract} ---")
        extract_files(data, args.extract)
        print()

    if args.extract_rom:
        print(f"--- Extracting ROM payload ---")
        extract_rom(data, args.extract_rom)
        print()


if __name__ == '__main__':
    main()
