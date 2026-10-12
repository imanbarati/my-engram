#!/usr/bin/env bash
# Installs a git pre-commit hook that blocks commits containing secrets.
set -euo pipefail
cd "$(dirname "$0")/.."
[ -d .git ] || { echo "Run 'git init' first."; exit 1; }
cat > .git/hooks/pre-commit << 'HOOK'
#!/usr/bin/env bash
exec python3 scripts/check_secrets.py --staged
HOOK
chmod +x .git/hooks/pre-commit
echo "Pre-commit secret scan installed."
