#!/usr/bin/env python3
"""
repack_bootimg.py - Android Boot Image Assembler for LeEco Le 2 (Helio X20 / MT6797)
Compliant with standard Android AOSP boot_img_hdr format (v0).
"""

import sys
import os
import gzip
import struct
import hashlib

PAGE_SIZE = 2048
BASE_ADDR = 0x40078000
KERNEL_OFFSET = 0x00008000     # Load: 0x40080000
RAMDISK_OFFSET = 0x04f88000    # Load: 0x45000000
SECOND_OFFSET = 0x00e88000     # Load: 0x40f00000
TAGS_OFFSET = 0x03f88000       # Load: 0x44000000
CMDLINE = b"bootopt=64S3,32N2,64N2 buildvariant=userdebug"
BOARD_NAME = b"2   1489686749  "

def pad_data(data, page_size=PAGE_SIZE):
    remainder = len(data) % page_size
    if remainder > 0:
        return data + b"\x00" * (page_size - remainder)
    return data

def build_boot_img(kernel_path, dtb_path, ramdisk_path, output_path):
    print(f"[*] Reading kernel from: {kernel_path}")
    with open(kernel_path, "rb") as f:
        kdata = f.read()

    # If raw Image, compress to gzip
    if not (kdata[:2] == b"\x1f\x8b"):
        print(f"[*] Raw Image detected ({len(kdata)} bytes), compressing with gzip -9...")
        import io
        buf = io.BytesIO()
        # Use mtime=0 for deterministic reproducibility
        with gzip.GzipFile(fileobj=buf, mode="wb", compresslevel=9, mtime=0) as gz:
            gz.write(kdata)
        kdata_gz = buf.getvalue()
        print(f"[*] Compressed kernel size: {len(kdata_gz)} bytes")
    else:
        kdata_gz = kdata
        print(f"[*] Pre-compressed Image.gz detected: {len(kdata_gz)} bytes")

    # Append DTB
    if dtb_path and os.path.exists(dtb_path):
        print(f"[*] Appending DTB from: {dtb_path}")
        with open(dtb_path, "rb") as f:
            dtb_data = f.read()
        kernel_blob = kdata_gz + dtb_data
        print(f"[*] Kernel blob (Image.gz + DTB) size: {len(kernel_blob)} bytes")
    else:
        kernel_blob = kdata_gz

    # Read Ramdisk
    print(f"[*] Reading ramdisk from: {ramdisk_path}")
    with open(ramdisk_path, "rb") as f:
        ramdisk_data = f.read()

    # Calculate SHA1 ID
    sha = hashlib.sha1()
    sha.update(kernel_blob)
    sha.update(struct.pack("<I", len(kernel_blob)))
    sha.update(ramdisk_data)
    sha.update(struct.pack("<I", len(ramdisk_data)))
    sha.update(b"") # second size = 0
    sha.update(struct.pack("<I", 0))
    id_bytes = sha.digest() + b"\x00" * (32 - len(sha.digest()))

    # Build Header (2048 bytes)
    header = bytearray(PAGE_SIZE)
    header[:8] = b"ANDROID!"
    
    struct.pack_into(
        "<IIIIIIIII",
        header, 8,
        len(kernel_blob), BASE_ADDR + KERNEL_OFFSET,
        len(ramdisk_data), BASE_ADDR + RAMDISK_OFFSET,
        0, BASE_ADDR + SECOND_OFFSET,
        BASE_ADDR + TAGS_OFFSET,
        PAGE_SIZE,
        0 # unused
    )

    header[44:44+len(BOARD_NAME)] = BOARD_NAME
    header[64:64+len(CMDLINE)] = CMDLINE
    header[576:576+32] = id_bytes

    # Assemble full boot image with page padding
    full_img = bytes(header) + pad_data(kernel_blob) + pad_data(ramdisk_data)

    print(f"[*] Writing boot image to: {output_path} ({len(full_img)} bytes)")
    with open(output_path, "wb") as f:
        f.write(full_img)

    print(f"[+] Successfully generated boot image: {output_path}")
    return output_path

if __name__ == "__main__":
    if len(sys.argv) < 5:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        default_analysis_dir = os.path.join(os.path.dirname(base_dir), "boot_analysis")
        k = os.path.join(default_analysis_dir, "Image")
        d = os.path.join(default_analysis_dir, "le_x620.dtb")
        r = os.path.join(default_analysis_dir, "ramdisk.cpio.gz")
        out = os.path.join(base_dir, "boot_test.img")
        print(f"Usage: python repack_bootimg.py <kernel_Image> <dtb> <ramdisk.cpio.gz> <output_boot.img>")
        print(f"Running self-test with workspace files...")
        build_boot_img(k, d, r, out)
    else:
        build_boot_img(sys.argv[1], sys.argv[2], sys.argv[3], sys.argv[4])

