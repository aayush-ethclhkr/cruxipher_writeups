# santas-nice-list

**CruXipher CTF 2026 | OSINT + Crypto | 490 points**

| | |
|---|---|
| **Artifact** | A numbered list of 41 places (shops, restaurants, a school, and seven Plus Codes), followed by an empty line `42.` |
| **Tags** | osint, geolocation, crypto |
| **Flag format** | `cruXipher{...}` / `cruX{...}` |
| **Tools used** | Google Maps, Open Location Code library, Python, a UTC offset reference |
| **Solved by** | piyush |

---

## Summary

Every place on the list sits on a longitude that matches a real UTC offset when divided by 15°, so each entry encodes one offset. The 32 offsets that have a usable land location form a 32-symbol alphabet, which maps onto Base32 after a shift of 25 (December 25). Entry 23 is missing on purpose: it is the North Pole (offset 0), and putting it back makes the string decode to the flag.

**Solve chain:**

```
41 POIs -> geocode -> lng / 15 = UTC offset -> 32-offset alphabet
  -> Christmas shift (-25) -> restore #23 (North Pole) -> Base32 decode -> flag
```

---

## Step 1: Geocoding the list

Most entries are business names with a town, which Google Maps resolves directly. Seven entries are Open Location Codes (Plus Codes), for example:

- `#6  JFFX+QH2 Shiraz`
- `#16 7MM8M54Q+CRG` (Bokaro)
- `#28 6QFH46RX+PW9` (Sorong)

The full-length codes decode offline. The short ones like `JFFX+QH2 Shiraz` need the town name as a reference point, which Google Maps handles.

```python
>>> from openlocationcode import openlocationcode as olc
>>> a = olc.decode("7MM8M54Q+CRG")
>>> (round(a.latitudeCenter, 6), round(a.longitudeCenter, 6))
(23.656063, 86.189578)      # #16 The Daily Shop, Bokaro

>>> a = olc.decode("6QFH46RX+PW9")
>>> (round(a.latitudeCenter, 6), round(a.longitudeCenter, 6))
(-0.858213, 131.249859)     # #28 Rumah Makan Manado Rufei, Sorong
```

The places are scattered all over the world with no obvious order in latitude. Longitude turned out to be the signal.

---

## Step 2: Finding the pattern (solar meridians)

> **Dead end first.** The obvious idea is to use each place's civil timezone (IST, PKT, AKST, ...). That does not work. Civil zones squash very different longitudes onto a few political values (all of India is +05:30, for example), and the resulting string does not decode to anything.

What does work is the **solar offset**:

```
u = longitude / 15°
```

Every entry lands on or very close to a meridian that matches one of the real-world UTC offsets, including the unusual ones like +5:45 and +8:45. A few examples:

| # | Place | Longitude | Civil zone | Solar offset (meridian) |
|---|---|---|---|---|
| 16 | The Daily Shop, Bokaro, India | `+86.190°` | +05:30 IST | **+05:45** (86.25°) |
| 19 | DK Grill, Bahria Town Karachi, Pakistan | `+67.348°` | +05:00 PKT | **+04:30** (67.50°) |
| 21 | Olive school, Roviana Lagoon, Solomon Islands | `+157.500°` | +11:00 SBT | **+10:30** (157.50°) |
| 25 | Heppa Restaurant, Höfn, Iceland | `-15.201°` | +00:00 GMT | **-01:00** (-15.00°) |
| 28 | Rumah Makan Manado Rufei, Sorong | `+131.250°` | +09:00 WIT | **+08:45** (131.25°) |
| 36 | Salmon & Bear Restaurant, McCarthy, AK, USA | `-142.923°` | -09:00 AKST | **-09:30** (-142.50°) |
| 40 | Restaurante Leão, Capão do Leão, RS, Brazil | `-52.500°` | -03:00 BRT | **-03:30** (-52.50°) |

![Offset meridians used by the list with the seven sample POIs](images/santa_meridians_map.png)

Green lines are the `15° × u` meridians that appear in the list. Sample POI positions are approximate and only shown for context.

![Civil timezone vs solar offset](images/santa_civil_vs_solar.png)

---

## Step 3: Building the 32-symbol alphabet

Between -12:00 and +12:00 there are 35 real UTC offsets. Three of them cannot carry a populated land POI on their exact meridian:

- **-12:00** shares the 180° meridian with +12:00
- **-11:00** falls in open ocean
- **-02:00** falls in open ocean

Removing those leaves exactly **32** offsets, which is the size of the Base32 alphabet (`A-Z` + `2-7`). That count was the strongest hint that the encoding is Base32.

Sorted ascending, each offset gets an index `k = 0..31`. A straight index-to-letter mapping gives nonsense, but the theme is Christmas, so I tried a shift of **25** (December 25). With that shift, the first characters immediately decode to `cruX`.

| Offset | -10:00 | -9:30 | -9:00 | -8:00 | -7:00 | -6:00 | -5:00 | -4:00 | -3:30 | -3:00 | -1:00 | 0:00 | +1:00 | +2:00 | +3:00 | +3:30 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k | 0 | 1 | 2 | 3 | 4 | 5 | 6 | 7 | 8 | 9 | 10 | 11 | 12 | 13 | 14 | 15 |
| Base32 (k-25) | **H** | **I** | **J** | **K** | **L** | **M** | **N** | **O** | **P** | **Q** | **R** | **S** | **T** | **U** | **V** | **W** |

| Offset | +4:00 | +4:30 | +5:00 | +5:30 | +5:45 | +6:00 | +6:30 | +7:00 | +8:00 | +8:45 | +9:00 | +9:30 | +10:00 | +10:30 | +11:00 | +12:00 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| k | 16 | 17 | 18 | 19 | 20 | 21 | 22 | 23 | 24 | 25 | 26 | 27 | 28 | 29 | 30 | 31 |
| Base32 (k-25) | **X** | **Y** | **Z** | **2** | **3** | **4** | **5** | **6** | **7** | **A** | **B** | **C** | **D** | **E** | **F** | **G** |

```python
OFFSETS_32 = [-10, -9.5, -9, -8, -7, -6, -5, -4, -3.5, -3, -1, 0, 1, 2, 3, 3.5,
              4, 4.5, 5, 5.5, 5.75, 6, 6.5, 7, 8, 8.75, 9, 9.5, 10, 10.5, 11, 12]
B32 = "ABCDEFGHIJKLMNOPQRSTUVWXYZ234567"

def to_b32(offset):
    return B32[(OFFSETS_32.index(offset) - 25) % 32]   # Christmas shift
```

---

## Step 4: The missing entry (#23)

Converting all 41 entries in order gives this string, with something clearly wrong around position 23:

```
MNZHKWDJOBUGK4T3KMYFEU[?]ZGRXDA4TUNBJXINDSPU
```

The first 22 characters decode cleanly to `cruXipher{S0R`, then the output breaks. Two things point to a missing symbol:

1. A 26-byte plaintext needs `ceil(26 × 8 / 5) = 42` Base32 characters. The list has 41 places plus an empty `42.`, so one symbol is unaccounted for.
2. The symbols after position 22 only line up into readable text once one symbol is inserted there.

The intended entry #23 is the **North Pole**, where all meridians meet. That corresponds to offset `0`, which maps to `S`. Dropping it shifted entries 24..42 up to 23..41. The flag itself apologises to the North Star for this.

| Block | Entries | Solar offsets (u = lng / 15°) | Base32 | Plain |
|---|---|---|---|---|
| 1 | 01..08 | -6, -5, +5, -10, -8, +3.5, +10, -9 | `MNZHKWDJ` | `cruXi` |
| 2 | 09..16 | -4, +9, +2, +12, -8, +6, +1, +5.75 | `OBUGK4T3` | `pher{` |
| 3 | 17..24 | -8, -6, +4.5, +11, +10.5, +2, **0 (North Pole)**, +5 | `KMYFEU`**`S`**`Z` | `S0RRY` |
| 4 | 25..32 | +12, -1, +4, +10, +8.75, +6, +1, +2 | `GRXDA4TU` | `4n0rt` |
| 5 | 33..40 | -5, +9, -9, +4, -9.5, -5, +10, 0 | `NBJXINDS` | `hSt4r` |
| 6 | 41..42 | -3.5, +2 (padded with `======`) | `PU======` | `}` |

---

## Step 5: Decoding

```python
>>> import base64
>>> s = "MNZHKWDJOBUGK4T3KMYFEUSZGRXDA4TUNBJXINDSPU"
>>> base64.b32decode(s + "======")
b'cruXipher{S0RRY4n0rthSt4r}'
```

---

## Flag

```
cruXipher{S0RRY4n0rthSt4r}
cruX{S0RRY4n0rthSt4r}
```

---

## Notes

- The civil timezone was a deliberate trap. Using the raw longitude instead of the political timezone was the key insight.
- Counting helps: 32 usable offsets matched the Base32 alphabet, and the 42-character length explained the empty last line.
- The Christmas theme was the hint for both the shift value (25) and the missing North Pole entry.
