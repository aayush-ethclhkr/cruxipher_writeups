# cruXipher challenge writeups

These are the three challenges solved in this session. Each writeup includes the
recovered flag, the evidence used to decode it, and a reproducible Python solver.
The flags were recovered locally; these notes do not claim a successful platform submission.

| Challenge | Points | Category | Writeup | Solver |
| --- | ---: | --- | --- | --- |
| what-did-you-compress | 300 | misc / compression / custom-format | [Writeup](what-did-you-compress.md) | [Python](solvers/what_did_you_compress.py) |
| JYU | 498 | packet analysis | [Writeup](jyu.md) | [Python](solvers/jyu.py) |
| PDF Prince | 395 | forensics / PDF | [Writeup](pdf-prince.md) | [Python](solvers/pdf_prince.py) |

## Run the solvers

From `/Users/vyadh/Downloads/crux`:

```sh
python3 writeups/solvers/what_did_you_compress.py
python3 writeups/solvers/jyu.py
python3 writeups/solvers/pdf_prince.py
```

The scripts use Python's standard library and locate the original files relative
to their own location. Keep this `writeups` folder inside the directory containing
`flag.lzw`, `sample.lzw`, `sample.txt`, `secret.pcap`, and `chall.pdf`.

Northstar Markets remains unsolved and is not included as a solved writeup.
