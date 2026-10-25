# Writeup: Minecraft Seed

**Category:** Misc / Forensics\
**Flag:** `cruXipher{123321}`

## Challenge

A friend found a YouTube video of a Minecraft world and wants the seed. All we know is that it lies between 100,000 and 150,000. The flag format is `cruXipher{seed}`. The attachment, `images.zip`, contains five screenshots.

## Step 1: Read the screenshots

Every screenshot has the F3 debug overlay open. That gives us three useful things:

- **Version:** `Minecraft 1.21.3 (1.21.3/vanilla)`. Structure placement and biome generation change between versions, so the version matters for the brute force.
- **Exact player coordinates** (XYZ and block position).
- **The biome** the player stands in, plus the structure being looked at.

| Image | Player position (X, Z) | Biome | What it shows |
| --- | --- | --- | --- |
| image.png | (-485, -52) | dark\_forest (at y=153) | Open forest, no structure |
| image2.png | (2922, -4678) | dark\_forest | Woodland mansion roof |
| image3.png | (-1959, 36) | desert | Stronghold end portal room |
| image4.png | (-1916, 81) | desert | Desert temple (sandstone) |
| image5.png | (-4372, 31) | jungle | Jungle temple (mossy cobblestone) |

The player is standing on or next to each structure in screenshots 2, 3, 4 and 5, so those coordinates are very close to the structure positions.

## Step 2: Plan

The search space is only 50,001 seeds, so brute force is cheap. Structure placement in Minecraft depends only on the world seed, the structure type and the region coordinates, so I can ask "does seed S put a desert temple near (-1915, 81)?" without generating the world.

I used the [cubiomes](https://github.com/Cubitect/cubiomes) C library, which reimplements Minecraft's biome and structure generation and supports `MC_1_21_3`.

## Step 3: Brute force

For each seed from 100000 to 150000, I checked whether:

1. a **desert pyramid** generates within 48 blocks of (-1915, 81),
2. a **jungle pyramid** generates within 48 blocks of (-4371, 31),
3. a **woodland mansion** generates within 100 blocks of (2922, -4677),
4. the **biome** at each screenshot position matches the F3 readout.

```c
static int near(int type, int mc, uint64_t seed, int x, int z, int tol) {
    StructureConfig sc;
    if (!getStructureConfig(type, mc, &sc)) return 0;
    int rs = sc.regionSize * 16;
    int rx = (int)floor((double)x / rs), rz = (int)floor((double)z / rs);
    for (int dx = -1; dx <= 1; dx++)
        for (int dz = -1; dz <= 1; dz++) {
            Pos p;
            if (!getStructurePos(type, mc, seed, rx + dx, rz + dz, &p)) continue;
            if (abs(p.x - x) <= tol && abs(p.z - z) <= tol) return 1;
        }
    return 0;
}
```

The three structure checks alone left 50 candidates, which was too many. Adding a strict requirement that all five biome samples match returned nothing, because my biome sample for the first screenshot was taken at the wrong height (see below). So I scored each seed by number of matches instead of requiring all of them, and printed anything scoring 6 or more out of 8.

Only one seed qualified: **123321**, with all three structures matched and 4 of 5 biomes.

## Step 4: Verify the one biome mismatch

The mismatch was the first screenshot at (-485, -52). My code sampled the biome at y=63, where 1.21's 3D biome system gives `dripstone_caves` underground. The screenshot was taken at y=153.9 in the open air, so I resampled at the right height:

```
(-485,-52)   y=153 -> dark_forest   (matches)
(2922,-4678)        -> dark_forest   (matches)
(-1959,36)          -> desert        (matches)
(-1916,81)          -> desert        (matches)
(-4372,31)          -> jungle        (matches)
```

All five biomes agree.

## Step 5: Cross-check with the stronghold

The third screenshot shows an end portal room. For seed 123321, cubiomes lists the first stronghold at about **(-1964, 4)**, in the same area as the screenshot position (-1959, 36). The stronghold's reported position is a chunk-level estimate, so this is consistent with the portal room being a few dozen blocks away. It gives independent confirmation that the seed is right.

## Result

The seed is **123321**.

```
cruXipher{123321}
```

## Takeaways

- F3 screenshots leak enough to pin down a seed: structure positions are a deterministic function of the seed.
- Always sample biomes at the player's actual height in 1.18+, since biomes are 3D.
- Scoring candidates by number of matches is more robust than requiring every check to pass, especially when one of your own inputs might be off.
