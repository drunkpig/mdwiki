from pathlib import Path
from typing import Optional

import click

from mdwiki import __version__
from mdwiki.mdwiki import build_site


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Build a static site from a directory of markdown files.",
)
@click.version_option(__version__, prog_name="mdwiki_exec")
@click.option(
    "--changed-files",
    type=click.Path(exists=True, dir_okay=False, path_type=Path),
    help="Optional newline-separated changed file list for safe incremental builds.",
)
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "dist_dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
def mdwiki_exec(source_dir: Path, dist_dir: Path, changed_files: Optional[Path]) -> None:
    """Build the markdown tree in SOURCE_DIR into DIST_DIR."""
    mode = build_site(str(source_dir), str(dist_dir), changed_files=str(changed_files) if changed_files else None)
    click.echo(f"build mode: {mode}")


def main() -> None:
    mdwiki_exec()
