# Configuration

## Auth lanes

Set **one** lane. `agyloop doctor` reports what it can prove.

**Developer API**

```bash
export GOOGLE_API_KEY=...
agyloop doctor
```

**Enterprise / Vertex (ADC)**

```bash
export GOOGLE_GENAI_USE_VERTEXAI=1   # or GOOGLE_GENAI_USE_ENTERPRISE=1
agyloop doctor
```

If `GOOGLE_API_KEY` and a Vertex flag are both set, doctor reports a conflict,
fails the auth check, and does not pick a lane.

## `agyloop.toml`

Precedence: CLI flags > `AGYLOOP_*` environment variables >
`./agyloop.toml` > `~/.config/agyloop/config.toml` > built-in defaults.

```toml
[run]
max_turns = 40
max_dollars = 5.0          # labeled estimate (ADR 0009)
gateway = "sdk"
ramp = 0

[model]
low = "gemini-2.5-flash-lite"
medium = "gemini-2.5-flash"
high = "gemini-2.5-pro"
```

`agyloop config` prints the effective table. `--preset low|medium|high` selects
both model and default effort. `--max-dollars` stops the run when the labeled
USD estimate reaches the cap.

## Environment

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Developer API key |
| `GOOGLE_ACCESS_TOKEN` / `CLOUDSDK_AUTH_ACCESS_TOKEN` | Bearer token for `agyloop api --lane vertex` |
| `GOOGLE_GENAI_USE_VERTEXAI` / `GOOGLE_GENAI_USE_ENTERPRISE` | Select Vertex lane for doctor / SDK |
| `GOOGLE_APPLICATION_CREDENTIALS` | ADC JSON path |
| `AGYLOOP_MAX_TURNS` / `AGYLOOP_MAX_DOLLARS` / `AGYLOOP_MODEL_LOW` … | Override toml keys |
| `AGYLOOP_UNSAFE_SKIP_ALLOWLIST` | Directories allowed with `--unsafe-skip-permissions` outside git |
| `AGYLOOP_AGY_SETTINGS` / `AGYLOOP_AGY_SETTINGS_FILE` | Written for `--gateway cli` sandbox settings |

State lives under `.agyloop/` in the working directory. `agyloop reset --yes`
deletes that tree only (refuses while a run PID is live).

## Logging

`--verbose` / `--log-level` / `--log-file` on the root command. File logs are
JSON lines and pass through redaction. Per-run `events.jsonl` is a separate
sink under `.agyloop/runs/<id>/`.

## Gateway and permissions

`--gateway sdk` (default) uses `google-antigravity`. `--unsafe-skip-permissions`
is refused on this path.

`--gateway cli` runs `agy -p` with `--sandbox` and
`proceed-in-sandbox` / `deny: unsandboxed`. `--unsafe-skip-permissions` is
valid after refusing root, refusing `--sandbox`, and refusing a non-git cwd.
agyloop never emits skip-permissions together with `--sandbox`
([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

See [Security](../security.md).
