#!/usr/bin/env python3
"""Generate a full-bleed, opaque 1024px Nightwell Studio icon using only stdlib.

No external images, fonts or native graphics APIs are required on the macOS runner.
The PNG encoder writes canonical RGB scanlines and CRC-checked chunks.
"""
import math
import struct
import sys
import zlib
from pathlib import Path

SIZE = 1024
OUT = Path(sys.argv[1])

FACETS = [
    ([(275, 236), (390, 336), (390, 700), (275, 813)], .80),
    ([(642, 330), (758, 232), (758, 804), (642, 706)], .77),
    ([(304, 246), (410, 314), (744, 720), (744, 867), (320, 396)], 1.0),
]


def inside(px, py, vertices):
    result = False
    j = len(vertices) - 1
    for i, (xi, yi) in enumerate(vertices):
        xj, yj = vertices[j]
        if (yi > py) != (yj > py) and px < ((xj - xi) * (py - yi) / (yj - yi) + xi):
            result = not result
        j = i
    return result


def chunk(name, body):
    return (struct.pack(">I", len(body)) + name + body
            + struct.pack(">I", zlib.crc32(name + body) & 0xffffffff))


OUT.parent.mkdir(parents=True, exist_ok=True)
compressor = zlib.compressobj(6)
data = bytearray()
with OUT.open("wb") as output:
    output.write(b"\x89PNG\r\n\x1a\n")
    output.write(chunk(b"IHDR", struct.pack(">IIBBBBB", SIZE, SIZE, 8, 2, 0, 0, 0)))
    for y in range(SIZE):
        row = bytearray([0])
        for x in range(SIZE):
            top = max(0.0, 1.0 - math.hypot(x - 70, y - 90) / 900.0)
            bottom = max(0.0, 1.0 - math.hypot(x - 955, y - 960) / 850.0)
            light = 7.0 + 9.0 * top + 11.0 * bottom
            rgb = [light * .90, light * .99, light * 1.17]
            for polygon, brightness in FACETS:
                if inside(x, y, polygon):
                    variation = min(1.0, .28 + .58 * ((SIZE - y) / SIZE) + .25 * (x / SIZE))
                    silver = 95 + 158 * variation * brightness
                    rgb = [silver, silver * 1.008, silver * 1.037]
            diagonal = abs((y - 246) - 1.14 * (x - 304))
            if 306 < x < 739 and diagonal < 1.8:
                rgb = [220, 231, 251]
            row.extend(max(0, min(255, int(v))) for v in rgb)
        data.extend(compressor.compress(row))
    data.extend(compressor.flush())
    output.write(chunk(b"IDAT", bytes(data)))
    output.write(chunk(b"IEND", b""))
print(f"AppIcon: {SIZE}x{SIZE}, {OUT.stat().st_size} bytes")
