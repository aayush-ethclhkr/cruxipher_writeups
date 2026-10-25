# T2F Program

**Points:** 500  
**Category:** Reverse Engineering / Compression  
**File:** `t2f-masterclass.zip`

## Flag

```text
cruXipher{sighunzips}
```

## Challenge

The `t2f-masterclass.zip` attachment contains a damaged raw DEFLATE stream. Its 
compressed payload begins at byte offset 38 and has length 121532 bytes. Normal 
extraction fails because the dynamic Huffman literal/length table is invalid.

## Method

Parse the dynamic-block header and decode its code-length table. Enumerate small 
repairs to literal/length code lengths, then attempt raw DEFLATE decompression 
with `zlib.decompress(candidate, -15)`. Require both the expected uncompressed 
length, 131072 bytes, and the original ZIP CRC32; a successful decompression 
alone is insufficient.

The successful repair sets literal/length table entries 100 and 113 to zero. The 
resulting output matches CRC32 `0xcce1c38d`, and searching its bytes for the 
challenge prefix recovers the flag.

## Solution

The solver uses only Python's standard library to repair the corrupted DEFLATE 
stream and extract the flag.

### Code

```python
from pathlib import Path
import struct, zlib, itertools

src = Path('t2f-masterclass.zip').read_bytes()
raw = src[38:38+121532]

class Bits:
    def __init__(s, b):
        s.b = b
        s.p = 0
    def get(s, n):
        v = sum(((s.b[(s.p+i)//8]>>((s.p+i)%8))&1)<<i for i in range(n))
        s.p += n
        return v

def tree(ls):
    counts = [ls.count(i) for i in range(16)]
    counts[0] = 0
    code = 0
    nexts = {}
    out = {}
    for i in range(1, 16):
        code = (code+counts[i-1])<<1
        nexts[i] = code
    for symbol, l in enumerate(ls):
        if l:
            out[(l, nexts[l])] = symbol
            nexts[l] += 1
    return out

def decode(r, tr):
    c = 0
    for n in range(1, 16):
        c = c*2+r.get(1)
        if (n, c) in tr:
            return tr[n, c]
    raise ValueError(('invalid', r.p))

r = Bits(raw)
r.get(3)
nl = r.get(5)+257
nd = r.get(5)+1
nc = r.get(4)+4
order = [16,17,18,0,8,7,9,6,10,5,11,4,12,3,13,2,14,1,15]
ls = [0]*19
for i in order[:nc]:
    ls[i] = r.get(3)
t = tree(ls)
lengths = [decode(r, t) for _ in range(nl+nd)]

def patch(changes):
    b = bytearray(raw)
    for i, val in changes:
        code = {0:0, 1:1, 4:2, 5:3, 6:4, 7:5, 8:6, 9:7}[val]
        for k in range(3):
            p = 74+i*3+k
            mask = 1<<(p%8)
            if (code>>(2-k))&1:
                b[p//8] |= mask
            else:
                b[p//8] &= 255^mask
    return bytes(b)

if __name__ == '__main__':
    import re
    target_crc = struct.unpack_from('<I', src, 14)[0]
    candidates = [[(i, 8)] for i, v in enumerate(lengths[:nl]) if v == 7]
    candidates += [[(i, 0)] for i, v in enumerate(lengths[:nl]) if v == 8]
    singles = [(i, 9) for i, v in enumerate(lengths[:nl]) if v == 8]
    singles += [(i, 0) for i, v in enumerate(lengths[:nl]) if v == 9]
    candidates += [list(pair) for pair in itertools.combinations(singles, 2)
                   if pair[0][0] != pair[1][0]]
    for changes in candidates:
        try:
            fixed = patch(changes)
            output = zlib.decompress(fixed, -15)
        except zlib.error:
            continue
        if len(output) == 131072 and zlib.crc32(output) == target_crc:
            print('Repaired code lengths:', changes)
            print('Verified CRC32:', hex(target_crc))
            Path(__file__).with_name('flag.txt').write_bytes(output)
            Path(__file__).with_name('repaired.zip').write_bytes(
                src[:38] + fixed + src[38+len(fixed):])
            print(re.search(rb'cruXipher\{[^}]+\}', output).group().decode())
            break
    else:
        raise RuntimeError('No repair matched the original checksum')
```

### Usage

```sh
python3 repair.py
```

### Output

```text
Repaired code lengths: [(100, 0), (113, 0)]
Verified CRC32: 0xcce1c38d
cruXipher{sighunzips}
```

The solver also writes `flag.txt` (the decompressed content) and `repaired.zip` 
(the fixed archive).
