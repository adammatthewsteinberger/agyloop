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
3. After each publish, `develop` is fast-forwarded onto `main` automatically. Do
   not back-merge by hand.

## What bumps what

`vibey-gh version --since origin/main --explain` shows the derivation: source
changes bump the version; docs-, workflow-, or tooling-only changes do not, and a
version that already differs from `main` is never double-bumped.

There is no release-please, no standing release PR, and no manual tag in the
normal flow. A `v*` tag additionally attaches artifacts to a GitHub Release.
