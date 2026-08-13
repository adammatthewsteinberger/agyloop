# agyloop

Autonomous Google Antigravity / Gemini session runner. Same job as
[claudeloop](https://github.com/adammatthewsteinberger/claudeloop): never
block on a human, and never treat billing / daily-quota exhaustion as a
short waitable RPM/TPM blip.

## Install

Python 3.12+. From a clone:

```bash
pipx install .
agyloop --help
```

Or editable for development:

```bash
uv sync --extra dev
uv run agyloop --help
```

Auth is **either** `GOOGLE_API_KEY` (Gemini Developer API) **or** Application
Default Credentials with a Vertex/Enterprise flag. `agyloop doctor` reports
the lane; it never guesses. See [docs/usage.md](docs/usage.md).

## Quickstart

```bash
agyloop doctor                  # pre-flight: auth lane, no interactive hooks
agyloop run handoff.md          # seed a session from a plan and run unattended
agyloop resume --last           # resume the most recent .agyloop/ run
agyloop resume --conversation <id>
agyloop sessions                # local .agyloop/runs registry only

# Mid-run (second terminal, same cwd):
agyloop prompt --now "Also cover the error path"
agyloop prompt --at-break "Then write tests"
agyloop stop                    # soft-stop the active run
```

Generated Gemini REST `agyloop api` is deferred ([ADR 0006](docs/architecture/decisions/0006-defer-genai-rest.md)).

## Capacity model (RPM vs RPD vs credits)

A `429 RESOURCE_EXHAUSTED` is not one thing:

| State | Meaning | Waiting helps? |
|---|---|---|
| RPM / TPM / IPM window | Per-minute throttle | Yes — short probe cadence |
| RPD window | Daily quota | Yes — next Pacific midnight, not a short sleep |
| Credits / spend / billing cap | No balance, spend cap | **No clock reset.** Probe until a human tops up |
| Auth failure | Bad or revoked credentials | Never — abort |

`--no-probe` waits only to computed quota boundaries and issues zero probe
requests. `--max-turns`, `--max-wait`, and `--max-tokens` bound a run.
Details: [docs/usage.md](docs/usage.md#capacity).

## Never block on a human

`ask_question` is denied with guidance. Interactive SDK hooks are never
registered. Operator `stop` / `prompt` write the run inbox; they do not wait
on stdin. See [SECURITY.md](SECURITY.md).

## Permissions

Default SDK path: `allow_all()` + workspace scope + destructive-command
denies. `--safe` limits tools; `--yolo` drops workspace/destructive scopes.

`--unsafe-skip-permissions` is a **CLI-adapter** opt-in for
`agy --dangerously-skip-permissions`. It refuses root, refuses combining with
`--sandbox`, and refuses a non-git cwd. agyloop never emits that flag together
with `--sandbox` ([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

## Tests

```bash
pytest                          # skips system/live
pytest -m system                # real FS/git/control + scripted agent; no Google account
```

## Plans

| Document | Purpose |
|---|---|
| [docs/usage.md](docs/usage.md) | Run / resume / doctor / auth / capacity |
| [SECURITY.md](SECURITY.md) | Sandbox footgun, never-block, reporting |
| [docs/plans/architecture-and-roadmap.md](docs/plans/architecture-and-roadmap.md) | Design / transplant plan from claudeloop |
| [docs/plans/research-notes.md](docs/plans/research-notes.md) | Vendor SDK/CLI capacity + autonomy research |
| [docs/architecture/decisions/0006-defer-genai-rest.md](docs/architecture/decisions/0006-defer-genai-rest.md) | Why `agyloop api` does not ship |

## Naming

| Item | Value |
|---|---|
| PyPI / CLI | `agyloop` |
| Env prefix | `AGYLOOP_*` |
| State dir | `.agyloop/` |
| Done marker | `AGYLOOP_TASK_FULLY_COMPLETE` |
