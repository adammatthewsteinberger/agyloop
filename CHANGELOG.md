# Changelog

## [0.1.0](https://github.com/adammatthewsteinberger/agyloop/releases/tag/v0.1.0) (2026-08-13)

First public release of **agyloop**: an unattended Google Antigravity /
Gemini runner that never blocks on a human and never treats billing
exhaustion as a short waitable RPM window.

### Features

- Autonomous SDK gateway (`google-antigravity`) with optional `agy` CLI adapter
- Five-member capacity classifier (ADR 0003): Available, WindowExhausted,
  TransientThrottle, CreditsExhausted, AuthenticationFailed
- Git savepoints, mid-run control, generated Gemini REST (`agyloop api`)
- Input-detection retarget off withdrawn `gemini-2.5-flash-lite`
- Fail-closed on empty turns that 404 a withdrawn model
- `run.exception` on the per-run event stream; `turn.completed.cost_usd`
  matches the labeled ledger estimate
