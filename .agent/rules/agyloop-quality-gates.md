# agyloop-quality-gates (Antigravity mirror of `.claude/skills/agyloop-quality-gates/SKILL.md`)


# agyloop quality gates

```bash
ruff check src tests
ruff format --check src tests
mypy --strict src/agyloop
pytest
pytest -m system
lint-imports
bandit -q -r src/agyloop
pip-audit
properdocs build --strict --config-file properdocs.yml
```

| Gate | Fix |
|---|---|
| `ruff check` | `ruff check --fix src tests` |
| `ruff format` | `ruff format src tests` |
| `mypy` | Annotate. No bare `Any` without a reason. |
| `lint-imports` | Move code to the correct layer (architecture skill). |
| `bandit` | Fix, or `# nosec Bxxx` with *why*. |
| `pip-audit` | Bump the dependency. |
| `properdocs` | Broken link or missing nav entry. |

`pre-commit run --all-files` runs the hook subset. Python 3.12–3.13 in CI.
