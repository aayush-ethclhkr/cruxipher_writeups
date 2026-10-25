# Boxy Proxy

**Points:** 500  
**Category:** Web / Cryptography  
**URL:** `https://proxy.cruxipher.crux-bphc.com/`  
**File:** `ca_cert.pem`

## Flag

```text
cruXipher{som4h4W_b4tt4r_th4n_eMud4ra}
```

## Challenge

Boxy Proxy implements a small, TLS-like protocol over raw TCP. A client connects to a registered proxy node, asks for an upstream, and starts an authenticated X25519 key exchange.

## Overview

The clean solution is to **impersonate the upstream instead of relaying to it**:

1. Register a public TCP listener with `/register-proxy`.
2. Recover the private key corresponding to the supplied CA certificate.
3. Return the trusted CA certificate and your own X25519 public key.
4. Sign that X25519 key with the recovered CA private key.
5. Compute the X25519 shared secret, derive the AES key using the supplied HKDF hint, and decrypt the client's message.

No upstream connection is required.

## Reconnaissance

The landing page advertises a custom proxy protocol. The site's custom 404 response points toward the useful endpoint:

```text
Sorry, we couldn't find that page! Perhaps you're looking for /register-proxy ?
```

Registration requires:

```json
{"host":"PUBLIC_HOST","port":9000}
```

When a reachable listener is registered, the challenge server connects and sends the requested upstream address, then immediately starts its custom handshake.

## Protocol Layout

Every handshake message is framed with a **4-byte big-endian length**, followed by exactly that many bytes.

The client sends four frames:

| Frame | Size | Meaning |
|---|---:|---|
| 0 | 459 bytes | Plaintext greeting/protocol description |
| 1 | 451 bytes | Client RSA public key in PEM format |
| 2 | 32 bytes | Client X25519 public key |
| 3 | 256 bytes | RSA-PSS signature over frame 2 |

The expected server response has three frames:

| Frame | Meaning |
|---|---|
| 0 | X.509 certificate in PEM format |
| 1 | Server X25519 public key, 32 bytes |
| 2 | RSA-PSS/SHA-256 signature over the server X25519 public key |

The client trusts the CA represented by the provided `ca_cert.pem`.

## Recovering the CA Private Key

The supplied certificate contains a 2048-bit RSA public key with `e = 65537`. A FactorDB lookup for this challenge's modulus returned a complete factorization into two 1024-bit factors, `p` and `q`.

With the factors known, reconstruct the RSA private exponent using Carmichael's lambda:

```text
λ(n) = lcm(p-1, q-1)
d = e^(-1) mod λ(n)
```

## Forging the Upstream Handshake

1. Generate an ephemeral X25519 key pair
2. Sign the public key with the recovered CA private key using RSA-PSS/SHA-256
3. Return three length-prefixed frames: CA certificate, X25519 public key, signature
4. Compute the X25519 shared secret

## Deriving the AES Key and Decrypting

The update supplies the exact KDF:

```python
def derive_aes_key(shared_secret):
    return HKDF(
        algorithm=hashes.SHA256(),
        length=32,
        salt=None,
        info=b"handshake encryption",
    ).derive(shared_secret)
```

After the handshake, the client sends one encrypted frame with layout:

```text
12-byte AES-GCM nonce || ciphertext || 16-byte authentication tag
```

## Solution

See the full solver in the complete code repository.

### Usage

```bash
python3 solve.py 9000
```

Then register the public address:

```bash
curl -k -X POST \
  'https://proxy.cruxipher.crux-bphc.com/register-proxy' \
  -H 'Content-Type: application/json' \
  --data '{"host":"YOUR_PUBLIC_HOST","port":9000}'
```

### Output

```text
Shared secret: 0591dc6c02dd7be0f8dc1d40efe85999abfbfbd8b38d5e566dc46a512c734c5b
AES key:       a877b6c980c878c88bf03ad7ee342a9dfd9a543239243d78602eff4584c24e22
Plaintext:     Hello Bob! No one can intercept us now MWAHAHAHA..... or can they?.... cruXipher{som4h4W_b4tt4r_th4n_eMud4ra}
FLAG: cruXipher{som4h4W_b4tt4r_th4n_eMud4ra}
```

## Security Takeaway

The key exchange only remains secure while the trust anchor's private key remains secret. Once the CA key is recovered, certificate validation no longer distinguishes the real upstream from an attacker.
