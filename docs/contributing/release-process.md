# Release process

Nobody remembers to cut a release, bump a version, or sync a changelog — so here,
nobody has to. Releases are automated by [vibey-gh](https://pypi.org/project/vibey-gh/):
the version is **derived from what actually changed** since `main`, applied at
promotion, and published to PyPI via
[Trusted Publishing](https://docs.pypi.org/trusted-publishers/) (OIDC — no long-lived
API token stored anywhere).

## The loop

1. Feature PRs squash-merge into `develop`. Every push to `develop` publishes a
   `.devN` build to TestPyPI.
2. `promote-to-main.yml` compares `develop` and `main` by content, opens the
   promotion PR when they differ, applies the derived version bump, waits for
   checks, and rebase-merges. That push publishes to PyPI (TestPyPI first, then a
   verify step, then PyPI).
3. After each publish, a `realign` step force-pushes `main`'s tree onto `develop`
   when `AUTOMERGE_TOKEN` is configured — **not a fast-forward**: `main` is
   rebase-merged, so its commits are rewritten copies with new SHAs and `develop`
   can never be fast-forwarded onto it. `realign` converges the two branches only
   when their trees are already identical, so it cannot discard develop-only
   work — if `develop` has anything `main` does not, it reports that and stops
   instead of forcing. Without `AUTOMERGE_TOKEN` this step is skipped (harmless;
   promotion compares by content, so a divergent `develop` never blocks a
   release). Do not back-merge by hand.

## What bumps what

`vibey-gh version --since origin/main --explain` shows the derivation: source
changes bump the version; docs-, workflow-, or tooling-only changes do not, and a
version that already differs from `main` is never double-bumped.

There is no release-please, no standing release PR, and no manual tag in the
normal flow. A `v*` tag additionally attaches artifacts to a GitHub Release.
