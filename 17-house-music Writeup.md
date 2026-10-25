# cruXipher — "Someone had the bright idea of writing their own compressor, and then they forgot how it works"

**Category:** Forensics / Reverse Engineering (custom compression)
**Flag:** `cruXipher{m3ss3d_up_compXsion}`

---

## 1. Summary

The challenge ships a custom LZW-style container (`flag.lzw`) plus a known-plaintext pair
(`sample.txt` ⇄ `sample.lzw`) and a red-herring PDF memo (`chall.pdf`).

The codec is a LZW variant with four deviations from the textbook version:

| # | Deviation | Detail |
|---|-----------|--------|
| 1 | **Shuffled literal table** | The 256 byte values are not at their own code; the table is shuffled per tape with a seeded PRNG. |
| 2 | **Reserved control codes** | Codes `0–255` = literals, `256` = RESET, `257` = END, dynamic entries start at `258`. |
| 3 | **Wide start** | Codes are **10 bits** wide from the beginning (not 9), because the "vault ledger grew". |
| 4 | **Width growth** | The width steps to **11 bits** once the dictionary reaches 1024 entries. |

Everything needed to rebuild the table — *the shuffle algorithm, the PRNG, the PRNG variant and
the seed* — is described in prose inside the "ARCHIVE OFFICE BULLETIN" section of `sample.txt`.
The PDF is a trap; the bulletin is the spec.

---

## 2. Files provided

| File | Size | Role |
|------|------|------|
| `flag.lzw` | 27 B | The target container (21 codes) |
| `sample.txt` | 2323 B | Known plaintext — **contains the codec spec in prose** |
| `sample.lzw` | 1453 B | Known plaintext compressed with the same codec/key (1126 codes) |
| `chall.pdf` | — | **Decoy** (see §3) |

---

## 3. The decoy: `chall.pdf`

A PDF was attached for flavour. It contains:

* a memo body written in **ROT13** ("…just a routine update to the archive procedures…");
* an invisible **OCG (optional content group)** layer literally named *keyring*, holding
  `key = L7-b5acb9c6` and `flag = flag{nice_grep_but_not_the_flag}`;
* a hidden trailer string `ctf{copy_paste_is_a_trap}`.

None of these are the flag. Using the PDF key as the PRNG seed (`0xb5acb9c6` / `0x7b5acb9c6`)
produces pure non-ASCII garbage — the PDF key is a deliberate lure. **The real key is in
`sample.txt`.** ("Do not ask the vault clerks about the details; the clerks only keep the keys,
not the codec." — the *keys* are in the bulletin, the *codec* had to be reverse-engineered.)

---

## 4. Phase 1 — the container format (no key needed)

Bit-level analysis of the two `.lzw` files:

1. Both files start with the byte `0x00`. Sweeping every candidate code width against the
   known plaintext showed a **fixed 10-bit, LSB-first** code stream is the only hypothesis that
   decodes `sample.lzw` into `sample.txt` for the first ~768 codes.
2. The first code is `256` and the last is `257` — matching the bulletin's
   *"a leading reset code, then data codes, then an end code"*, with the control codes
   occupying the first two slots *after* the 256 literals.
3. Bits are packed **from the low end of each byte** (*"packs the bits from the low end of
   each byte"*), i.e. code *k*'s bit *b* is bit `b` of the current byte position.

At this point the stream is structure-perfect but the **symbols are scrambled**, because code
`k` no longer maps to byte `k`.

### Side note: the width growth trap

Naively decoding all 1126 codes of `sample.lzw` as 10-bit gives correct output for the first
768 codes and then garbage — which looks exactly like a corrupted dictionary. The real cause is
that the width steps up mid-stream. Brute-forcing the switch point confirms a **unique**
solution:

```
switch index = 767   →   codes[0..767] are 10 bits, codes[768..] are 11 bits
```

That is precisely standard LZW width-growth semantics: the dictionary holds
`256 literals + 2 control codes + 766 dynamic entries = 1024` entries after the 768th code,
so the next code no longer fits in 10 bits (2¹⁰ = 1024) and needs 11.

Sanity check on the byte budget for `sample.lzw`:
`768 × 10 + 358 × 11 = 11 618 bits → 1453 bytes` ✓ (exactly the file size).

---

## 5. Phase 2 — the real spec, hidden in `sample.txt`

The third paragraph of `sample.txt` is the spec, written as an office bulletin:

> "The table is reshuffled **Fisher-Yates style, walking down from the last slot**, and the random
> numbers come from a **small xorshift-family generator**. The generator is seeded with the
> **index key printed in the tape log**. For this tape the index key is, in hex: **0745B6**."

> "The codec writes a leading **reset** code, then data codes, then an **end** code, and packs
> the bits from the low end of each byte. **Code widths start out wider** than the older codec
> did, because the vault ledger grew; the width grows again as the table fills. **The first slots
> of the table are reserved for the control codes**, so literal symbols are not the first thing in
> the table any more."

Decoding the hints:

| Hint | Interpretation |
|------|----------------|
| "reshuffled Fisher-Yates style" | a shuffle of `list(range(256))` |
| "walking down from the last slot" | the loop runs **i = 255 → 1** (not the textbook 0 → 255) |
| "small xorshift-family generator" | a 32-bit xorshift: `x^=x<<13; x^=x>>17; x^=x<<5` |
| "index key … in hex: 0745B6" | seed = `0x0745B6` |
| "the first slots … reserved for the control codes" | 256 literals, then `256`=RESET, `257`=END, dynamic from `258` |
| "widths start out wider" | 10-bit start (not 9) |

Nice touch: the seed `0745B6` is literally spelled out in the story — the tape was found
"**By 07:45**" and moved to shelf "**[B-6]**" → `07 45 B 6`.

---

## 6. Phase 3 — recovering the symbol table

Two independent routes were used and cross-checked.

### Route A — brute-force the xorshift variant

With the seed and the algorithm family known, the only unknowns are the three shift amounts
(and the direction of the shuffle). Brute-forcing all xorshift32 variants gives a unique hit:

```
x ^= (x << 13) & 0xFFFFFFFF
x ^= x >> 17
x ^= (x <<  5) & 0xFFFFFFFF
```

with the shuffle walking **down**:

```python
t = list(range(256))
for i in range(255, 0, -1):        # down from the last slot
    j = next() % (i + 1)
    t[i], t[j] = t[j], t[i]
```

### Route B — known-plaintext (no key required)

As a cross-check, the literal table can be recovered *without* the key: the first 768 codes
decode structurally (the dictionary is irrelevant for literal-only codes), and since
`sample.txt` is known, each literal code can be mapped to the character that appears in that
position. This yields 69 mappings (the number of distinct characters in `sample.txt`),
including two late discoveries that pin down the width-growth behaviour:

* code `253` → `'D'` (first occurrence at byte 1590),
* code `50` → `'P'` (first occurrence at byte 1684).

The key-derived table reproduces **all 69** mappings exactly — the two routes agree.

The permutation has **no fixed points** (`table[i] != i` for every `i`), i.e. it is a genuine
shuffle, not an affine/identity-ish transform — which is also why no `random.shuffle`,
`random.sample`, RC4, LCG or GF(2)-affine shortcut ever matched.

### Recovered table (code → byte), first 64 entries

```
code :  0    1    2    3    4    5    6    7    8    9   10   11   12   13   14   15
byte : 0x1e 0xee 0x21 0x6f 0x2f 0x62 0x3b 0x16 0x95 0xed 0xe7 0x11 0xf3 0x79 0x8e 0x4a
```

---

## 7. The full codec specification (recovered)

### Table layout

| Codes | Meaning |
|-------|---------|
| `0 – 255` | Literals, value = `table[code]` (shuffled) |
| `256` | RESET — clears the dynamic dictionary, next free code = 258, clears "previous" |
| `257` | END — terminates the stream |
| `258 – 1023` | Dynamic dictionary entries (LZW strings), assigned sequentially |
| `1024+` | Would require 11-bit codes |

### Stream format

```
[RESET 256] [data code] [data code] ... [END 257]
```

* Codes are packed **LSB-first** into the byte stream; the first code occupies bits 0–9 of
  byte 0, the second bits 10–19 (spilling into byte 1), etc.
* Width is **10 bits** initially and becomes **11 bits** once the dictionary would hold 1024
  entries. In `sample.lzw` the switch happens at code index **767** (i.e. the 768th code is the
  last 10-bit one).
* The END code is written with the width in force at that point (10-bit for `flag.lzw`,
  11-bit for `sample.lzw`).

### Decoder

```
prev = None ; next_free = 258
for code in stream:
    if code == RESET: reset dictionary; next_free = 258; prev = None; continue
    if code == END:   stop
    if code < 258:            entry = bytes([table[code]])          # literal
    elif code == next_free:   entry = prev + prev[:1]                # the KwKwK case
    else:                     entry = dictionary[code]
    emit(entry)
    if prev is not None: dictionary[next_free] = prev + entry[:1]; next_free += 1
    prev = entry
```

### Encoder (inverse)

Standard LZW match search over the *inverted* table (`byte → code`), with the same width
schedule, wrapped in RESET/END.

---

## 8. The solver

`solve_lzw.py` (standalone, no dependencies):

```python
#!/usr/bin/env python3
"""cruXipher - 'lost the compressor' solver."""
import sys

MASK = 0xFFFFFFFF
KEY = int("0745B6", 16)          # index key from the vault bulletin
CLEAR, EOI = 256, 257
W0, W1, SWITCH_AT = 10, 11, 767  # code widths / where the width grows


def make_table(seed=KEY):
    """Shuffled literal table: table[code] -> byte value."""
    x = seed & MASK

    def nxt():
        nonlocal x
        x ^= (x << 13) & MASK
        x &= MASK
        x ^= x >> 17
        x ^= (x << 5) & MASK
        x &= MASK
        return x

    t = list(range(256))
    for i in range(255, 0, -1):          # walk down from the last slot
        j = nxt() % (i + 1)
        t[i], t[j] = t[j], t[i]
    return t


def read_codes(data):
    bits = []
    for byte in data:
        bits.extend((byte >> i) & 1 for i in range(8))
    codes, i, width = [], 0, W0
    while i + width <= len(bits):
        v = 0
        for k in range(width):
            v |= bits[i + k] << k
        codes.append(v)
        i += width
        if len(codes) - 1 >= SWITCH_AT:
            width = W1
    return codes


def decode(data, table):
    codes = read_codes(data)
    d = [bytes([table[c]]) for c in range(256)] + [b"\x00", b"\x00"]
    nxt, out, prev = 258, bytearray(), None
    for c in codes:
        if c == CLEAR:
            d = [bytes([table[k]]) for k in range(256)] + [b"\x00", b"\x00"]
            nxt, prev = 258, None
            continue
        if c == EOI:
            break
        if c < len(d) and d[c]:
            entry = d[c]
        elif prev is not None and c == nxt:
            entry = prev + prev[:1]
        else:
            raise ValueError(f"invalid code {c}")
        out += entry
        if prev is not None:
            d.append(prev + entry[:1])
            nxt += 1
        prev = entry
    return bytes(out)


def encode(text, table):
    d = {bytes([table[c]]): c for c in range(256)}
    nxt, codes, w = 258, [], b""
    for ch in text:
        c = bytes([ch])
        wc = w + c
        if wc in d:
            w = wc
        else:
            codes.append(d[w])
            d[wc] = nxt
            nxt += 1
            w = c
    if w:
        codes.append(d[w])
    bits = [(CLEAR >> k) & 1 for k in range(W0)]
    for i, c in enumerate(codes):
        width = W0 if i < SWITCH_AT else W1
        bits += [(c >> k) & 1 for k in range(width)]
    # the end code is emitted with whatever width the stream has reached
    bits += [(EOI >> k) & 1 for k in range(W0 if len(codes) <= SWITCH_AT else W1)]
    out = bytearray()
    for i in range(0, len(bits), 8):
        chunk = bits[i:i + 8]
        chunk += [0] * (8 - len(chunk))
        out.append(sum(b << j for j, b in enumerate(chunk)))
    return bytes(out)


def main():
    table = make_table()
    files = sys.argv[1:] or ["flag.lzw", "sample.lzw"]
    for path in files:
        try:
            raw = open(path, "rb").read()
        except OSError as e:
            print(f"{path}: {e}")
            continue
        plain = decode(raw, table)
        roundtrip = encode(plain, table) == raw
        print(f"{path}: {len(raw)} bytes -> {len(plain)} chars  (round-trip exact: {roundtrip})")
        print(f"   {plain.decode('latin1')}")


if __name__ == "__main__":
    main()
```

Usage:

```
$ python3 solve_lzw.py flag.lzw sample.lzw
flag.lzw: 27 bytes -> 19 chars  (round-trip exact: True)
   m3ss3d_up_compXsion
sample.lzw: 1453 bytes -> 2323 chars  (round-trip exact: True)
   Agent Z lost a backup tape of the server log ...
```

---

## 9. Verification

| Test | Result |
|------|--------|
| `decode(sample.lzw)` vs `sample.txt` | **byte-identical** (2323 / 2323 bytes) |
| `encode(decode(sample.lzw))` vs `sample.lzw` | **byte-identical** (1453 / 1453 bytes) |
| `encode(decode(flag.lzw))` vs `flag.lzw` | **byte-identical** (27 / 27 bytes) |
| Key-derived table vs known-plaintext table | 69 / 69 mappings agree |
| Width-switch point | uniquely 767 (brute-forced 700–819) |

`flag.lzw` in full (27 bytes), which decodes to the 19 characters `m3ss3d_up_compXsion`:

```
0000  00 59 23 89 20 82 48 32 c5 3d 2b 78 72 0f 32 03
0010  58 e3 49 3d 82 98 30 80 28 01 01
```

Its 21 codes are `RESET`, 19 literals, `END` (all 10-bit — the file is too short to reach the
width switch).

---

## 10. Flag

```
cruXipher{m3ss3d_up_compXsion}
```

---

## 11. Takeaways / dead ends

* **The PDF is a decoy.** ROT13 body, an invisible OCG "keyring" layer with a hex key, and two
  fake flags (`flag{nice_grep_but_not_the_flag}`, `ctf{copy_paste_is_a_trap}`). Seeding the
  PRNG with the PDF key yields garbage. The real spec was in `sample.txt` all along — always
  read the known-plaintext file *as text*, not just as a key.
* **A wrong-looking dictionary is usually a wrong bit width.** The first 768 codes decoded
  perfectly and then turned to noise, which strongly suggests corruption but is actually the
  10 → 11-bit width growth. Cross-check the byte budget: `768×10 + 358×11 = 11618 bits =
  1453 bytes` — the file size confirms the schedule before any decoding.
* **Pragmas > brute force.** A combinatorial search over candidate flag texts produced
  thousands of matching candidates; the data alone is ambiguous. The bulletin text collapsed the
  search space to a single xorshift variant.
* **Always cross-validate.** The known-plaintext route (which needs no key) and the key-derived
  route agreed on all 69 mappings, which is what made the result trustworthy.
* **Little-endian everywhere:** bits from the low end of each byte, code *k*'s bit *b* at
  position *b* — getting this backwards is another classic time sink.
