#!/usr/bin/env python3
"""Recover the saved terminal line and undo Dvorak key mapping."""
from pathlib import Path
import re
import struct


def server_bytes(path):
    segments = {}
    with path.open("rb") as capture:
        header = capture.read(24)
        assert header[:4] == b"\xd4\xc3\xb2\xa1", "Expected little-endian pcap"
        assert struct.unpack_from("<I", header, 20)[0] == 0, "Expected DLT_NULL"
        while packet_header := capture.read(16):
            _, _, length, _ = struct.unpack("<IIII", packet_header)
            ip = capture.read(length)[4:]
            if not ip or ip[0] >> 4 != 4 or ip[9] != 6:
                continue
            ip_length = struct.unpack_from("!H", ip, 2)[0]
            tcp = ip[(ip[0] & 15) * 4:ip_length]
            source, _, sequence = struct.unpack_from("!HHI", tcp)
            payload = tcp[(tcp[12] >> 4) * 4:]
            if source == 9999 and payload:
                segments.setdefault(sequence, payload)
    return b"".join(segments[key] for key in sorted(segments))


def terminal_line(data):
    # Minimal terminal replay for the controls used by this capture.
    text = data.decode("utf-8", errors="replace")
    text = re.sub(r"\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)", "", text)
    text = re.sub(r"\x1bP.*?\x1b\\", "", text, flags=re.S)
    tokens = re.compile(r"\x1b\[([0-?]*)([ -/]*)([@-~])|\x1b[()][^\n]|\x1b.|.", re.S)
    screen = [[" "] * 160 for _ in range(40)]
    row = col = 0
    for match in tokens.finditer(text):
        token = match.group(0)
        if match.group(1) is not None:
            raw, _, command = match.groups()
            if raw.startswith(("?", ">", "<", "=")):
                continue
            values = [int(v) if v.isdigit() else 0 for v in raw.split(";")]
            amount = values[0] or 1
            if command in ("H", "f"):
                row = (values[0] or 1) - 1
                col = ((values[1] if len(values) > 1 else 1) or 1) - 1
            elif command == "A":
                row = max(0, row - amount)
            elif command == "B":
                row += amount
            elif command == "C":
                col += amount
            elif command == "D":
                col = max(0, col - amount)
            elif command == "J" and values[0] in (2, 3):
                screen = [[" "] * 160 for _ in range(40)]
            elif command == "K":
                if values[0] == 0:
                    screen[row][col:] = [" "] * (160 - col)
                elif values[0] == 2:
                    screen[row] = [" "] * 160
            continue
        if token.startswith("\x1b"):
            continue
        if token == "\r":
            col = 0
        elif token == "\n":
            row += 1
        elif token == "\b":
            col = max(0, col - 1)
        elif ord(token) >= 32 and 0 <= row < 40 and 0 <= col < 160:
            screen[row][col] = token
            col += 1
    return "".join(screen[0]).rstrip()


def undo_dvorak(text):
    qwerty = "`1234567890-=qwertyuiop[]\\asdfghjkl;'zxcvbnm,./"
    dvorak = "`1234567890[]',.pyfgcrl/=\\aoeuidhtns-;qjkxbmwvz"
    qwerty_shift = '~!@#$%^&*()_+QWERTYUIOP{}|ASDFGHJKL:"ZXCVBNM<>?'
    dvorak_shift = '~!@#$%^&*(){}"<>PYFGCRL?+|AOEUIDHTNS_:QJKXBMWVZ'
    mapping = dict(zip(dvorak + dvorak_shift, qwerty + qwerty_shift))
    return "".join(mapping.get(character, character) for character in text)


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[2]
    raw = terminal_line(server_bytes(root / "secret.pcap"))
    print("Saved line:", raw)
    print(undo_dvorak(raw))
