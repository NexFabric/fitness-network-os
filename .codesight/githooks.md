# Git Hooks

> **Note for agents:** These hooks fire automatically on git operations and will block the operation if they fail.

## `pre-commit` — raw git hook

- **set**: `set -e`
- **changed=$(git**: `changed=$(git diff --cached --name-only --diff-filter=ACMR)`
- **case**: `case "$changed" in`
- ***.py|*.ts|*.tsx|*.md|*backend/*|*frontend/*|*docs/*)**: `*.py|*.ts|*.tsx|*.md|*backend/*|*frontend/*|*docs/*) ;;`
- ***)**: `*) exit 0 ;;`
- **esac**: `esac`
- **command**: `command -v npx >/dev/null 2>&1 || exit 0`
- **npx**: `npx --yes --no-install codesight --wiki >/dev/null 2>&1 || exit 0`
- **if**: `if [ -d docs ]; then`
- **npx**: `npx --yes --no-install codesight --mode knowledge docs -o .codesight >/dev/null 2>&1 || true`
- **fi**: `fi`
- **git**: `git add .codesight >/dev/null 2>&1 || true`
- **exit**: `exit 0`

_Source: .git/hooks/pre-commit_
