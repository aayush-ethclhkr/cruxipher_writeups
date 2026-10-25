# Writeup: pocketflag

**Category:** Reverse Engineering\
**Event:** cruXipher\
**Flag:** `cruXipher{0bfusc4t1on_g0D}`\
**PIN:** `6742`

## Challenge

A mystery Linux x86\_64 binary produces almost random output for any input. The only hint is that it needs a 4-digit PIN to give anything useful.

## Overview of the solution

The binary does not reject a wrong PIN. Each failed check silently corrupts a hidden key byte, and that key is later used to decrypt a 26-byte buffer that gets printed. A wrong PIN therefore still prints something, but it is garbage. The task is to recover the four PIN digits from the checks.

## Step 1: Triage

- `file` and `strings` showed a dynamically linked ELF that uses `sigaction`, `syscall` and `putchar`.
- The interpreter path pointed into a Nix store that does not exist on a normal machine, so it cannot be run directly. It does run through the system loader: `/lib64/ld-linux-x86-64.so.2 ./pocketflag <pin>`.
- A XOR-0x5a encoded string in `.rodata` decodes to `/proc/self/status`. This is an anti-debug check that reads `TracerPid`.

## Step 2: The PIN checks

`main` requires `argc == 2` and `strlen(argv[1]) == 4`. It then runs a series of checks on the four bytes `a0..a3`. Most arithmetic is written with mixed boolean-arithmetic (MBA) identities that look scary but simplify to something trivial, for example:

- `(a | b) - (a & b) + 2*(a & b)` is just `a + b`
- `(a | b) - (a & b)` is just `a ^ b`

After simplification the checks are:

| Check | Meaning | Result |
| --- | --- | --- |
| `a0 + a3 == 0x68` | sum of digits 1 and 4 | with `a0='6'` (0x36) gives `a3='2'` |
| `a1 ^ a2 == 3` | XOR of digits 2 and 3 | with `a2='4'` gives `a1='7'` |
| `a0 ^ a1 == 1` | XOR of digits 1 and 2 | `a0='6'` |
| `a2 == 0x34` | third digit is '4' | `a2='4'` |

Solving these gives **6742**. Each failed check adds a constant into the hidden key byte, so with the correct PIN the key byte stays at its clean value.

Two more derived values (computed from the PIN, again via MBA) are stored for the decryption step: `(a0^0x15) + (a1^0x2a)` and `(a2^0x4c) - (a3^0x11)`. For 6742 these are `0x40` and `0x55`.

A Collatz function is also called on the PIN data. It always returns 1, so it is a decoy.

## Step 3: The decryption stage

After the checks the program executes an `int3` and a `SIGTRAP` handler (installed with `sigaction`) acts as a tiny bytecode interpreter. The bytecode sits right after each `int3`, in two-byte (opcode, operand) pairs:

- one opcode XORs the current byte of a 26-byte table in `.data` with a value derived from the key and the stored values above,
- one opcode subtracts a value from that byte,
- one opcode advances the table index and loops back until all 26 bytes are processed.

When the loop finishes, the program prints the 26 table bytes with `putchar`. With a wrong key the bytes decrypt to noise, which is why the output looked random.

## Step 4: Anti-debug tricks

The handler and startup code also tamper with the key if they think they are being analysed:

- a `TracerPid` check in `/proc/self/status`,
- an `rdtsc` timing check between traps (single-stepping is slow),
- a scan of its own code for `0xcc` software breakpoints.

Because I did not debug the binary (static reading, then a plain run), none of these triggered.

## Step 5: Getting the flag

```
$ /lib64/ld-linux-x86-64.so.2 ./pocketflag 6742
cruXipher{0bfusc4t1on_g0D}
```

## Takeaways

- MBA expressions look intimidating but usually reduce to plain `+`, `^`, `&`, `|`. Simplify them before reasoning.
- "Random output" without an error message often means a silent key-corruption design rather than a hard reject.
- Running the binary normally (instead of under a debugger) avoids the anti-debug logic entirely.

**Flag: `cruXipher{0bfusc4t1on_g0D}`**
