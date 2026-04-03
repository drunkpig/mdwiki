# mdwiki

`mdwiki` is a small static site builder that turns a directory tree of markdown files into a blog-ready HTML site.

It keeps the authoring model simple:

- directories become URL segments
- each markdown file becomes one HTML page
- local images referenced from markdown are copied into the output site
- index pages and tag pages are generated automatically

## Install

Use `uv`:

```bash
uv tool install mdwiki
```

Or install from source:

```bash
uv sync
uv run mdwiki_exec ./example-posts ./dist
```

## CLI

Build a site from a markdown source tree:

```bash
mdwiki_exec <source_dir> <dist_dir>
```

Show the built-in help or version:

```bash
mdwiki_exec --help
mdwiki_exec --version
```

Example:

```bash
mdwiki_exec ./post ./dist
```

`source_dir` usually contains:

- markdown posts under dated folders such as `post/2024/04/03/demo.md`
- optional local images next to each markdown file
- optional `CNAME`
- optional `config.json`

## Optional GoatCounter support

You can enable real pageview counters by adding `goatcounter_script` to your `config.json`:

```json
{
  "goatcounter_script": "<script data-goatcounter=\"https://drunkpig.goatcounter.com/count\" async src=\"//gc.zgo.at/count.js\"></script>"
}
```

When this field is present:

- article pages render a counter next to the slug
- index pages fetch and display per-article pageviews

When it is absent, `mdwiki` renders `未知` instead of fake random numbers.

## GitHub Pages workflow

The recommended deployment model is:

1. Keep markdown source in your repository.
2. Build the site in GitHub Actions.
3. Upload the generated `dist/` directory as a Pages artifact.
4. Deploy with `actions/deploy-pages`.

Example workflow:

```yaml
name: Build and Deploy Pages

on:
  push:
    branches: ["master"]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - uses: actions/configure-pages@v5
      - name: Install mdwiki
        run: pip install mdwiki
      - name: Build site
        run: mdwiki_exec ./post ./dist
      - uses: actions/upload-pages-artifact@v3
        with:
          path: ./dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

## Develop with uv

```bash
uv sync
uv run mdwiki_exec ./post ./dist
uv build
```

Publish to PyPI:

```bash
git tag -a v0.3.3 -m "Release v0.3.3"
git push origin master v0.3.3
```

Pushing a new `v*` tag triggers the bundled GitHub Actions release workflow, which builds the package with `uv` and publishes it to PyPI.

## Notes

- `CNAME` is optional.
- The bundled default theme is stored under `mdwiki/templates/default`.
- `mdwiki_exec` is the supported public CLI entrypoint.
