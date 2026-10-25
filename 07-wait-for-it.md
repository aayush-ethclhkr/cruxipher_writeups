# Wait For It

**Points:** 499  
**Category:** Packet Analysis / Timing Attack  
**File:** `capture.pcap`

## Flag

```text
cruXipher{T1M1NG_1S_3V3RYTH1NG}
```

**Note:** The original answer submitted was lowercase, `cruXipher{t1m1ng_1s_3v3ryth1ng}`, 
and the user replied **wrong**. There is no recorded acceptance of the uppercase 
candidate. Morse decoding conventionally uses uppercase letters and does not 
itself encode letter case, so the repeated timing message supports the payload 
but cannot establish the platform's required capitalization.

## Challenge

The capture contains IRC traffic with a hidden timing-based channel.

## Finding the Hidden Channel

The capture contains IRC traffic. The analysis selected server-to-client TCP 
packets from source port `6667` to destination port `57474` whose payload 
contains `PRIVMSG`. It extracted their PCAP timestamps in microseconds.

The useful signal is the timing of the selected messages. Closely spaced packets 
form bursts, and the durations of those bursts can be interpreted as Morse dots 
and dashes. The flags visible in the chat text are decoys.

## Decoding the Timing

The solver uses these thresholds for this capture:

| Measurement | Interpretation |
|---|---|
| Interpacket gap greater than 20,000 microseconds | Start a new burst |
| Burst duration greater than 200,000 microseconds | Dash |
| Burst duration at most 200,000 microseconds | Dot |
| Gap between bursts greater than 700,000 microseconds | Message/word separator |
| Otherwise, gap greater than 200,000 microseconds | Letter separator |
| Shorter gap | Continue the same letter |

A burst's duration is its last packet timestamp minus its first packet timestamp. 
The gap following it is the next burst's first timestamp minus the preceding 
burst's last timestamp.

Mapping the resulting dot/dash groups through the Morse alphabet, including 
`..--.-` for underscore, yields the same payload twice:

```text
T1M1NG_1S_3V3RYTH1NG
T1M1NG_1S_3V3RYTH1NG
```

The repetition is a consistency check on the timing decode. Wrap the payload in 
the challenge prefix to obtain the uppercase candidate above.

## Solution

The solver extracts IRC packet timing from the PCAP, interprets burst durations 
as Morse code, and decodes the message.

### Code

```python
"""Recover Morse encoded in IRC packet burst durations. Standard library only."""
from pathlib import Path
import struct
import sys

CAPTURE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path('capture.pcap')
MORSE = dict(pair.split() for pair in (
    '.- A|-... B|-.-. C|-.. D|. E|..-. F|--. G|.... H|.. I|.--- J|'
    '-.- K|.-.. L|-- M|-. N|--- O|.--. P|--.- Q|.-. R|... S|- T|'
    '..- U|...- V|.-- W|-..- X|-.-- Y|--.. Z|----- 0|.---- 1|'
    '..--- 2|...-- 3|....- 4|..... 5|-.... 6|--... 7|---.. 8|----. 9|..--.- _'
).split('|'))

def timestamps(capture):
    raw = capture.read_bytes()
    assert raw[:4] == bytes.fromhex('d4c3b2a1'), 'Expected little-endian microsecond PCAP'
    position = 24
    while position < len(raw):
        seconds, microseconds, size, _ = struct.unpack_from('<IIII', raw, position)
        position += 16
        frame = raw[position:position+size]
        position += size
        if frame[12:14] != b'\x08\x00':
            continue
        ip = frame[14:]
        if ip[9] != 6:
            continue
        tcp = ip[(ip[0] & 15)*4:]
        source, destination = struct.unpack_from('!HH', tcp)
        payload = tcp[(tcp[12] >> 4)*4:]
        if source == 6667 and destination == 57474 and b'PRIVMSG' in payload:
            yield seconds*1000000 + microseconds

def recover(times):
    bursts = []
    start = previous = times[0]
    for current in times[1:]:
        if current-previous > 20000:
            bursts.append((previous-start, current-previous))
            start = current
        previous = current
    bursts.append((previous-start, 0))
    encoded = ''
    for duration, gap in bursts:
        encoded += '-' if duration > 200000 else '.'
        if gap > 700000:
            encoded += ' / '
        elif gap > 200000:
            encoded += ' '
    words = [''.join(MORSE[symbol] for symbol in word.split())
             for word in encoded.split('/')]
    return encoded, words

if __name__ == '__main__':
    encoded, repetitions = recover(list(timestamps(CAPTURE)))
    print('Morse:', encoded)
    print('Decoded:', repetitions)
    assert len(repetitions) == 2 and repetitions[0] == repetitions[1]
    print('Flag: cruXipher{' + repetitions[0] + '}')
```

### Usage

```sh
python3 solve.py capture.pcap
```

### Output

```text
Decoded: ['T1M1NG_1S_3V3RYTH1NG', 'T1M1NG_1S_3V3RYTH1NG']
Flag: cruXipher{T1M1NG_1S_3V3RYTH1NG}
```

Platform acceptance remains unconfirmed.
