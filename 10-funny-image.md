# Funny Image

**Points:** 400  
**Category:** Steganography / Forensics  
**File:** `funny-image.png`

## Flag

```text
cruXipher{r_rAnDom_Keey_Th4T_i56_vErY_uNCrAcKaBl237}
```

## Challenge

> Joe Mudra has a funny image, but he doesn't find it funny. John Cert told him to look deeper: there's some strange subtraction and reversal going on in the coordinates. Can you find the funny in Joe's image?

The file is a 4096 × 4096 RGBA PNG that looks like nested grey squares.

## Step 1: Rule Out the Usual Suspects

- **File structure:** Only `IHDR`, `bKGD`, `IDAT` and `IEND` chunks. No extra text chunks, no trailing data.
- **Colours:** Only 21 distinct colours. 13 are flat grey levels in 256 × 256 px blocks.
- **Counting pixels:** Each grey level should cover an exact multiple of 65,536 pixels. Almost every level was short by a handful of pixels - the border colour was short by 21, the next level by 15, etc.

## Step 2: Find the Odd Pixels

Looking for pixels that differ from all four neighbours revealed exactly **52** outlier pixels. Every one is the surrounding grey level plus or minus 6.

## Step 3: Spot the Grid

Dividing the image into 256 × 256 cells (16 columns and 4 rows), each cell contains at most one odd pixel:

- Rows 0, 1 and 2 each have exactly 16 odd pixels (one per column)
- Row 3 has 4 (in the first four columns)
- Total: 3 × 16 + 4 = **52**

Reading the points in cell order (left to right, then top to bottom) gives a 52-element sequence - a plausible flag length.

## Step 4: Decode (Subtraction and Reversal)

The hint says "subtraction and reversal in the coordinates". The decode that worked treats x and y coordinates as two separate streams:

1. Take the x coordinates in reading order: `x_0 ... x_51`
2. Take the y coordinates and **reverse** that stream: pair x at index `i` with y at index `51 - i`
3. **Subtract**: `char_i = (x_i - y_(51-i)) mod 256`

The result starts with `cruXipher{` and is printable ASCII end to end.

## Solution

```python
# Extract odd pixel coordinates (x, y)
# Sort by cell order (col, row)
# Apply reversal and subtraction decode

coords_x = [x_0, x_1, ..., x_51]  # in order
coords_y_rev = [y_51, y_50, ..., y_0]  # reversed

flag = ''.join(chr((coords_x[i] - coords_y_rev[i]) % 256) for i in range(52))
```

## Takeaways

- When a synthetic image has exact block structure, count pixels per colour to find tampering
- Isolated outlier pixels (differing from all four neighbours) signal LSB-style or position-based stego
- If the hint mentions coordinates, test combinations across streams rather than only per-point transforms
