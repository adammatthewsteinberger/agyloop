# Using agyloop

Unattended Antigravity / Gemini runs. The SDK path is the default. Generated
Gemini REST (`agyloop api`) does not ship; see
[ADR 0006](architecture/decisions/0006-defer-genai-rest.md).

## Auth

Set **one** lane. `agyloop doctor` reports what it can prove and will not
guess Developer vs Enterprise when both look possible.

**Developer API**

```bash
export GOOGLE_API_KEY=...
agyloop doctor
```

**Enterprise / Vertex (ADC)**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=1   # or GOOGLE_GENAI_USE_ENTERPRISE=1
# ADC via GOOGLE_APPLICATION_CREDENTIALS or
# ~/.config/gcloud/application_default_credentials.json
agyloop doctor
```

If `GOOGLE_API_KEY` and a Vertex flag are both set, doctor reports a
conflict and does not pick a lane.

## Run

```bash
agyloop run plan.md
agyloop run plan.md --cwd /path/to/repo --model gemini-2.5-pro
agyloop run plan.md --max-turns 40 --max-wait 86400 --max-tokens 200000
agyloop run plan.md --no-probe          # wait to quota boundaries only
agyloop run plan.md --safe              # nondestructive tools
agyloop run plan.md --yolo              # drop workspace/destructive SDK scopes
```

The plan file is copied under `.agyloop/runs/<run-id>/plan.md`. Completion
is a structured verdict (`complete`, `remaining_work`, `blocked_on`,
`summary`) with the fallback marker `AGYLOOP_TASK_FULLY_COMPLETE`.

## Resume

agyloop resumes **its own registry**, not an enumeration of vendor
conversations.

```bash
agyloop resume --last
agyloop resume --conversation <conversation_id>
agyloop sessions
```

If the vendor conversation cannot be resumed, the runner starts a fresh
conversation seeded with the persisted plan text.

## Doctor

```bash
agyloop doctor
```

Checks: auth lane and source, no interactive hooks, optional `agy` CLI on
`PATH`, no MCP servers (OAuth cannot complete unattended), git working
directory. It does not read live quota — use AI Studio / Cloud Console for
that.

## Mid-run control

Same cwd, second terminal. Commands target the newest **active** run
(live PID). Finished runs are refused.

```bash
agyloop prompt --now "Also handle the timeout path"
agyloop prompt --at-break "Then run the tests"
agyloop stop
```

These write `.agyloop/runs/<id>/inbox/*.cmd.json`. They never block waiting
for a human at the keyboard of the running loop.

## Capacity

| Classifier state | Typical signal | What agyloop does |
|---|---|---|
| RPM / TPM / IPM | per-minute / per-token window | Short wait + probe |
| RPD | daily quota / requests per day | Wait toward next Pacific midnight |
| Credits / spend / billing | spend-based, billing cap, no balance | Probe cadence (no fabricated `resets_at`); notify |
| Auth failure | 401 / unauthenticated | Abort |

`--no-probe` skips capacity chat turns and waits only until computed
boundaries. Credits exhaustion is still not a short RPM sleep.

RPM ≠ RPD ≠ credits. A billing wall does not grow a reset timestamp.

## Permissions and the CLI sandbox

Default SDK autonomy is scoped. See [SECURITY.md](../SECURITY.md) for the
`--sandbox` + `--dangerously-skip-permissions` footgun
([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

`--unsafe-skip-permissions` is the explicit CLI-adapter argv opt-in
(`build_agy_argv`). `agyloop run` refuses it: the SDK path uses policies /
`--yolo` and never emits `--dangerously-skip-permissions`. On the argv
builder it refuses root, refuses `--sandbox`, and refuses a non-git
directory unless `AGYLOOP_UNSAFE_SKIP_ALLOWLIST` includes it.

## Tests

```bash
pytest                 # unit/application; excludes system and live
pytest -m system       # scripted agent, real filesystem/git/control inbox
```

System tests do not need a live Google account.
