# What Did You Compress

**Points:** 300  
**Category:** Misc / Compression / Custom Format  
**Files:** `flag.lzw`, `sample.txt`, `sample.lzw`

## Flag

```text
cruXipher{m3ss3d_up_compXsion}
```

The capital `X` in `compXsion` is part of the recovered data.

## Challenge

> Someone had the bright idea of writing their own compressor, and then they
> forgot how it works. Help them recover the data they compressed in their file.
> Make sure to submit the flag in the format of cruXipher{...}

## Find the Format Clues

The provided files have these sizes:

| File | Bytes |
| --- | ---: |
| `sample.txt` | 2,323 |
| `sample.lzw` | 1,453 |
| `flag.lzw` | 27 |

The important clues are in the sample text itself. Its archive bulletin describes
a shuffled symbol table, Fisher–Yates shuffling, a small xorshift-family generator,
reset and end codes, bits packed from the low end of each byte, and code widths
that increase as the dictionary fills. It explicitly gives this index key:

```text
0745B6
```

This is enough to test a concrete LZW implementation against the known plaintext.

## Recover the Code Packing and Alphabet

Reading ten bits at a time, least significant bit first, gives the start of the
sample's code stream:

```text
256, 67, 78, 238, 162, 69, 133, 239, 133, 77, 3, 130, 262, ...
```

After the leading reset, the sample starts with `Agent Z lost ...`. The first
codes therefore reveal these shuffled literal assignments:

| Code | Literal |
| ---: | --- |
| 67 | `A` |
| 78 | `g` |
| 238 | `e` |
| 162 | `n` |
| 69 | `t` |
| 133 | space |
| 239 | `Z` |

The next repeated phrase also agrees with LZW: code `262` expands to `t `.

The assignments match a descending Fisher–Yates shuffle of the byte values
`0..255`, seeded with `0x0745B6`, using xorshift32 with shifts `(13, 17, 5)`:

```python
state ^= (state << 13) & 0xFFFFFFFF
state ^= state >> 17
state ^= (state << 5) & 0xFFFFFFFF
state &= 0xFFFFFFFF
j = state % (i + 1)
symbols[i], symbols[j] = symbols[j], symbols[i]
```

Here `symbols[code]` is the original literal byte. The state advances once for
each shuffle step, with `i` descending from 255 to 1.

## Decode LZW

The rules confirmed by the actual files are:

- Literal codes: `0..255`, interpreted through the shuffled alphabet.
- Reset: `256`.
- End: `257`.
- First dictionary entry: `258`.
- Starting width: 10 bits.
- Bit packing: least significant bit first.
- On each dictionary insertion, increment the next free code. Increase the width
  when that next free code equals `1 << width`.
- Use the normal LZW special case when a code equals the next free code:
  `previous + previous[:1]`.

The complete sample decodes to an exact byte-for-byte match with `sample.txt`.
This also checks the width transition from 10 to 11 bits, rather than just the
initial alphabet assignments.

The flag file contains only 10-bit codes:

```text
256, 214, 146, 130, 130, 146, 83, 247, 43, 158,
247, 200, 3, 214, 158, 245, 130, 38, 3, 162, 257
```

Using the same verified table, these decode to:

```text
m3ss3d_up_compXsion
```

Wrap that body in the flag format requested by the challenge.

## Solution

The solver constructs the shuffled table, decompresses the sample, asserts an 
exact match, and then prints the flag.

See `solvers.py` for the complete implementation.

### Usage

```sh
python3 solvers.py
```

### Output

```text
Sample: exact match
cruXipher{m3ss3d_up_compXsion}
```
