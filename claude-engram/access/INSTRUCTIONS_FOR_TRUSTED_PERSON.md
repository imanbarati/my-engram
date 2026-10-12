# For the trusted person

> Fill in the bracketed parts before storing this file. Keep a printed copy somewhere safe too.

**Owner:** Iman
**Trusted person:** [NAME]   **Backup trusted person:** [NAME]
**How to reach the owner's family / legal contact:** [FILL IN]

## What this is

This repository holds an **AI simulation** of Iman. It is built from interviews, writings, and notes that he recorded himself. It can answer questions about what he said and thought, and it can explain his technical projects.

It is **not Iman**. It cannot know anything he did not record. It will say "I don't know" when the records are silent. His own letters, recordings, and messages are the real legacy; this tool is a supplement.

## Who may use it

[FILL IN: e.g. "Family members and the trusted person only. Do not make it public. Do not share the key with anyone else."]

## What you need

1. A computer (Windows, macOS, or Linux) with **Python 3.8 or newer**.
2. This repository (a copy is on GitHub, **private**, and in the encrypted backups).
3. The **decryption key or passphrase**. Location: [FILL IN, e.g. "sealed envelope with the lawyer", "password manager entry named ..."]. It is never stored in the repository.
4. For AI answers: **Ollama** (free, runs offline): https://ollama.com. Then run `ollama pull qwen2.5:14b`. A computer with 16 GB RAM is recommended. Without this, you can still search the records (step 5).

## Steps

1. **Get the repo:** `git clone <repo-url>` (or unzip the backup).
2. **Decrypt the data:**
   - If the repo uses git-crypt: `git-crypt unlock /path/to/engram.key`
   - If you have an encrypted backup: `age -d -o backup.tar engram-backup-DATE.tar.age` (or `gpg -d -o backup.tar engram-backup-DATE.tar.gpg`), then `tar -xf backup.tar`
3. **Build the search index:** `python scripts/ingest.py`
4. **Ask a question:** `python scripts/ask.py "What did Iman think about <topic>?"`
   or have a conversation: `python scripts/ask.py --chat`
5. **No AI model available?** You can still read the matching passages from his own words: `python scripts/ask.py --retrieve-only "<keywords>"`, or open the files in `data/` directly.

## If something has gone wrong

- **GitHub account or repo is gone:** restore from the encrypted backups (`scripts/backup.sh` creates them). Locations: [FILL IN, ideally two places in two different countries].
- **The AI model is no longer available:** the data in `data/` is plain text and stays usable. Any future AI can read it. See `HANDOFF.md`, which is written for an AI to continue the project.
- **Ollama or the model won't run:** use `--retrieve-only`, or ask any AI assistant to help, giving it `HANDOFF.md` and `README.md`.

## Please be gentle

The answers may be moving or painful to hear. You do not have to use it. Take it slowly, and lean on the real people around you.
