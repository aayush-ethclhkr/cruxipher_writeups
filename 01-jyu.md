# JYU

**Points:** 498  
**Category:** Packet Analysis  
**File:** `secret.pcap`

## Flag

```text
cruXipher{v1m_netw0rk_c4ptur3}
```

## Challenge

> just a pcap file patented in 1936

## Identify the Session

`secret.pcap` is a little-endian, microsecond-resolution pcap with DLT_NULL
link-layer encapsulation. Each packet begins with a four-byte loopback header,
followed by an IPv4 packet. The capture contains 308 packets.

The relevant TCP conversation is:

```text
127.0.0.1:56243 <-> 127.0.0.1:9999
```

A quick inspection with tcpdump shows terminal escape sequences rather than a
normal application protocol:

```sh
tcpdump -nn -r secret.pcap -X
```

The server opens an alternate terminal screen and displays:

```text
"flag.txt" [New]
```

Later it displays `-- INSERT --`, cursor movements, individual typed characters,
and a final write status. This is a Vim editing session transported over TCP.

## Reconstruct the Saved Text

Reading every printable client byte as flag text would include editor commands,
mistakes, and deleted characters. Replaying the server's terminal output makes
the actual saved line clear.

The user first presses `i` to enter insert mode and types:

```text
jpgQcld.p?k1m{b.y,prt
```

After Escape, the commands `b` and `cw` change the final word. The server moves
the cursor to row 1, column 19 and clears to the end of the line, leaving the
first 18 characters:

```text
jpgQcld.p?k1m{b.y,
```

The replacement text initially typed is:

```text
0pt{jmfoy.p
```

Seven backspaces remove `jmfoy.p`, leaving `0pt{`. The final insertion is:

```text
j4lygp3+
```

The user exits insert mode and executes `:wq`. The saved line is therefore:

```text
jpgQcld.p?k1m{b.y,0pt{j4lygp3+
```

It is 30 characters long. The server's confirmation, `1L, 31B written`, agrees
with those 30 ASCII characters plus the terminating newline.

## Undo the Keyboard Layout

The year in the description points to the Dvorak keyboard layout. The recovered
text is what the intended QWERTY key positions produce under Dvorak.

Map each saved character from its Dvorak position back to the corresponding
QWERTY key, including shifted punctuation:

| Captured character | Intended character |
| --- | --- |
| `j` | `c` |
| `p` | `r` |
| `g` | `u` |
| `Q` | `X` |
| `?` | `{` |
| `{` | `_` |
| `+` | `}` |

Applying that mapping to the complete saved line gives:

```text
cruXipher{v1m_netw0rk_c4ptur3}
```

The Vim commands must be handled before applying this character mapping; they
are editing actions, not characters in the saved file.

## Solution

The solver parses the pcap using the standard library, reassembles the server 
payloads by TCP sequence number, replays the terminal controls used by this 
capture, and translates the saved first line.

See `solvers.py` for the complete implementation.

### Usage

```sh
python3 solvers.py
```

### Output

```text
Saved line: jpgQcld.p?k1m{b.y,0pt{j4lygp3+
cruXipher{v1m_netw0rk_c4ptur3}
```
