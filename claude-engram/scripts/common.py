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
SEMANTIC_MIN = 0.5  # minimum cosine similarity for an embedding-only match
DEFAULT_MODELS = {"ollama": "qwen2.5:14b", "anthropic": "claude-sonnet-5-5"}

# Patterns that suggest a secret or sensitive number. Used by check_secrets.py.
SECRET_PATTERNS = {
    "api key (sk-...)": r"sk-[A-Za-z0-9_\-]{16,}",
    "aws access key": r"AKIA[0-9A-Z]{16}",
    "private key block": r"-----BEGIN [A-Z ]*PRIVATE KEY-----",
    "card-like number": r"\b(?:\d[ -]?){13,19}\b",
    "password/key assignment": r"(?i)\b(password|passwd|api[_ -]?key|secret|token)\b\s*[:=]\s*\S+",
    "persian password": r"(رمز\s*عبور|پسورد)\s*[:=]\s*\S+",
}


def find_secrets(text):
    """Return the names of the secret patterns found in text (never the secrets)."""
    return [name for name, pat in SECRET_PATTERNS.items() if re.search(pat, text)]


# ------------------------- text normalization / tokens -------------------------

_DIGITS = str.maketrans("۰۱۲۳۴۵۶۷۸۹٠١٢٣٤٥٦٧٨٩", "01234567890123456789")
_DIACRITICS = re.compile("[\u064B-\u065F\u0670\u0640]")


def normalize(text):
    """Unify Arabic/Persian letter variants, strip diacritics, ZWNJ -> space, lowercase."""
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
            tok = tok[:-1]  # crude plural folding: values -> value
        tokens.append(tok)
    return tokens


# --------------------------------- chunking ---------------------------------

def split_front_matter(text):
    m = re.match(r"^---\n(.*?)\n---\n?", text, re.S)
    meta = {}
    if m:
        for line in m.group(1).splitlines():
            if ":" in line:
                k, v = line.split(":", 1)
                meta[k.strip()] = v.strip()
        text = text[m.end():]
    return meta, text


def chunk_text(text, max_chars=900):
    """Split text into chunks of roughly max_chars, preferring paragraph breaks."""
    paragraphs = re.split(r"\n\s*\n", text.strip())
    chunks, current = [], ""
    for p in paragraphs:
        p = p.strip()
        if not p:
            continue
        if current and len(current) + len(p) + 2 > max_chars:
            chunks.append(current)
            current = p
        else:
            current = (current + "\n\n" + p).strip() if current else p
    if current:
        chunks.append(current)
    # If a single paragraph is too long, hard-split
    final = []
    for c in chunks:
        if len(c) <= max_chars:
            final.append(c)
        else:
            for i in range(0, len(c), max_chars):
                final.append(c[i:i + max_chars])
    return final


def build_chunks(data_dir):
    """Walk data_dir and return a list of chunk dicts."""
    data_dir = Path(data_dir)
    chunks = []
    for path in sorted(data_dir.rglob("*")):
        if not path.is_file() or path.suffix.lower() not in TEXT_EXTENSIONS:
            continue
        if path.name.startswith(("_", ".")) or path.name.lower().startswith("readme"):
            continue
        try:
            text = path.read_text(encoding="utf-8")
        except UnicodeDecodeError:
            continue
        meta, body = split_front_matter(text)
        date = meta.get("date") or (path.stem[:10] if re.match(r"\d{4}-\d{2}-\d{2}", path.stem) else "unknown")
        source = str(path.relative_to(data_dir))
        for i, piece in enumerate(chunk_text(body)):
            chunks.append({
                "id": f"{source}#{i}",
                "source": source,
                "date": date,
                "text": piece,
            })
    return chunks


# --------------------------------- retrieval ---------------------------------

class Retriever:
    def __init__(self, chunks):
        self.chunks = chunks
        self.N = len(chunks) or 1
        self.df = Counter()
        self.docs = []
        for c in chunks:
            toks = tokenize(c["text"])
            self.docs.append(Counter(toks))
            for t in set(toks):
                self.df[t] += 1

    def search(self, query, k=5):
        q = tokenize(query)
        if not q:
            return []
        scores = []
        for i, doc in enumerate(self.docs):
            score = 0.0
            for t in q:
                if t not in doc:
                    continue
                tf = doc[t]
                idf = math.log(1 + self.N / (1 + self.df[t]))
                score += (tf / (tf + 1.2)) * idf  # simple BM25-ish
            if score > 0:
                scores.append((score, i))
        scores.sort(reverse=True)
        return [(self.chunks[i], s) for s, i in scores[:k]]

    def search_hybrid(self, query, k=5, query_emb=None):
        """Keyword + optional embedding fusion (Reciprocal Rank Fusion)."""
        kw = self.search(query, k=k * 3)
        fused = {}
        for rank, (chunk, _) in enumerate(kw):
            idx = self.chunks.index(chunk)
            fused[idx] = fused.get(idx, 0.0) + 1 / (60 + rank)
        if query_emb is not None:
            try:
                sims = []
                for c in self.chunks:
                    emb = c.get("emb")
                    if not emb:
                        sims.append(-1)
                        continue
                    # cosine
                    dot = sum(a * b for a, b in zip(query_emb, emb))
                    na = math.sqrt(sum(a * a for a in query_emb)) or 1
                    nb = math.sqrt(sum(b * b for b in emb)) or 1
                    sims.append(dot / (na * nb))
                top = sorted(range(len(sims)), key=lambda i: -sims[i])[: k * 3]
                for rank, i in enumerate(top):
                    if sims[i] >= SEMANTIC_MIN:
                        fused[i] = fused.get(i, 0.0) + 1 / (60 + rank)
            except RuntimeError:
                pass  # embeddings unavailable -> keyword-only
        ranked = sorted(fused.items(), key=lambda kv: -kv[1])[:k]
        return [(self.chunks[i], score) for i, score in ranked]


# ------------------------------- model backends -------------------------------

def _post(url, payload, headers=None, timeout=300):
    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json", **(headers or {})},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        raise RuntimeError(f"HTTP {e.code}: {e.read().decode('utf-8', 'replace')[:500]}")
    except urllib.error.URLError as e:
        raise RuntimeError(f"Connection failed: {e.reason}")


def _ollama_host():
    return os.environ.get("OLLAMA_HOST", "http://localhost:11434").rstrip("/")


def chat(provider, model, system, messages, max_tokens=900):
    model = model or DEFAULT_MODELS[provider]
    if provider == "ollama":
        data = _post(f"{_ollama_host()}/api/chat", {
            "model": model,
            "stream": False,
            "messages": [{"role": "system", "content": system}] + messages,
            "options": {"num_predict": max_tokens},
        })
        return data["message"]["content"].strip()
    if provider == "anthropic":
        key = os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("Set ANTHROPIC_API_KEY to use the anthropic provider.")
        data = _post(
            "https://api.anthropic.com/v1/messages",
            {"model": model, "max_tokens": max_tokens, "system": system, "messages": messages},
            {"x-api-key": key, "anthropic-version": "2023-06-01"},
        )
        return "".join(b.get("text", "") for b in data["content"] if b.get("type") == "text").strip()
    raise ValueError(f"Unknown provider: {provider}")


def embed(texts, model="nomic-embed-text", batch=16):
    out = []
    for i in range(0, len(texts), batch):
        data = _post(f"{_ollama_host()}/api/embed", {"model": model, "input": texts[i:i + batch]})
        out.extend(data["embeddings"])
    return out
