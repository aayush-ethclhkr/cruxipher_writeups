# Puffer (Scrambled Tiles)

**Points:** 475  
**Category:** Misc / Forensics / QR Code  
**File:** `buncharandoms.zip`

## Flag

```text
cruXipher{1_l0v3_3x1f_m3t4dat4}
```

## Challenge

> No cats were harmed during the naming of these files. This archive may be useful.

The attachment contains a folder `output_pixels/` with 841 small JPEG files with random-looking names.

## Step 1: Look at the Files

- There are exactly **841** files, and 841 = 29 × 29
- Each JPEG is a tiny **10 × 10** image
- Every tile is either solid black or solid white (mean brightness clusters at ~0 or ~255)

A 29 × 29 grid of black and white blocks is the size of a **version 3 QR code**. Each tile is one QR module, and the puzzle is to put them back in the right order.

The filenames are random, and the zip timestamps are not unique (830 distinct times for 841 files), so neither gives a reliable order.

## Step 2: Find the Ordering in the Metadata

The "no cats harmed" hint points at metadata (EXIF). Dumping strings from a file:

```bash
$ strings -n 4 0BrMQ8ZTf0n3pI.jpg | head
JFIF
AExif
(ASCII
34rot9ten
```

Every file has a unique EXIF `UserComment` that looks like an English word with digits mixed in:

| UserComment | Word | Digits | Position |
| --- | --- | --- | --- |
| `34rot9ten` | rotten | 3, 4, 9 | **349** |
| `4enter66` | enter | 4, 6, 6 | **466** |
| `red198` | red | 1, 9, 8 | **198** |
| `90useful` | useful | 9, 0 | **90** |

The words are noise; the digits carry the information. Stripping everything except digits gives a unique value from **1 to 841** for each file - that is the tile's position.

## Step 3: Rebuild the Grid

Using the number as a 1-based index, tile `n` goes at column `(n-1) mod 29` and row `(n-1) div 29`. A tile counts as white if its mean brightness is above 128.

```python
import glob, re
from PIL import Image

W = 29
img = Image.new('L', (W, W))
for f in glob.glob('output_pixels/*.jpg'):
    d = open(f, 'rb').read()
    i = d.find(b'ASCII\x00\x00\x00') + 8
    j = d.find(b'\xff\xdb', i)
    n = int(re.sub(r'\D', '', d[i:j].decode())) - 1
    t = Image.open(f).convert('L')
    img.putpixel((n % W, n // W), 255 if sum(t.getdata()) / 100 > 128 else 0)

# Add quiet zone and scale up
big = Image.new('L', (W + 8, W + 8), 255)
big.paste(img, (4, 4))
big = big.resize(((W + 8) * 10, (W + 8) * 10), Image.NEAREST)
big.save('qr.png')
```

## Step 4: Decode

OpenCV's QR detector reads the reconstructed image:

```python
import cv2
v, _, _ = cv2.QRCodeDetector().detectAndDecode(cv2.imread('qr.png'))
print(v)
# Y3J1WGlwaGVyezFfbDB2M18zeDFmX20zdDRkYXQ0fQ==
```

That is base64. Decoding it:

```bash
$ echo 'Y3J1WGlwaGVyezFfbDB2M18zeDFmX20zdDRkYXQ0fQ==' | base64 -d
cruXipher{1_l0v3_3x1f_m3t4dat4}
```

The flag reads "I love EXIF metadata" in leetspeak, matching how the puzzle was hidden.

## Solution

Complete reconstruction script provided in the repository.

## Takeaways

- When a file count is a perfect square (841 = 29²), suspect a tile or pixel puzzle
- Filenames and timestamps are obvious ordering keys, but the intended one was hidden in EXIF
- The words in the comments were a distraction - strip them and keep only the digits
- Remember the quiet zone: many QR decoders fail without a white border around the code
