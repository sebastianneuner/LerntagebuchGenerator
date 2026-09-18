"""Hilfsfunktionen fuer die Tests."""

import struct
import zlib


def make_png(width, height, rgba=(0, 0, 255, 255)):
    """Einfarbiges PNG erzeugen, ohne Zusatzpakete wie Pillow."""
    def chunk(tag, data):
        return (struct.pack(">I", len(data)) + tag + data
                + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF))
    pixel = bytes(rgba)
    raw = b"".join(b"\x00" + pixel * width for _ in range(height))
    return (b"\x89PNG\r\n\x1a\n"
            + chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 6, 0, 0, 0))
            + chunk(b"IDAT", zlib.compress(raw))
            + chunk(b"IEND", b""))
