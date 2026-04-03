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

Run the safe incremental mode with a newline-separated changed file list:

```bash
mdwiki_exec --changed-files changed.txt ./post ./dist
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

## Safe Incremental Build

`mdwiki` now supports a safe incremental mode aimed at static blog workflows:

- if only markdown files under `post/` changed, it rebuilds the affected detail pages
- if images or other local assets under `post/` changed, it rebuilds posts in the same folder
- it always refreshes index pages and tag pages so listing pages stay correct
- if `config.json`, `CNAME`, or files outside the source tree changed, it falls back to a full rebuild

The builder writes a manifest file named `.mdwiki-build.json` into the output directory.
If the previous output directory is restored in CI, the next run can reuse that manifest and avoid rewriting every article page.

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

## Optional source markdown link

You can also expose the original markdown source for crawlers and readers:

```json
{
  "source_markdown_base_url": "https://raw.githubusercontent.com/drunkpig/drunkpig.github.io/master/post"
}
```

When this field is present, article pages will:

- add a standard `<link rel="alternate" type="text/markdown">` tag in `<head>`
- keep the raw markdown URL available to crawlers without showing a visible banner in the page body

## Build date in footer

The default footer template renders `build_version` as a `YYYYMMDD` date during site generation.
Because GitHub Pages is built from source on every deploy, this date updates for all generated pages on each successful build.

## GitHub Pages workflow

The recommended deployment model is:

1. Keep markdown source in your repository.
2. Restore the previous `dist/` directory from cache.
3. Build the site in GitHub Actions.
4. Upload the generated `dist/` directory as a Pages artifact.
5. Deploy with `actions/deploy-pages`.

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
      - uses: actions/checkout@v6
        with:
          fetch-depth: 0

      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - uses: actions/cache/restore@v4
        with:
          path: dist
          key: pages-dist-${{ github.ref_name }}-${{ github.run_id }}
          restore-keys: |
            pages-dist-${{ github.ref_name }}-

      - name: Detect changed files
        run: |
          if [ "${{ github.event.before }}" = "0000000000000000000000000000000000000000" ]; then
            : > changed.txt
          else
            git diff --name-only "${{ github.event.before }}" "${{ github.sha }}" > changed.txt
          fi

      - name: Install mdwiki
        run: pip install mdwiki

      - name: Build site
        run: |
          if [ -s changed.txt ]; then
            mdwiki_exec --changed-files changed.txt ./post ./dist
          else
            mdwiki_exec ./post ./dist
          fi

      - uses: actions/cache/save@v4
        if: github.event_name == 'push'
        with:
          path: dist
          key: pages-dist-${{ github.ref_name }}-${{ github.run_id }}
```

## Develop with uv

```bash
uv sync
uv run mdwiki_exec ./post ./dist
uv build
```

Publish to PyPI:

```bash
git tag -a v0.3.6 -m "Release v0.3.6"
git push origin master v0.3.6
```

Pushing a new `v*` tag triggers the bundled GitHub Actions release workflow, which builds the package with `uv` and publishes it to PyPI.

## Notes

- `CNAME` is optional.
- The bundled default theme is stored under `mdwiki/templates/default`.
- `mdwiki_exec` is the supported public CLI entrypoint.
