#!/usr/bin/env python3
"""Decode the challenge's shuffled-alphabet LZW format (standard library only)."""
from pathlib import Path


def alphabet(seed):
    symbols = list(range(256))
    state = seed
    for i in range(255, 0, -1):
        state ^= (state << 13) & 0xFFFFFFFF
        state ^= state >> 17
        state ^= (state << 5) & 0xFFFFFFFF
        state &= 0xFFFFFFFF
        j = state % (i + 1)
        symbols[i], symbols[j] = symbols[j], symbols[i]
    return symbols


def decompress(data, seed=0x0745B6):
    symbols = alphabet(seed)
    table = {i: bytes([symbol]) for i, symbol in enumerate(symbols)}
    width, next_code, bit_position = 10, 258, 0
    previous = None
    bits = int.from_bytes(data, "little")
    output = bytearray()
    while bit_position + width <= len(data) * 8:
        code = (bits >> bit_position) & ((1 << width) - 1)
        bit_position += width
        if code == 256:
            table = {i: bytes([symbol]) for i, symbol in enumerate(symbols)}
            width, next_code, previous = 10, 258, None
            continue
        if code == 257:
            return bytes(output)
        if code in table:
            word = table[code]
        elif code == next_code and previous is not None:
            word = previous + previous[:1]
        else:
            raise ValueError(f"Invalid LZW code {code} at bit {bit_position}")
        output.extend(word)
        if previous is not None:
            table[next_code] = previous + word[:1]
            next_code += 1
            if next_code == 1 << width:
                width += 1
        previous = word
    raise ValueError("Missing end code")


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    assert decompress((root / "sample.lzw").read_bytes()) == (root / "sample.txt").read_bytes()
    print("Sample: exact match")
    body = decompress((root / "flag.lzw").read_bytes()).decode("ascii")
    print("cruXipher{" + body + "}")
