#!/usr/bin/env python3
"""Lock a single-file HTML page behind a password for static hosting.

The page is gzipped, then encrypted with AES-256-GCM using a key derived from
the password (PBKDF2-SHA256). copies/<ID>.json holds only the ciphertext; the
unlock page (index.html) decrypts it in the browser with WebCrypto. Wrong password = GCM tag fails.

Library for issue.py: lock(page_bytes, code) -> {s, i, n, c}.
"""
import base64, gzip, json, os, sys
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

ITER = 310_000  # ponytail: fixed cost; raise if the password ever needs to resist offline guessing harder

def lock(src, pw):
    """src: bytes of the page. Returns the JSON-ready dict {s, i, n, c}."""
    salt, iv = os.urandom(16), os.urandom(12)
    key = PBKDF2HMAC(hashes.SHA256(), 32, salt, ITER).derive(pw.encode())
    ct = AESGCM(key).encrypt(iv, gzip.compress(src, 9), None)
    b = lambda x: base64.b64encode(x).decode()
    return {"s": b(salt), "i": b(iv), "n": ITER, "c": b(ct)}
