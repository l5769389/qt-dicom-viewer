"""Small stored RAR4 writer for synthetic DICOM and malformed-archive tests.

Only test data is written; actual compressed RAR4/5 reference archives live in
fixtures/rar. Header layout follows RAR's published technote / CRC rules.
"""

import stat
import struct
import zlib


def header(kind, flags, payload=b""):
    block = struct.pack("<BHH", kind, flags, len(payload) + 7) + payload
    return struct.pack("<H", zlib.crc32(block) & 0xFFFF) + block


def stored_rar(path, entries, *, volume=False, corrupt_crc=False):
    data = bytearray(b"Rar!\x1a\x07\x00" + header(0x73, int(volume), b"\0" * 6))
    for entry in entries:
        name, content, *attributes = entry
        mode = attributes[0] if attributes else stat.S_IFREG | 0o644
        directory = stat.S_ISDIR(mode)
        flags = 0x8000 | (0xE0 if directory else 0)
        if name.isascii():
            filename = name.encode("ascii")
        else:
            # Encode full UTF-16 code units using the RAR4 Unicode "10" form.
            encoded = name.encode("utf-16le")
            unicode_name = bytearray(b"\0")
            for start in range(0, len(encoded), 8):
                unicode_name += b"\xaa" + encoded[start : start + 8]
            filename = name.encode("utf-8") + b"\0" + unicode_name
            flags |= 0x200
        checksum = zlib.crc32(content) ^ int(corrupt_crc)
        body = (
            struct.pack(
                "<IIBIIBBHI",
                len(content),
                len(content),
                3,
                checksum,
                0,
                20,
                0x30,
                len(filename),
                mode,
            )
            + filename
        )
        data += header(0x74, flags, body) + content
    data += header(0x7B, 0)
    path.write_bytes(data)
    return path
