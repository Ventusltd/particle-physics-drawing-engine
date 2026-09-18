"""png.py: the smallest PNG writer, no dependencies. 8-bit greyscale. Black ground, particles are light."""
import struct, zlib


def _chunk(tag, data):
    c = struct.pack(">I", len(data)) + tag + data
    return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)


def write_grey(path, width, height, pixels):
    """pixels: bytes or list of ints 0..255, row-major, len == width*height."""
    raw = bytearray()
    for y in range(height):
        raw.append(0)
        raw += bytes(pixels[y * width:(y + 1) * width])
    with open(path, "wb") as f:
        f.write(b"\x89PNG\r\n\x1a\n")
        f.write(_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 0, 0, 0, 0)))
        f.write(_chunk(b"IDAT", zlib.compress(bytes(raw), 9)))
        f.write(_chunk(b"IEND", b""))


def raster_to_png(path, size, counts, gamma=0.5):
    """Density raster (counts per cell) to PNG; gamma < 1 lifts sparse cells so a lone particle is visible."""
    peak = max(counts) or 1
    px = bytes(int(255 * (c / peak) ** gamma) if c else 0 for c in counts)
    write_grey(path, size, size, px)
