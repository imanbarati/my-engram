#!/usr/bin/env bash
# Makes an ENCRYPTED backup of data/, persona/, and access/ (not the rebuildable index).
# Usage: scripts/backup.sh [output-name]
# Needs 'age' (preferred) or 'gpg'. You will be asked for a passphrase: store it somewhere
# OUTSIDE this repo and give it to your trusted person.
set -euo pipefail
cd "$(dirname "$0")/.."
OUT="${1:-engram-backup-$(date +%F).tar}"
tar -cf "$OUT" data persona access HANDOFF.md README.md scripts
if command -v age >/dev/null 2>&1; then
  age -p -o "$OUT.age" "$OUT"
  rm "$OUT"
  echo "Encrypted backup: $OUT.age   (decrypt: age -d -o backup.tar $OUT.age)"
elif command -v gpg >/dev/null 2>&1; then
  gpg --symmetric --cipher-algo AES256 -o "$OUT.gpg" "$OUT"
  rm "$OUT"
  echo "Encrypted backup: $OUT.gpg   (decrypt: gpg -d -o backup.tar $OUT.gpg)"
else
  rm "$OUT"
  echo "Install 'age' or 'gpg' first. Refusing to leave an unencrypted backup." >&2
  exit 1
fi
echo "Copy it to at least two different places (different devices, different countries)."
