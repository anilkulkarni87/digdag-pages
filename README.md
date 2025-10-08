# digdag-pages

Generate dark-themed inline-SVG HTML workflow pages from Digdag `.dig` files, with a searchable schedules index and Prism-highlighted SQL pages.

## Install
```bash
pip install -e .
```

## Use
```bash
digdag-pages
```
Outputs into `graphs/` and a root `scheduled_workflows.html`.

### Treasure Data Console links
The SQL page shows “Open in TD Console” links. Set your region/base URL via:

```bash
export TD_CONSOLE_BASE="https://console.treasuredata.com"  # change per region/account


## Examples
A runnable `examples/sample_project` is included (schedule, `!include`, `td>` -> SQL demo).
```bash
pip install -e .[dev]
digdag-pages               # from repo root
open scheduled_workflows.html
```


## GitHub Pages
This repo includes a Pages workflow that builds the graphs and deploys them.
1. Push to `main` (or `master`).
2. In your repo settings, enable **Pages** → **Build and deployment** → **Source: GitHub Actions**.
3. The workflow will publish `scheduled_workflows.html` (root) and the `graphs/` folder.


## Publish to PyPI

### One-time
1. Create accounts at [PyPI](https://pypi.org/) and [TestPyPI](https://test.pypi.org/).
2. In GitHub repo **Settings → Secrets and variables → Actions → New repository secret** add:
   - `TEST_PYPI_API_TOKEN` (scoped token from TestPyPI)
   - `PYPI_API_TOKEN` (scoped token from PyPI)

### CI (recommended)
- Push a tag like `v0.1.0` to trigger `.github/workflows/publish.yml` which builds and uploads to **TestPyPI then PyPI**.

### Local (optional)
```bash
python -m pip install --upgrade build twine
python -m build
twine upload --repository-url https://test.pypi.org/legacy/ dist/*
# verify install works from TestPyPI in a clean venv, then:
twine upload dist/*
```
