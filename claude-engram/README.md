# Engram

A **private, honest AI persona of Iman**, built from his own interviews, writings, and technical notes, so that trusted people can ask it questions if he is ever unavailable.

It is an **echo built from records, not Iman**. It answers only from what he recorded, cites its sources, and says "I don't know" when the records are silent.

> **Keep this repository PRIVATE.** It will contain personal material. Read `access/INSTRUCTIONS_FOR_TRUSTED_PERSON.md` and `HANDOFF.md`.

## How it works

```
interview.py  ->  data/interviews/*.md   (your words, dated, tagged [stated])
                         |
ingest.py     ->  index/chunks.json      (searchable chunks; rebuildable)
                         |
ask.py        ->  finds relevant passages -> AI model answers ONLY from them, with citations
```

Search is keyword-based (BM25) and works fully offline, with Persian and English support. Optional embeddings (via Ollama) add meaning-based search.

## Quick start

Requires **Python 3.8+**. No packages to install.

```bash
# 1. Pick a model backend (default: local, free, offline)
#    Install Ollama (https://ollama.com), then:
ollama pull qwen2.5:14b

# 2. Record yourself: the AI asks, you answer. Saved to data/interviews/
python scripts/interview.py --list
python scripts/interview.py --topic values --lang both

# 3. Build the index (re-run whenever you add data)
python scripts/ingest.py

# 4. Ask the persona
python scripts/ask.py "What did Iman value most?"
python scripts/ask.py --chat
```

Try it first on the fictional sample data (nothing personal):

```bash
python scripts/ask.py --data examples/sample_data --retrieve-only "what do you value"
python -m unittest discover -s tests
```

Use the Claude API instead of Ollama: `export ANTHROPIC_API_KEY=...` and add `--provider anthropic`.

## Layout

```
HANDOFF.md        status + instructions for any AI continuing this project
persona/          system_prompt.md (rules), values.md (fill in yourself)
data/             interviews/ writings/ audio/ technical/   <- your material (ENCRYPT THIS)
scripts/          interview.py ingest.py ask.py check_secrets.py backup.sh install_hook.sh common.py
access/           instructions for the trusted person
examples/         fictional sample data for testing
tests/            offline tests
index/            generated search index (git-ignored)
```

## Privacy and safety checklist

- [ ] Repo is **private**.
- [ ] `data/` is encrypted: see `.gitattributes.example` (git-crypt), or use `scripts/backup.sh` for encrypted archives.
- [ ] Install the secret-scanning hook: `git init && sh scripts/install_hook.sh`.
- [ ] No passwords, keys, ID or bank numbers, exact locations, or other people's private details in `data/`. Run `python scripts/check_secrets.py` before committing.
- [ ] `access/INSTRUCTIONS_FOR_TRUSTED_PERSON.md` filled in, and the key stored **outside** the repo.
- [ ] Encrypted backups in at least two places, in different countries.

## Limits

- Quality depends on how much you record. Hours of interviews matter more than the model.
- The persona never claims to be Iman, and won't invent opinions. That is deliberate.
- Recorded letters, messages, a will, and project handoff notes are more reliable than any AI. Make those too.
