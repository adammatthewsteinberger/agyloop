# Installation

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

Docs extra (this site):

```bash
uv sync --extra docs
uv run mkdocs serve
```

Auth is **either** `GOOGLE_API_KEY` (Gemini Developer API) **or** Application
Default Credentials with a Vertex / Enterprise flag. `agyloop doctor` reports
the lane; it never guesses. See [Configuration](configuration.md).
