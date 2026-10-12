#!/usr/bin/env python3
"""
ingest.py - turn everything in data/ into a searchable index (index/chunks.json).

Reads every .md and .txt file under data/ (interviews, writings, technical notes),
splits it into chunks, and writes them to the index. Run it again whenever you add data.

  python scripts/ingest.py                       # keyword (BM25) index, works offline
  python scripts/ingest.py --embed               # also add embeddings (needs Ollama + an embed model)
  python scripts/ingest.py --data other_folder   # index a different folder

Files whose names start with "_" or "." and README files are skipped.
Audio and other non-text files are ignored (see HANDOFF.md for voice-clone plans).
"""

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from common import ROOT, build_chunks, embed, find_secrets


def main():
    ap = argparse.ArgumentParser(description="Build the Engram search index.")
    ap.add_argument("--data", default=str(ROOT / "data"), help="folder to index (default: data/)")
    ap.add_argument("--out", default=str(ROOT / "index" / "chunks.json"), help="index output path")
    ap.add_argument("--embed", action="store_true", help="add embeddings via Ollama")
    ap.add_argument("--embed-model", default="nomic-embed-text")
    args = ap.parse_args()

    data_dir = Path(args.data)
    if not data_dir.is_dir():
        sys.exit(f"Data folder not found: {data_dir}")

    chunks = build_chunks(data_dir)
    if not chunks:
        sys.exit(f"No .md/.txt content found in {data_dir}. Run scripts/interview.py first.")

    flagged = sorted({c["source"] for c in chunks if find_secrets(c["text"])})
    if flagged:
        print("WARNING: possible secrets or ID numbers in these files (run scripts/check_secrets.py):")
        for f in flagged:
            print(f"  - {f}")

    embed_model = None
    if args.embed:
        print(f"Embedding {len(chunks)} chunks with {args.embed_model} ...")
        try:
            vectors = embed([c["text"] for c in chunks], args.embed_model)
        except RuntimeError as e:
            sys.exit(f"Embedding failed: {e}\nIs Ollama running and the model pulled? "
                     f"(ollama pull {args.embed_model})")
        for c, v in zip(chunks, vectors):
            c["emb"] = v
        embed_model = args.embed_model

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps({
        "version": 1,
        "built": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "embed_model": embed_model,
        "chunks": chunks,
    }, ensure_ascii=False), encoding="utf-8")

    files = len({c["source"] for c in chunks})
    print(f"Indexed {len(chunks)} chunks from {files} files -> {out}")


if __name__ == "__main__":
    main()
