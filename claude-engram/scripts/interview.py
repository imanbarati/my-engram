#!/usr/bin/env python3
"""
interview.py - AI interviewer that records Iman's answers as dated [stated] transcripts.

  python scripts/interview.py --list
  python scripts/interview.py --topic values --lang both
  python scripts/interview.py --topic technical --lang en

Saves to data/interviews/YYYY-MM-DD-topic.md
Supports Ollama (default) or Anthropic API.
"""

import argparse
import datetime as dt
import os
import re
import sys
from pathlib import Path

from common import ROOT, chat, find_secrets

TOPICS = {
    "values": "Personal values, what matters most, advice for younger people, what to remember.",
    "technical": "Technical decisions, projects, deployments, tools, architecture choices.",
    "life": "Life story, important events, family, relationships (only what he chooses to share).",
    "work": "Work history, lessons learned, what he would do differently.",
    "free": "Open conversation – ask whatever feels important today.",
}

SYSTEM = """You are a careful, warm interviewer helping Iman record his thoughts for a future AI persona of himself.
Rules:
- Ask ONE clear question at a time.
- Prefer open questions.
- Switch language to match the user (Persian or English).
- Never invent answers for him.
- After each answer, briefly acknowledge and ask the next question.
- If he says he is done, thank him and stop.
- Keep questions grounded in the topic: {topic_desc}
"""


def main():
    ap = argparse.ArgumentParser(description="Interview Iman and save transcripts.")
    ap.add_argument("--topic", choices=list(TOPICS), default="values")
    ap.add_argument("--lang", choices=["en", "fa", "both"], default="both")
    ap.add_argument("--provider", choices=["ollama", "anthropic"],
                    default=os.environ.get("ENGRAM_PROVIDER", "ollama"))
    ap.add_argument("--model", default=os.environ.get("ENGRAM_MODEL"))
    ap.add_argument("--list", action="store_true", help="list available topics")
    args = ap.parse_args()

    if args.list:
        for k, v in TOPICS.items():
            print(f"  {k:12} {v}")
        return

    out_dir = ROOT / "data" / "interviews"
    out_dir.mkdir(parents=True, exist_ok=True)
    today = dt.date.today().isoformat()
    out_path = out_dir / f"{today}-{args.topic}.md"

    system = SYSTEM.format(topic_desc=TOPICS[args.topic])
    if args.lang == "fa":
        system += "\nSpeak only in natural Persian."
    elif args.lang == "en":
        system += "\nSpeak only in English."
    else:
        system += "\nMatch the language the user writes in (Persian or English)."

    print(f"Interview topic: {args.topic}")
    print(f"Saving to: {out_path}")
    print("Type /quit when finished.\n")

    history = []
    # Seed first question
    try:
        first = chat(args.provider, args.model, system,
                     [{"role": "user", "content": "Start the interview with a good first question."}])
    except RuntimeError as e:
        print(f"[error] {e}")
        return
    print(f"AI> {first}\n")

    lines = [f"# Interview – {args.topic}\n", f"Date: {today}\n", f"Topic: {args.topic}\n\n"]

    while True:
        try:
            ans = input("you> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break
        if not ans:
            continue
        if ans.lower() in ("/quit", "/exit", "done", "تمام"):
            break

        secrets = find_secrets(ans)
        if secrets:
            print(f"[warning] possible secrets detected ({', '.join(secrets)}). Consider redacting.")

        lines.append(f"Q: {first if not history else history[-1]['content']}\n")
        lines.append(f"A: [stated] {ans}\n\n")

        history += [{"role": "assistant", "content": first if not history else history[-1]["content"]},
                    {"role": "user", "content": ans}]

        try:
            next_q = chat(args.provider, args.model, system, history[-6:])
        except RuntimeError as e:
            print(f"[error] {e}")
            break
        print(f"\nAI> {next_q}\n")
        first = next_q  # for next round label

    out_path.write_text("".join(lines), encoding="utf-8")
    print(f"\nSaved {out_path}")


if __name__ == "__main__":
    main()
