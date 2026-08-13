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

If `GOOGLE_API_KEY` and a Vertex flag are both set, doctor reports a conflict
and does not pick a lane.

## Environment

| Variable | Purpose |
|---|---|
| `GOOGLE_API_KEY` | Developer API key |
| `GOOGLE_GENAI_USE_VERTEXAI` / `GOOGLE_GENAI_USE_ENTERPRISE` | Select Vertex lane |
| `GOOGLE_APPLICATION_CREDENTIALS` | ADC JSON path |
| `AGYLOOP_UNSAFE_SKIP_ALLOWLIST` | Directories allowed with `--unsafe-skip-permissions` outside git |
| `AGYLOOP_AGY_SETTINGS` / `AGYLOOP_AGY_SETTINGS_FILE` | Written for `--gateway cli` sandbox settings |

State lives under `.agyloop/` in the working directory.

## Gateway and permissions

`--gateway sdk` (default) uses `google-antigravity`. `--unsafe-skip-permissions`
is refused on this path.

`--gateway cli` runs `agy -p` with `--sandbox` and
`proceed-in-sandbox` / `deny: unsandboxed`. `--unsafe-skip-permissions` is
valid after refusing root, refusing `--sandbox`, and refusing a non-git cwd.
agyloop never emits skip-permissions together with `--sandbox`
([antigravity-cli#36](https://github.com/google-antigravity/antigravity-cli/issues/36)).

See [Security](../security.md).
