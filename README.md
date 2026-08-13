# agyloop

[![CI](https://github.com/adammatthewsteinberger/agyloop/actions/workflows/ci.yml/badge.svg)](https://github.com/adammatthewsteinberger/agyloop/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/agyloop)](https://pypi.org/project/agyloop/)
[![Python versions](https://img.shields.io/pypi/pyversions/agyloop)](https://pypi.org/project/agyloop/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://github.com/adammatthewsteinberger/agyloop/blob/main/LICENSE)
[![Docs](https://img.shields.io/badge/docs-github.io-teal)](https://adammatthewsteinberger.github.io/agyloop/)

Autonomous Google Antigravity / Gemini session runner. Same job as
[claudeloop](https://github.com/adammatthewsteinberger/claudeloop): never
block on a human, and never treat billing / daily-quota exhaustion as a
short waitable RPM/TPM blip.

## Install

Python 3.12+.

```bash
pip install agyloop
pipx install agyloop
```

TestPyPI (contributor dry run; runtime deps still come from PyPI):

```bash
pip install -i https://test.pypi.org/simple/ --extra-index-url https://pypi.org/simple/ agyloop
```

Auth is **either** `GOOGLE_API_KEY` (Gemini Developer API) **or** Application
Default Credentials with a Vertex/Enterprise flag. `agyloop doctor` reports
the lane; it never guesses. See the
[usage guide](https://adammatthewsteinberger.github.io/agyloop/usage/).

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
agyloop snapshot
agyloop api --help
```

Generated Gemini REST is `agyloop api`
([ADR 0015](https://adammatthewsteinberger.github.io/agyloop/architecture/decisions/0015-generated-gemini-rest-with-drift-gate/)).
Pace cold Enterprise runs with `--ramp N`. Drive a live `agy` binary with
`--gateway cli`.

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
Details: [usage](https://adammatthewsteinberger.github.io/agyloop/usage/).

## Never block on a human

`ask_question` is denied with guidance. Interactive SDK hooks are never
registered. Operator `stop` / `prompt` write the run inbox; they do not wait
on stdin. See [SECURITY.md](https://github.com/adammatthewsteinberger/agyloop/blob/main/SECURITY.md).

## Permissions

Default SDK path: `allow_all()` + workspace scope + destructive-command
denies. `--safe` limits tools; `--yolo` drops workspace/destructive scopes.

`--unsafe-skip-permissions` is a **CLI-adapter argv** opt-in for
`agy --dangerously-skip-permissions`. `agyloop run` (`--gateway sdk`, the
default) **refuses** the flag. `--gateway cli` honors it after the usual
gates. agyloop never emits that flag together with `--sandbox`
([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

## Tests

```bash
pytest                          # skips system/live
pytest -m system                # real FS/git/control + scripted agent; no Google account
```

## Links

| Document | URL |
|---|---|
| Documentation | https://adammatthewsteinberger.github.io/agyloop/ |
| Installation | https://adammatthewsteinberger.github.io/agyloop/getting-started/installation/ |
| Contributing | https://github.com/adammatthewsteinberger/agyloop/blob/main/CONTRIBUTING.md |
| Changelog | https://github.com/adammatthewsteinberger/agyloop/blob/main/CHANGELOG.md |
| Security | https://github.com/adammatthewsteinberger/agyloop/blob/main/SECURITY.md |
| Source | https://github.com/adammatthewsteinberger/agyloop |
| PyPI | https://pypi.org/project/agyloop/ |

## Naming

| Item | Value |
|---|---|
| PyPI / CLI | `agyloop` |
| Env prefix | `AGYLOOP_*` |
| State dir | `.agyloop/` |
| Done marker | `AGYLOOP_TASK_FULLY_COMPLETE` |
