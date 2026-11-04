#!/usr/bin/env python3
"""Run the upstream fixgpt sequence on disposable 4K-sector loop disks only."""

import hashlib
from pathlib import Path
import struct
import subprocess
import sys
import tempfile
import uuid
import zlib


SECTOR = 4096
LAST = 4095
COMMANDS = "x\nj\n\nk\n\nw\nY\n"


def header(current, alternate, first, last, disk_guid, table, count, entries):
    data = bytearray(SECTOR)
    struct.pack_into("<8sIIIIQQQQ16sQIII", data, 0, b"EFI PART", 0x10000,
                     92, 0, 0, current, alternate, first, last, disk_guid,
                     table, count, 128, zlib.crc32(entries))
    struct.pack_into("<I", data, 16, zlib.crc32(data[:92]))
    return data


def check_header(data, offset):
    hdr = bytearray(data[offset:offset + 92])
    assert hdr[:8] == b"EFI PART"
    expected = struct.unpack_from("<I", hdr, 16)[0]
    struct.pack_into("<I", hdr, 16, 0)
    assert zlib.crc32(hdr) == expected, "header CRC mismatch"
    table, count, size, crc = struct.unpack_from("<QIII", hdr, 72)
    entries = data[table * SECTOR:table * SECTOR + count * size]
    assert zlib.crc32(entries) == crc, "entry-array CRC mismatch"
    return hdr, entries


def verify(gdisk, directory, lun, count, old_backup):
    # Counts, FirstUsableLBA and tail gaps match the supplied piano backups.
    sectors = (count * 128 + SECTOR - 1) // SECTOR
    old_last = old_backup - 1
    disk_guid = uuid.UUID(int=lun + 1).bytes_le
    entries = bytearray(count * 128)
    for index, start, end, name in [(0, 6, 100, "piano-first"),
                                    (1, 128, old_last, "piano-last")]:
        struct.pack_into("<16s16sQQQ", entries, index * 128,
                         uuid.UUID("0fc63daf-8483-4772-8e79-3d69d8477de4").bytes_le,
                         uuid.UUID(int=100 + lun * 2 + index).bytes_le,
                         start, end, 0)
        label = name.encode("utf-16le")
        entries[index * 128 + 56:index * 128 + 56 + len(label)] = label
    image = directory / f"lun{lun}.img"
    with image.open("w+b") as disk:
        disk.truncate((LAST + 1) * SECTOR)
        mbr = bytearray(SECTOR)
        mbr[450] = 0xEE
        struct.pack_into("<II", mbr, 454, 1, LAST)
        mbr[510:512] = b"\x55\xaa"
        disk.write(mbr)
        for lba, payload in [(1, header(1, LAST, 6, old_last, disk_guid, 2, count, entries)),
                             (2, entries), (old_backup, entries),
                             (LAST, header(LAST, 1, 6, old_last, disk_guid, old_backup, count, entries)),
                             (6, b"FIRST PARTITION CANARY"),
                             (old_last, b"LAST PARTITION CANARY")]:
            disk.seek(lba * SECTOR)
            disk.write(payload)
    before = image.read_bytes()
    loop = subprocess.check_output(["losetup", "--find", "--show", "--sector-size",
                                    str(SECTOR), str(image)], text=True).strip()
    try:
        previous = None
        for attempt in range(2):
            result = subprocess.run([gdisk, loop], input=COMMANDS, text=True,
                                    stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=30)
            assert result.returncode == 0, result.stdout
            assert "The operation has completed successfully." in result.stdout, result.stdout
            after = image.read_bytes()
            primary, primary_entries = check_header(after, SECTOR)
            backup, backup_entries = check_header(after, LAST * SECTOR)
            assert primary_entries == backup_entries == entries, "partition entries changed"
            assert primary[56:72] == backup[56:72] == disk_guid
            assert struct.unpack_from("<QQ", primary, 40) == (2 + sectors, LAST - sectors - 1)
            assert struct.unpack_from("<Q", backup, 72)[0] == LAST - sectors
            assert before[6 * SECTOR:(old_last + 1) * SECTOR] == after[6 * SECTOR:(old_last + 1) * SECTOR], "partition payload changed"
            digest = hashlib.sha256(after).digest()
            if attempt:
                assert digest == previous, "second run was not idempotent"
            previous = digest
        print(f"PASS LUN{lun}: {count} entries, valid primary/backup CRCs, entries and payload preserved, idempotent")
    finally:
        subprocess.run(["losetup", "--detach", loop], check=True)


if __name__ == "__main__":
    gdisk = str(Path(sys.argv[1]).resolve())
    with tempfile.TemporaryDirectory(prefix="piano-fixgpt-") as temporary:
        for lun, count in enumerate([64, 32, 32, 32, 96, 32]):
            verify(gdisk, Path(temporary), lun, count, LAST - (6 if lun == 4 else 4))
