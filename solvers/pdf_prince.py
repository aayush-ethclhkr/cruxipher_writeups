#!/usr/bin/env python3
"""Recover the old content stream and decode it through GhostMono's glyphs."""
from pathlib import Path
import re
import struct
import zlib


def object_streams(pdf, number):
    pattern = rb"\b" + str(number).encode() + rb" 0 obj\s*<<(.*?)>>\s*stream\r?\n(.*?)\r?\nendstream"
    for match in re.finditer(pattern, pdf, re.S):
        dictionary, stream = match.groups()
        yield zlib.decompress(stream) if b"/FlateDecode" in dictionary else stream


def font_cmap(font):
    # Parse this font's TrueType format-4 cmap, including idRangeOffset entries.
    count = struct.unpack_from(">H", font, 4)[0]
    tables = {}
    for index in range(count):
        tag, _, offset, length = struct.unpack_from(">4sIII", font, 12 + 16 * index)
        tables[tag] = (offset, length)
    base, _ = tables[b"cmap"]
    subtables = struct.unpack_from(">H", font, base + 2)[0]
    for index in range(subtables):
        _, _, relative = struct.unpack_from(">HHI", font, base + 4 + 8 * index)
        offset = base + relative
        if struct.unpack_from(">H", font, offset)[0] == 4:
            break
    else:
        raise ValueError("No format-4 cmap")
    segments = struct.unpack_from(">H", font, offset + 6)[0] // 2
    end_base = offset + 14
    start_base = end_base + 2 * segments + 2
    delta_base = start_base + 2 * segments
    range_base = delta_base + 2 * segments
    result = {}
    for index in range(segments):
        end = struct.unpack_from(">H", font, end_base + 2 * index)[0]
        start = struct.unpack_from(">H", font, start_base + 2 * index)[0]
        delta = struct.unpack_from(">h", font, delta_base + 2 * index)[0]
        range_offset = struct.unpack_from(">H", font, range_base + 2 * index)[0]
        for codepoint in range(start, min(end, 0xFFFE) + 1):
            if range_offset:
                address = range_base + 2 * index + range_offset + 2 * (codepoint - start)
                glyph = struct.unpack_from(">H", font, address)[0]
                if glyph:
                    glyph = (glyph + delta) & 0xFFFF
            else:
                glyph = (codepoint + delta) & 0xFFFF
            if glyph:
                result[chr(codepoint)] = glyph
    return result


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    pdf = (root / "chall.pdf").read_bytes()
    revisions = list(object_streams(pdf, 4))
    key = re.search(rb"\(key = ([^)]+)\)", revisions[-1]).group(1)
    encoded = bytes.fromhex(re.search(rb"<([0-9A-F]+)> Tj", revisions[0]).group(1).decode())
    markers, ciphertext = encoded[::2], encoded[1::2]
    even_then_odd = key[::2] + key[1::2]
    assert markers == (even_then_odd * (len(markers) // len(key) + 1))[:len(markers)]
    xor_key = key[1::2] + key[::2]
    glyph_ids = [value ^ xor_key[index % len(xor_key)] for index, value in enumerate(ciphertext)]
    font = next(object_streams(pdf, 8))
    cmap = font_cmap(font)
    symbols = sorted(cmap)
    # Verified by rendering the font: cmap labels are one character behind
    # the actual glyph outlines in this cyclic, sorted alphabet.
    actual_glyphs = {cmap[label]: symbols[(index + 1) % len(symbols)]
                     for index, label in enumerate(symbols)}
    print("Hidden layer key:", key.decode())
    print("Glyph IDs:", glyph_ids)
    print("".join(actual_glyphs[glyph] for glyph in glyph_ids))
