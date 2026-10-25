# Dropped as a Baby

**Points:** 450  
**Category:** Forensics / Misc  
**File:** `dropped-as-a-baby.zip`

## Flag

```text
cruXipher{th1s_1m4ge_m1gh7_h4v3_4_c0ncuss1on}
```

## Challenge

> I don't think this guy knows how images work

The archive holds 14 files named `dat_xxxxxx.png` (about 320–350 KB each), with the tag **"evil archive"**.

## Step 1: The PNGs Are Broken

None of the files open in an image viewer, and `file` reports most of them as plain `data`. Parsing the chunk structure revealed several deliberate corruptions:

- The 8-byte PNG signature has altered bytes (e.g., `0d0b1a0a` instead of `0d0a1a0a`)
- The IHDR fields are scrambled (wrong bit depth, color type, interlace flag, sometimes width and height swapped)
- Many IHDR and IDAT CRCs are wrong
- Junk chunks are scattered between IDATs: misspelled types like `teXt`, `vpAg`, `prVt`, `gAMq` and `pHYq`
- Decoy `tEXt` comments ("nothing to see here", "i love programming")
- Some files have garbage after `IEND`

The one thing left intact is the IDAT payload - it still concatenates and zlib-decompresses cleanly.

## Step 2: Repairing the Headers

The approach:

1. Walk the chunks and keep only the IDAT payloads
2. Concatenate them and decompress with zlib
3. Compare the decompressed length against every plausible (width, height, depth, color type, interlace) combination

Every file matched exactly one family of parameters: **8-bit RGB, non-interlaced**, with a decompressed size of either `360400` bytes (300×400) or `360300` bytes (400×300).

## Step 3: The Images Are Puzzle Pieces

The repaired images are noisy blue-to-green gradient tiles with fragments of tall, stretched, yellow text. Some tiles are portrait and some landscape. The stretch direction is perpendicular between the two groups.

The text is stretched about 6× vertically. Using edge correlation, four stacks of three tiles were identified:

| Stack | Tiles (top to bottom) |
| --- | --- |
| A | 1, 0, 3 |
| B | 7, 5, 8 |
| C | 9, 11, 13 |
| D | 6, 10, 12 |

Tiles 2 and 4 are padding (pure background, no strokes).

A brute-force search over all orderings and orientations of the four columns picked one clear winner: **C, D, A (rotated 180°), B (flipped vertically)**. The result is a single 1600×900 image.

## Step 4: Reading the Text

To read the assembled image:

1. Rotate it by 180°
2. Apply a light Gaussian blur to suppress noise
3. Resize vertically by roughly 1/6 to restore normal aspect ratio

The line then reads clearly as:

```text
jvuAiroiy{xh1v_1m4il_q1nl7_h4y3_4_c0pjyzw1oq}
```

The glyph shapes are distinct in this font: `1` has a flag, `l` has a curved tail, and `0` has a slash.

## Step 5: Decrypting the Text

The prefix `jvuAiroiy` has the same length and casing pattern as `cruXipher`, so the text is a polyalphabetic cipher over the known flag format. Computing the per-letter shift gives:

```text
c→j: 7   r→v: 4   u→u: 0   X→A: 3   i→i: 0
p→r: 2   h→o: 7   e→i: 4   r→y: 7
```

Those shifts are `7 4 0 3 0 2 7 4 7`, which spell **`headache`** (h=7, e=4, a=0, d=3). Decrypting with a Vigenère cipher and the key `headache`, advancing the key only on letters:

```python
ct = 'jvuAiroiy{xh1v_1m4il_q1nl7_h4y3_4_c0pjyzw1oq}'
key = 'headache'
out, k = [], 0
for ch in ct:
    if ch.isalpha():
        s = ord(key[k % len(key)]) - 97
        base = 65 if ch.isupper() else 97
        out.append(chr((ord(ch) - base - s) % 26 + base))
        k += 1
    else:
        out.append(ch)
print(''.join(out))
```

## Solution

The complete solution involves:

1. Repairing PNG headers by extracting and decompressing IDAT streams
2. Determining correct dimensions from decompressed size
3. Using edge correlation to reassemble tiles
4. Descrambling and descaling the text
5. Breaking the Vigenère cipher using known plaintext

## Key Takeaways

- PNG structure is forgiving to rebuild when metadata is corrupted
- Ignore decoy text chunks and misspelled chunk types
- When tiles are stretched, edge correlation is a strong signal for reassembly
- When a decoded string looks like the flag format with wrong letters, derive the key directly from the known prefix
