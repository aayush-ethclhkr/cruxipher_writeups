# Is This Really OSINT?

**CruXipher CTF 2026 | Web + OSINT | 498 points**

| | |
|---|---|
| **Target** | `https://is-this-really-osint.cruxipher.crux-bphc.com` |
| **Tags** | web, geolocation, osint, browser |
| **Flag format** | `cruX{...}` |
| **Tools used** | Browser DevTools, Google Street View, NASA "Your Name in Landsat", curl, 7-Zip, Python |
| **Solved by** | 0xjyotirmoy |

---

## Summary

Six geolocation rounds each hide one character in the image. Solving all six unlocks a password through `/api/key`, and the six characters spell `B3ACOn`. That string is a TinyURL slug pointing to the author's GitHub repo, which holds a password-protected `notes.7z`. The text file inside is Vigenère-encrypted with the key `bacon`.

**Solve chain:**

```
6 geo stages -> /api/key -> letters "B3ACOn" -> tinyurl.com/B3ACOn
  -> GitHub repo -> notes.7z -> Vigenère (key "bacon") -> flag
```

---

## Step 1: Recon of the web app

The site is a single-page app that shows one image at a time and asks for coordinates. With the Network tab open while playing one round, the moving parts are easy to list:

| Request | Purpose |
|---|---|
| `GET /api/challenge-image/1..6` | Image for the current stage |
| `POST /api/verify` | Checks the submitted lat/lng for the current stage |
| `GET /api/key` | Returns a key, but only after all six stages are verified |
| Cookie `cruxipher_session` | JWT that tracks which stage the session has reached |

Progress is tracked server side through the JWT, so jumping straight to `/api/key` does not work. The six places have to actually be found.

---

## Step 2: Geolocating the six stages

Stages 1, 4, 5 and 6 are street-level photos of shopfronts. The store name plus the surroundings was enough to confirm each one on Street View.

Stages 2 and 3 are satellite images. Their odd shapes looked like letters, which led to NASA's **Your Name in Landsat** gallery, where every letter and digit is a real lake or river seen from orbit. Matching the shapes there gave the exact locations.

| Stage | Coordinates (lat, lng) | Location | How it was found | Char |
|---|---|---|---|---|
| 01 | `47.467125, 19.075161` | OBI store, Budapest, Hungary | Storefront branding, Street View | **B** |
| 02 | `-23.887111, 32.048528` | Lake Massingir, Mozambique | Landsat gallery, digit "3" | **3** |
| 03 | `40.659167, 47.113056` | River near Lake Guakhmaz, Yevlakh, Azerbaijan | Landsat gallery, letter "A" | **A** |
| 04 | `36.1859785, -5.4376502` | Conforama, Los Barrios, Spain | Storefront branding, Street View | **C** |
| 05 | `40.76072, -111.86738` | Storefront, Salt Lake City, UT, USA | Sign and street layout | **O** |
| 06 | `41.885558, -87.624064` | Nando's / Nutella Cafe, Chicago, IL, USA | Signage, Street View | **n** |

![Map of the six stage locations](images/osint_map_stages.png)

---

## Step 3: Picking up the key

After the sixth verify call succeeds, the frontend requests `/api/key` and stores the response in `localStorage` under a name that is a hint by itself. It can be read straight from the DevTools console:

```js
> localStorage.getItem("I_wonder_where_i_can_use_this_key")
'{"key": "th3-m4p-1s-n0t-th3-t3rr1t0ry-F4wCKY"}'
```

At this point there is a password, but nothing to use it on yet.

---

## Step 4: The characters hidden in the images

Looking at the stage images again, each one draws attention to exactly one character:

- On the shop photos, everything except one letter of the sign is blacked out.
- On the Landsat images, the shape itself is the character.

Case matters here, because stage 6 keeps a lowercase `n`.

| Stage 01: OBI sign, censored | Stage 02: Landsat lake shape | Stage 03: Guakhmaz river shape |
|:---:|:---:|:---:|
| ![Stage 1](images/stage_01.png) | ![Stage 2](images/stage_02.png) | ![Stage 3](images/stage_03.png) |
| **B** | **3** | **A** |

| Stage 04: Conforama sign | Stage 05: Storefront sign | Stage 06: Nando's / Nutella sign |
|:---:|:---:|:---:|
| ![Stage 4](images/stage_04.png) | ![Stage 5](images/stage_05.png) | ![Stage 6](images/stage_06.png) |
| **C** | **O** | **n** |

Read in order, the characters give: **`B3ACOn`**

---

## Step 5: Pivoting through a URL shortener

Six mixed-case characters look a lot like a short-link slug. I tried the string against a few common shorteners, and TinyURL answered with a redirect:

```bash
$ curl -sI https://tinyurl.com/B3ACOn | grep -iE "^(HTTP|location)"
HTTP/2 301
location: https://github.com/randombsgo234-pixel/ubiquitous-garbanzo
```

The repository belongs to the challenge author and contains an archive called `notes.7z`.

---

## Step 6: Opening the archive

The archive is password protected. The key from Step 3 opens it:

```bash
$ git clone https://github.com/randombsgo234-pixel/ubiquitous-garbanzo
$ cd ubiquitous-garbanzo
$ 7z x notes.7z -p'th3-m4p-1s-n0t-th3-t3rr1t0ry-F4wCKY'
$ cat "LAST AND FINAL I PROMISE.txt"
drwL{50z3u1m35_vv3_sm4g_y45_hu3_051o7_w3_f1r_4y0og_vv3_j4z}
```

---

## Step 7: Breaking the last layer (Vigenère)

The text keeps the shape of a flag, so it is a letter-only substitution. Lining up the known prefix `cruX` against `drwL` gives these shifts:

| Cipher | Plain | Shift | Key letter |
|:---:|:---:|:---:|:---:|
| d | c | +1 | b |
| r | r | +0 | a |
| w | u | +2 | c |
| L | X | +14 | o |

`b a c o ...` is the start of **bacon**, which is just `B3ACOn` with the digit removed. Digits, braces and underscores are skipped and do not advance the key.

First 15 letters against the repeating key:

| Ciphertext | d | r | w | L | z | u | m | v | v | s | m | g | y | h | u |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| Key | b | a | c | o | n | b | a | c | o | n | b | a | c | o | n |
| Plaintext | **c** | **r** | **u** | **X** | **m** | **t** | **m** | **t** | **h** | **f** | **l** | **g** | **w** | **t** | **h** |

Solver script:

```python
# Vigenère decrypt, key advances on letters only
ct  = "drwL{50z3u1m35_vv3_sm4g_y45_hu3_051o7_w3_f1r_4y0og_vv3_j4z}"
key = "bacon"

out, i = "", 0
for ch in ct:
    if ch.isalpha():
        base = 65 if ch.isupper() else 97
        shift = ord(key[i % len(key)]) - 97
        out += chr((ord(ch) - base - shift) % 26 + base)
        i += 1
    else:
        out += ch

print(out)
```

```
$ python3 solve.py
cruX{50m3t1m35_th3_fl4g_w45_th3_051n7_w3_d1d_4l0ng_th3_w4y}
```

---

## Flag

```
cruX{50m3t1m35_th3_fl4g_w45_th3_051n7_w3_d1d_4l0ng_th3_w4y}
```

---

## Notes

- The geolocation part is only half the work. The images double as the cipher key, so it pays to look at them again after each stage is solved.
- When a challenge hands out a short random-looking string, checking it as a short-link slug or a username is a cheap pivot worth trying early.
- Recognising the Landsat letters saved a lot of time on stages 2 and 3, since open water from orbit has very few other clues.
