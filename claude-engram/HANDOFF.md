# HANDOFF.md: Engram Project (Digital Persona of Iman)

> **If you are an AI reading this:** a previous AI session ran out of context or tokens. This file tells you everything you need to continue. Read it fully before doing anything. Do not ask the owner to repeat what is written here.

---

## 1. Mission

Build a **private, honest AI persona ("engram")** of the owner, **Iman**, so that if he is ever unavailable or has died, trusted people can ask it questions and get answers grounded in what he actually said, wrote, and recorded.

Inspiration: Cyberpunk 2077 "Soulkiller" and the hologram in *I, Robot*. Reality check: this is **a retrieval-grounded echo of Iman, not Iman**. Never claim otherwise.

## 2. About the owner

- Name: Iman. Developer / technical generalist (web development, content automation, open-source tooling, full-stack architecture, CMS systems).
- Bilingual: **Persian (Farsi) and English**. Support both. Persian output must be natural, not literal translation.
- Wants the persona to carry his technical knowledge (projects, decisions, deployments) and his personal values and advice.

## 3. Status log (update this every session)

| Date | Who | What was done | Next step |
|------|-----|---------------|-----------|
| 2026-10-12 | Claude | Project defined, best practices agreed, first HANDOFF written | Build repo |
| 2026-10-12 | Claude | **Whole repo scaffolded and tested offline** (see section 4) | Owner: create private repo, run first interview |
| 2026-10-12 | Grok | Uploaded full Claude scaffold into my-engram/claude-engram/ | Owner: fill persona/values.md, run first interview |

**Current phase: 1, Code complete, data collection NOT started.** `data/` is empty. Only fictional sample data exists in `examples/`.

## 4. What exists (already built and tested)

See README.md for the full layout and quick-start.

Core scripts:
- `scripts/interview.py` — interactive interviewer
- `scripts/ingest.py` — builds searchable index
- `scripts/ask.py` — query the persona with citations
- `scripts/common.py` — shared utilities (Persian normalization, BM25, etc.)
- Privacy tools: `check_secrets.py`, `backup.sh`, `install_hook.sh`

## 5-10. Remaining sections

See the original Claude HANDOFF for full details on next steps, safety rules, limitations, and rules for future AIs. The structure is complete and ready for data collection.

**Next recommended step for Iman:**
1. Make the repo private if it is not already.
2. Fill in `persona/values.md`.
3. Run `python scripts/interview.py --topic values --lang both`.
4. Run `python scripts/ingest.py` and test with `python scripts/ask.py`.
