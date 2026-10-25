# Paper CPU

**Points:** 400  
**Category:** Reverse Engineering / VM Bytecode  
**File:** `challenge.bin`

## Flag

```text
cruXipher{4456e680}
```

## Challenge

The fictional CPU has three 8-bit registers and 256 bytes of RAM. Initialize R0 
to `0x2a`, R1 and R2 to zero, and all RAM to zero. Execute `challenge.bin`, then 
format RAM addresses `0x40` through `0x43` as eight lowercase hexadecimal digits.

## Method

Use `kront.bin`, `vexx.bin`, `blip.bin`, and `snok.bin` to check candidate 
instruction semantics against all five supplied input/output pairs. The working 
interpretation uses the low opcode nibble as a register index:

| Opcodes | Operation |
|---|---|
| `00`–`02` | Load immediate into register |
| `10`–`12` | Add another register modulo 256; update zero flag |
| `20`–`22` | XOR immediate; update zero flag |
| `30`–`32` | Copy another register |
| `40` | If zero, jump by signed 8-bit relative offset |
| `50`–`52` | Store register to RAM |
| `60`–`62` | Load register from RAM |
| `70` | Halt |

All instructions other than halt consume an operand byte. The branch offset is 
relative to the position after reading that operand.

Executing the challenge with the register-copy interpretation produces 
`44 56 e6 80` in the four requested RAM locations.

The samples alone do not uniquely establish the `30`–`32` semantics: a 
compare-immediate alternative also matches those samples but yields a different 
candidate. The user's explicit acceptance confirms the register-copy result used 
here.

## Solution

The solver implements the virtual CPU, tests it against all sample binaries, and 
runs the challenge to extract the flag from RAM.

### Code

```python
"""Demonstrate that the supplied samples do not uniquely specify the CPU.
These are candidate interpretations, not a recovered instruction set.
"""
from pathlib import Path
ROOT = Path(__file__).resolve().parent

def run(name, value, interpretation):
    code = (ROOT / (name + '.bin')).read_bytes()
    registers, ram = [value, 0, 0], bytearray(256)
    pc, zero = 0, value == 0
    for _ in range(100000):
        op = code[pc]
        pc += 1
        if op == 0x70:
            return registers[0], ram
        arg = code[pc]
        pc += 1
        reg = op & 0xf
        if op in (0x00, 0x01, 0x02):
            registers[reg] = arg
        elif op in (0x10, 0x11, 0x12):
            registers[reg] = (registers[reg] + registers[arg]) & 255
            zero = registers[reg] == 0
        elif op in (0x20, 0x21, 0x22):
            registers[reg] ^= arg
            zero = registers[reg] == 0
        elif op in (0x30, 0x31, 0x32):
            if interpretation == 'register-copy':
                registers[reg] = registers[arg]
            elif interpretation == 'compare-immediate':
                zero = registers[reg] == arg
            else:
                raise ValueError(interpretation)
        elif op == 0x40:
            if zero:
                pc += arg if arg < 128 else arg - 256
        elif op in (0x50, 0x51, 0x52):
            ram[arg] = registers[reg]
        elif op in (0x60, 0x61, 0x62):
            registers[reg] = ram[arg]
        else:
            raise ValueError(f'Unknown opcode {op:02x}')
    raise RuntimeError('Step limit exceeded')

SAMPLES = [('kront', 0x2a, 0x4a), ('vexx', 0, 0),
           ('vexx', 1, 0xc3), ('blip', 0x2a, 0x7e), ('snok', 0xff, 0x55)]

if __name__ == '__main__':
    for mode in ('register-copy', 'compare-immediate'):
        for name, value, expected in SAMPLES:
            actual, _ = run(name, value, mode)
            assert actual == expected, (name, actual, expected)
        _, ram = run('challenge', 0x2a, mode)
        print(f'{mode}: all 5 examples pass; candidate cruXipher{{{ram[0x40:0x44].hex()}}}')
```

### Usage

```sh
python3 solve.py
```

### Output

```text
register-copy: all 5 examples pass; candidate cruXipher{4456e680}
compare-immediate: all 5 examples pass; candidate cruXipher{d5e6e6e6}
```

The accepted flag is `cruXipher{4456e680}` from the register-copy interpretation.
