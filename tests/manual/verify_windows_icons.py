"""Compare built EXE icon resources with every frame in the brand ICO.

Run on Windows after packaging, using the build dependency group.
"""
import argparse
from pathlib import Path
import struct
import sys


def expected_frames(path):
    data = path.read_bytes()
    reserved, kind, count = struct.unpack_from("<HHH", data)
    if reserved or kind != 1 or count == 0:
        raise ValueError(f"Invalid ICO: {path}")
    frames = {}
    for index in range(count):
        width, height, _, _, _, _, size, offset = struct.unpack_from("<BBBBHHII", data, 6 + 16 * index)
        frames[(width or 256, height or 256)] = data[offset:offset + size]
    return frames


def verify(executable, expected):
    from PyInstaller.compat import win32api

    module = win32api.LoadLibraryEx(str(executable.resolve()), 0, 2)
    try:
        for group in win32api.EnumResourceNames(module, 14):
            data = win32api.LoadResource(module, 14, group)
            frames = {}
            for index in range(struct.unpack_from("<H", data, 4)[0]):
                width, height, _, _, _, _, _, resource_id = struct.unpack_from("<BBBBHHIH", data, 6 + 14 * index)
                frames[(width or 256, height or 256)] = win32api.LoadResource(module, 3, resource_id)
            if frames == expected:
                print(f"PASS: {executable.name} embeds all {len(frames)} brand icon frames")
                return
        raise ValueError(f"Brand icon resources differ from ICO: {executable}")
    finally:
        win32api.FreeLibrary(module)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--icon", type=Path, required=True)
    parser.add_argument("executables", type=Path, nargs="+")
    args = parser.parse_args()
    if sys.platform != "win32":
        parser.error("EXE resource verification requires Windows")
    frames = expected_frames(args.icon)
    for executable in args.executables:
        verify(executable, frames)


if __name__ == "__main__":
    main()
