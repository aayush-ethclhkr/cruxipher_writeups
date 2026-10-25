# PDF Prince

**Points:** 395  
**Category:** Forensics / PDF  
**File:** `chall.pdf`

## Flag

```text
cruX{xr3f_r3m3mb3rs_wh4t_y0u_d3l3t3d}
```

This is the exact string decoded from the document, including its `cruX` prefix.

## Challenge

> An internal memo from a sanitisation review.

## Examine the Revisions

The rendered page is a short memo:

```text
INTERNAL MEMO 0x2F // REV 3 // SANITISED // DO NOT FORWARD

The flag was supposed to be here .
I wonder where it went.
```

The PDF has three cross-reference sections, at offsets `7548`, `8805`, and
`9081`. Following the final trailer's `/Prev` links leads through the earlier
revisions:

```text
9081 -> 8805 -> 7548
```

The final metadata claims:

```text
SanitizerPro 2.1 - history purged
```

However, the updates were appended to the file. Older object bodies remain
recoverable in the raw bytes. In particular, object `4 0` has both an original
content stream and a replacement content stream.

There are two misleading flag strings:

- Object 10 contains `flag{nice_grep_but_not_the_flag}` in a draft note. The final
  xref marks that object free but does not erase its bytes.
- The font's `/ToUnicode` mapping makes the last text line extract as
  `ctf{copy_paste_is_a_trap}` followed by zero-width characters. It renders as a
  line of dashes instead.

The first three extracted lines are also ROT13-transformed relative to their
visible text. This establishes that extracted Unicode labels cannot be trusted
to describe the actual glyphs.

## Recover the Hidden Layer Key

The middle revision adds an optional-content group:

```text
12 0 obj
<< /Type /OCG /Name (keyring) >>
```

The catalog's default optional-content configuration places this group in its
`/OFF` array. Its content is still present in the updated page stream:

```text
/OC /MC0 BDC
...
(KEYRING / layer 7) Tj T*
(key = L7-b5acb9c6) Tj T*
...
EMC
```

The key is therefore:

```text
L7-b5acb9c6
```

## Recover the Original Encoded Text

Decompressing the first version of object 4 reveals a hex text operand:

```text
4C322D1C351663D939A7361B3753623E61D462A463484C3C2DE0356A63E039FB36473753624861FE6268637D4C352D4335FC636A39C8363B37B0627761686293633D4C162D69352363E2
```

This is 74 bytes, or 37 pairs. Split each pair into a high and low byte. The high
bytes form a repeated marker:

```text
L-5c967babcL-5c967babcL-5c967babcL-5c
```

That repeating 11-character string is precisely the key's even-indexed
characters followed by its odd-indexed characters:

```python
key = b"L7-b5acb9c6"
marker = key[::2] + key[1::2]       # b"L-5c967babc"
xor_key = key[1::2] + key[::2]      # b"7babcL-5c96"
```

XOR the low bytes with the repeating opposite-parity key, `xor_key`. The result
is a sequence of glyph IDs:

```text
5, 126, 119, 187, 196, 87, 126, 11, 183, 157,
126, 11, 130, 11, 130, 152, 11, 126, 125, 157,
81, 75, 2, 33, 157, 8, 171, 119, 157, 66,
11, 170, 11, 33, 11, 66, 128
```

For example, the first pair is `4C 32`. Its high byte is the marker `L`; its low
byte XOR the first mask byte gives `0x32 ^ 0x37 = 5`.

## Decode the Glyph Outlines

The embedded font is `ABCDEF+GhostMono`. Object 8 contains its Flate-compressed
TrueType data. The font has 197 glyphs, including glyph 0, and a format-4 `cmap`.

The current page references 175 different nonzero glyph IDs. The remaining 21
glyphs are exactly the glyphs listed by the font's `cmap`, and every recovered
glyph ID belongs to that set. This supports the XOR interpretation.

The font's Unicode character labels are shifted relative to its visible
outlines. Sorting the labels gives:

```text
034X_bcdfhlmrstuwxy{}
```

Rendering that string using the embedded font visibly produces:

```text
34X_bcdfhlmrstuwxy{}0
```

Each label therefore selects the outline for the next character in the sorted
alphabet, wrapping around at the end. For instance, `cmap['b']` is glyph 5, but
glyph 5 visibly renders `c`.

Using the uncorrected `cmap` labels on the recovered glyph IDs would produce:

```text
bmt4ywm0dXm0l0l_0mrXuf3sXx}tXc0h0s0c{
```

Correcting the labels to the actual outlines produces the flag:

```text
cruX{xr3f_r3m3mb3rs_wh4t_y0u_d3l3t3d}
```

## Solution

The solver extracts the two page content streams, reads the hidden layer key, 
verifies the high-byte marker, XOR-decodes the glyph IDs, parses the embedded 
font's `cmap`, and applies the outline shift. It uses only Python's standard 
library.

See `solvers.py` for the complete implementation.

### Usage

```sh
python3 solvers.py
```

### Output

```text
Hidden layer key: L7-b5acb9c6
Glyph IDs: [5, 126, 119, 187, 196, 87, 126, 11, 183, 157, ...]
cruX{xr3f_r3m3mb3rs_wh4t_y0u_d3l3t3d}
```

The failure in the sanitisation is that appending a new PDF revision and freeing
an object in the xref do not remove the historical bytes. The flag survives in
that retained history, with the key and font needed to interpret it still embedded.
