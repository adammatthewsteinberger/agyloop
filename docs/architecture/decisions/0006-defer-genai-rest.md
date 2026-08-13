# ADR 0006: Defer the generated Gemini REST CLI

## Status

Accepted (M4 documented deferral). `agyloop api` does not ship.

## Context

claudeloop's M4 generated a 1:1 CLI over Anthropic REST endpoints by
introspecting the SDK resource tree, guarded by a drift gate. agyloop's
equivalent substrates (research F14, architecture §14) are:

| Option | Substrate |
|---|---|
| **A.** Discovery document | `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta` |
| **B.** Published OpenAPI 3.0 | `https://generativelanguage.googleapis.com/$discovery/OPENAPI3_0?version=v1beta` |
| **C.** `google-genai` SDK introspection | `client.models`, `.files`, `.caches`, `.batches`, `.tunings`, `.aio.*` |

Architecture §14 chose **A with B as a cross-check**, gated on a stability
criterion. Shipping a generated surface that is wrong within a month is worse
than not shipping one.

## Criterion

Ship a generated Gemini REST CLI only if **both** hold at M4 planning time:

1. The discovery document's endpoint inventory has been stable across two
   consecutive minor Gemini API releases, **and**
2. The Antigravity SDK has left preview.

Otherwise M4 is documented deferral: the `api` command does not ship.

## Spike (2026-08-13)

### (2) Antigravity SDK preview status — not met

The SDK is still in preview.

- Vendor launch post (19 May 2026) titled the product a **preview** / Research
  Preview: <https://antigravity.google/blog/introducing-google-antigravity-sdk>
- PyPI `google-antigravity` is still the **0.1.x** series: `0.1.0` (19 May
  2026) through `0.1.10` (5 August 2026). No 1.x / GA release exists.
- Official overview + Quick Start
  (<https://antigravity.google/docs/sdk/overview>) does not declare general
  availability.

Criterion (2) fails on its own. That is sufficient to defer.

### (1) Discovery-document stability — not met

Fetched **without an API key** on 2026-08-13:

- Discovery A: `https://generativelanguage.googleapis.com/$discovery/rest?version=v1beta`
  - `id`: `generativelanguage:v1beta`
  - `title`: Gemini API
  - `revision`: **20260812** (calendar-dated the previous day — not a frozen
    minor-release inventory)
  - 12 top-level resources (`auth_tokens`, `batches`, `cachedContents`,
    `corpora`, `dynamic`, `environments`, `fileSearchStores`, `files`,
    `generatedFiles`, `media`, `models`, `tunedModels`)
  - **84** REST methods
- OpenAPI B: same host, `$discovery/OPENAPI3_0?version=v1beta`
  - `info.version`: `v1beta`, `x-google-revision`: **20260812**
  - 69 paths / **91** operations — already a count mismatch with A, so an A/B
    cross-check binder would itself be new, unproven code

Gemini API changelog through July 2026 shows recent breaking and additive
churn (Interactions API schema migration May–June 2026; parameter
deprecations 21 July 2026). There is no evidence the endpoint inventory was
stable across two consecutive minor Gemini API releases.

Criterion (1) also fails.

### Vertex / Enterprise lane

`https://aiplatform.googleapis.com/$discovery/rest?version=v1` exists and
describes the Agent Platform / Vertex family (typings snapshot revision
`20260725`). That tree is a different API family with partially disjoint
operations from the Developer API discovery document. A generated CLI would
have to model the split the way claudeloop's `--provider` modeled partial
trees — further cost, not a reason to ship while the criterion fails.

`google-genai` (option C) was not used as the shipping substrate: it is a
second SDK, narrower than the raw API, and the criterion gates on discovery
stability plus Antigravity leaving preview, not on `google-genai` class-tree
shape.

## Decision

**Defer.** `agyloop api` does not ship. The `ApiGateway` application port
remains declared and unimplemented. No generated binder, no drift-gate
baseline, no 1:1 guess at Gemini REST.

Revisit when **both** criterion clauses hold. Until then, do not add an `api`
Typer command.

Mid-run operator control (`stop` / `prompt` writing into
`.agyloop/runs/<run_id>/inbox/`) is independent of this deferral and may
ship as M4 polish.

## Consequences

- Help text states the REST surface is deferred (ADR 0006); a CLI test
  asserts `api` is absent from the command list.
- A drift gate that hides one operation and fails CI is **not** added,
  because there is no generated surface to gate.
- Regenerating a 1:1 CLI from a daily-revision `v1beta` document would rot
  inside a month; that is the failure mode this ADR exists to prevent.
