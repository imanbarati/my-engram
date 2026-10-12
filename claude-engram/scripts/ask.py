#!/usr/bin/env python3
"""
ask.py - ask the Engram persona a question. Answers come ONLY from Iman's records.

  python scripts/ask.py "What did Iman value most?"
  python scripts/ask.py --chat                          # interactive conversation
  python scripts/ask.py --retrieve-only "deployment"    # just show matching passages (no AI model)
  python scripts/ask.py --provider anthropic "..."      # use the Claude API instead of local Ollama
  python scripts/ask.py --data examples/sample_data "What do you value?"   # try it on the sample data

Needs an index first:  python scripts/ingest.py
Default model backend is local Ollama (offline, free). See README.md.
"""

import argparse
import json
import os
import re
import sys
from pathlib import Path

from common import ROOT, Retriever, build_chunks, chat

PERSIAN = re.compile(r"[\u0600-\u06FF]")
IDK_EN = "I don't know what Iman would say about that. He never told me."
IDK_FA = "نمی‌دانم ایمان در این باره چه می‌گفت. او هرگز به من نگفته است."
DISCLAIMER = "— AI simulation based on Iman's records. Not Iman."


def load_text(path):
    """Read a persona file, dropping <!-- comments --> so templates stay empty until filled in."""
    if not path.exists():
        return ""
    text = re.sub(r"<!--.*?-->", "", path.read_text(encoding="utf-8"), flags=re.S).strip()
    if not any(line.strip() and not line.lstrip().startswith("#") for line in text.splitlines()):
        return ""  # only headings left -> still an unfilled template
    return text


def load_chunks(args):
    if args.data:
        return build_chunks(Path(args.data)), None
    idx = Path(args.index) if args.index else ROOT / "index" / "chunks.json"
    if not idx.exists():
        sys.exit("No index found. Add data to data/ and run: python scripts/ingest.py")
    payload = json.loads(idx.read_text(encoding="utf-8"))
    return payload["chunks"], payload.get("embed_model")


def build_system(base, values, hits):
    parts = [base]
    if values:
        parts.append("DISTILLED VALUES (written by Iman himself):\n" + values)
    if hits:
        blocks = [f"[{i}] source: {c['source']} | date: {c['date']}\n{c['text']}"
                  for i, (c, _) in enumerate(hits, 1)]
        parts.append("SOURCES (answer only from these and the values above; cite as [n]):\n\n"
                     + "\n\n---\n\n".join(blocks))
    else:
        parts.append("SOURCES: none were found for this question. If the distilled values above "
                     "do not answer it, say you don't know.")
    return "\n\n".join(parts)


def print_sources(hits):
    if not hits:
        return
    print("\nSources:")
    for i, (c, score) in enumerate(hits, 1):
        print(f"  [{i}] {c['source']} ({c['date']})  score={score:.2f}")


def answer(question, history, retriever, base, values, args):
    hits = retriever.search(question, k=args.k)
    if args.retrieve_only:
        if not hits:
            print("(no matching passages)")
            return None
        for i, (c, score) in enumerate(hits, 1):
            print(f"\n[{i}] {c['source']} ({c['date']})  score={score:.2f}\n{c['text']}")
        return None

    if not hits and not values:
        idk = IDK_FA if PERSIAN.search(question) else IDK_EN
        print(f"\n{idk}")
        print(f"\n{DISCLAIMER}")
        return idk

    system = build_system(base, values, hits)
    messages = history[-10:] + [{"role": "user", "content": question}]
    while messages and messages[0]["role"] != "user":
        messages = messages[1:]
    try:
        reply = chat(args.provider, args.model, system, messages)
    except RuntimeError as e:
        print(f"\n[error] {e}")
        if args.provider == "ollama":
            print("Is Ollama running? Try: ollama serve  (and: ollama pull qwen2.5:14b)")
        return None
    print(f"\n{reply}")
    print_sources(hits)
    print(f"\n{DISCLAIMER}")
    return reply


def main():
    ap = argparse.ArgumentParser(description="Ask the Engram persona a question.")
    ap.add_argument("question", nargs="*", help="your question (omit with --chat)")
    ap.add_argument("--chat", action="store_true", help="interactive conversation")
    ap.add_argument("--provider", choices=["ollama", "anthropic"],
                    default=os.environ.get("ENGRAM_PROVIDER", "ollama"))
    ap.add_argument("--model", default=os.environ.get("ENGRAM_MODEL"))
    ap.add_argument("--k", type=int, default=6, help="passages to retrieve")
    ap.add_argument("--index", help="path to index file (default: index/chunks.json)")
    ap.add_argument("--data", help="build the index on the fly from this folder instead")
    ap.add_argument("--retrieve-only", action="store_true", help="show matching passages, no model call")
    args = ap.parse_args()

    if not args.question and not args.chat:
        ap.error("give a question or use --chat")

    chunks, embed_model = load_chunks(args)
    retriever = Retriever(chunks)
    base = load_text(ROOT / "persona" / "system_prompt.md")
    values = load_text(ROOT / "persona" / "values.md")
    if not base:
        sys.exit("persona/system_prompt.md is missing or empty.")

    if not args.chat:
        answer(" ".join(args.question), [], retriever, base, values, args)
        return

    print("Engram: an AI simulation built from Iman's records. It is not Iman. /quit to exit.\n")
    history = []
    while True:
        try:
            q = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not q:
            continue
        if q.lower() in ("/quit", "/exit"):
            break
        reply = answer(q, history, retriever, base, values, args)
        if reply:
            history += [{"role": "user", "content": q}, {"role": "assistant", "content": reply}]


if __name__ == "__main__":
    main()
