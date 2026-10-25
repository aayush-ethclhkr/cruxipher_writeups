# zebra — CTF Writeup

**Points:** 300  
**Tags:** misc, compression, custom-format  
**Attachment:** `buncharandoms.zip`

The challenge description was:

> No cats were harmed during the naming of these files
>
> This archive may be useful

## 1. Inspecting the archive

The ZIP contains **841 JPEG files** inside `output_pixels/`. Their filenames look random, such as `0BrMQ8ZTf0n3pI.jpg`.

Each image is a **10×10 solid black or solid white tile**. The number of tiles is a useful clue:

```text
841 = 29 × 29
```

This suggests that the tiles could form a square binary image, possibly a QR code. The next problem is finding their correct order.

## 2. Finding the ordering in EXIF metadata

The JPEGs contain an EXIF `UserComment` field. For example:

| Image | UserComment | Digits joined together |
|---|---|---|
| `0BrMQ8ZTf0n3pI.jpg` | `34rot9ten` | `349` |
| `0D2iiIPSCWcUwd.jpg` | `4enter66` | `466` |
| `0djxCRu9JbNIHA.jpg` | `801feigned` | `801` |
| `0fkqEVyu4pj62d.jpg` | `us71ef2ul` | `712` |

Removing the non-digit characters from every comment produces each integer from **1 through 841 exactly once**. These numbers provide a position for every tile; the random filenames are unnecessary for reconstruction.

In Pillow, the EXIF subdirectory is available through tag `34665`, and `UserComment` is tag `37510`. These comments start with the eight-byte encoding prefix `b'ASCII\x00\x00\x00'`, which we remove before reading the text.

## 3. Reconstructing the QR code

Sort the tiles by their recovered indices and place their colors into a 29×29 image, filling each row from left to right, then moving down to the next row.

For a one-based index `i`, the coordinates are:

```python
x = (i - 1) % 29
y = (i - 1) // 29
```

Because each JPEG is a uniform tile, its top-left pixel is enough to determine its color. Adding a four-module white border and enlarging the result with nearest-neighbor scaling produces an easily readable QR code.

![Reconstructed QR code](reconstructed_qr.png)

## 4. Decoding the payload

The reconstructed QR code contains:

```text
Y3J1WGlwaGVyezFfbDB2M18zeDFmX20zdDRkYXQ0fQ==
```

Base64-decoding that string reveals the flag:

```text
cruXipher{1_l0v3_3x1f_m3t4dat4}
```

## Reproduction script

Install the two dependencies:

```bash
python -m pip install Pillow zxing-cpp
```

Save the following as `solve.py` beside `buncharandoms.zip`, then run `python solve.py`:

```python
import base64
import re
import zipfile
from io import BytesIO

from PIL import Image, ImageOps
import zxingcpp

pixels = {}

with zipfile.ZipFile('buncharandoms.zip') as archive:
    for name in archive.namelist():
        with Image.open(BytesIO(archive.read(name))) as tile:
            raw = tile.getexif().get_ifd(34665)[37510]
            assert raw.startswith(b'ASCII\x00\x00\x00')
            comment = raw[8:].decode('ascii')
            index = int(''.join(re.findall(r'\d', comment)))
            assert index not in pixels
            pixels[index] = tile.getpixel((0, 0))[0]

assert set(pixels) == set(range(1, 842))

qr = Image.new('L', (29, 29))
qr.putdata([pixels[i] for i in range(1, 842)])
qr = ImageOps.expand(qr, border=4, fill=255)
qr = qr.resize((740, 740), Image.Resampling.NEAREST)
qr.save('reconstructed_qr.png')

result = zxingcpp.read_barcode(qr)
assert result is not None, 'QR decoding failed'

print('QR payload:', result.text)
print('Flag:', base64.b64decode(result.text, validate=True).decode('ascii'))
```

Expected output:

```text
QR payload: Y3J1WGlwaGVyezFfbDB2M18zeDFmX20zdDRkYXQ0fQ==
Flag: cruXipher{1_l0v3_3x1f_m3t4dat4}
