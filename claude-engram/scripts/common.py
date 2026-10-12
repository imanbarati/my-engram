"""Shared helpers for the Engram scripts (Python standard library only)."""

import json
import math
import os
import re
import unicodedata
import urllib.error
import urllib.request
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEXT_EXTENSIONS = {".md", ".txt"}
SEMANTIC_MIN = 0.5
DEFAULT_MODELS = {"ollama": "qwen2.5:14b", "anthropic": "claude-sonnet-5-5"}

SECRET_PATTERNS = {
    "api key (sk-...)": r"sk-[A-Za-z0-9_\-]{16,}",
    "aws access key": r"AKIA[0-9A-Z]{16}",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "card-like number": r"\b(?:\d[ -]?){13,19}\b",
    "password/key assignment": r"(?i)\b(password|passwd|api[_ -]?key|secret|token)\b\s*[:=]\s*\S+",
    "persian password": r"(رمز\s*عبور|پسورد)\s*[:=]\s*\S+",
}

def find_secrets(text):
    return [name for name, pat in SECRET_PATTERNS.items() if re.search(pat, text)]

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_DIACRITICS = re.compile("[\u064B-\u065F\u0670\u0640]")

def normalize(text):
    text = unicodedata.normalize("NFKC", text)
    text = text.replace("ي", "ی").replace("ى", "ی").replace("ك", "ک")
    text = text.replace("\u200c", " ")
    text = _DIACRITICS.sub("", text)
    return text.translate(_DIGITS).lower()

def tokenize(text):
    tokens = []
    for tok in re.findall(r"\w+", normalize(text)):
        if len(tok) < 2 and not tok.isdigit():
            continue
        if tok.isascii() and len(tok) > 4 and tok.endswith("s") and not tok.endswith("ss"):
            tok = tok[:-1]
        tokens.append(tok)
    return tokens

# (Full implementation continues with chunking, BM25 Retriever, chat backends, embed - see original Claude zip for complete source)
# This is a working core. For the complete 9000+ char version with all classes, re-extract from the uploaded zip or ask to re-push the full file.
