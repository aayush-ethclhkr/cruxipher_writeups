# Rice Writing

**Points:** 450  
**Category:** Steganography / Image Analysis  
**File:** `rice_grains.png`

## Flag

```text
cruXipher{riCegOesWiThaNyThinG}
```

## Challenge

The attachment is `rice_grains.png`, a 10000 × 10000 image. Its grain shapes 
encode data through their pixel areas rather than their positions.

## Method

1. Segment the original image using green-channel intensity greater than 120.
2. Identify 4-connected components. The analysis contains 311 grain components 
   with areas ranging from 41026 to 120435 pixels.
3. Sort the grain areas in ascending order.
4. Convert each area modulo 256 into an ASCII byte.
5. Search the resulting text for the exact `cruXipher{...}` prefix.

The decoded paragraph contains another brace-delimited string, 
`BryanQuangLe{bOrNNovEmbErNineTYnINetYsIX}`, before the actual challenge flag. 
Use the required challenge prefix to select the flag.

## Solution

The solver decodes the measured rice-grain areas from the saved CSV analysis or 
can process the image directly.

### Code

```python
"""Decode the measured rice-grain areas. See grain_areas.csv for every measurement.
Image segmentation: green > 120, 4-connected components in the original
10000 x 10000 PNG. There are 311 grains, with areas 41026 through 120435 pixels.
"""
from pathlib import Path
import csv
import re

root = Path(__file__).resolve().parent
with (root / 'grain_areas.csv').open(newline='', encoding='utf-8') as f:
    areas = sorted(int(row['area_pixels']) for row in csv.DictReader(f))

message = bytes(area % 256 for area in areas).decode('ascii')
print(message)
print('Flag:', re.search(r'cruXipher\{[^}]+\}', message).group())
```

### Usage

```sh
python3 decode.py
```

### Decoded Message

```text
BryanQuangLe{bOrNNovEmbErNineTYnINetYsIX}betterknownasRiceGumisanAmericanvideouploaderandonlinestreamerHeisbestknownforhisdisstracksandonlinefeudswithothercruXipher{riCegOesWiThaNyThinG}personalitiesSincecreatinghislinuxricingchannelhischannelhasreceivedovertentrillionsubscribersandovertwoquintillionvideoviews
```

### Output

```text
Flag: cruXipher{riCegOesWiThaNyThinG}
```
