# agyloop

Autonomous Google Antigravity / Gemini session runner. Same job as [claudeloop](https://github.com/adammatthewsteinberger/claudeloop): never block on a human, and never treat billing / daily-quota exhaustion as a short waitable RPM/TPM blip.

**Status:** planning only. Product source is not scaffolded yet.

## Plans

| Document | Purpose |
|---|---|
| [docs/plans/architecture-and-roadmap.md](docs/plans/architecture-and-roadmap.md) | Full design / transplant plan from claudeloop 0.5.4 |
| [docs/plans/research-notes.md](docs/plans/research-notes.md) | Vendor SDK/CLI capacity + autonomy research |
| [docs/plans/_shared-transplant-outline.md](docs/plans/_shared-transplant-outline.md) | Cross-product keep/swap + Global Constraints |
| [docs/superpowers/plans/2026-08-13-agyloop-implementation.md](docs/superpowers/plans/2026-08-13-agyloop-implementation.md) | Bite-sized TDD implementation plan |

## Naming

| Item | Value |
|---|---|
| PyPI / CLI | `agyloop` |
| Env prefix | `AGYLOOP_*` |
| State dir | `.agyloop/` |
| Done marker | `AGYLOOP_TASK_FULLY_COMPLETE` |
