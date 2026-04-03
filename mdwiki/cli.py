from pathlib import Path

import click
from mdwiki.mdwiki import main as build_site


@click.command(
    context_settings={"help_option_names": ["-h", "--help"]},
    help="Build a static site from a directory of markdown files.",
)
@click.argument(
    "source_dir",
    type=click.Path(exists=True, file_okay=False, dir_okay=True, path_type=Path),
)
@click.argument(
    "dist_dir",
    type=click.Path(file_okay=False, dir_okay=True, path_type=Path),
)
def mdwiki_exec(source_dir: Path, dist_dir: Path) -> None:
    """Build the markdown tree in SOURCE_DIR into DIST_DIR."""
    build_site(str(source_dir), str(dist_dir))


def main() -> None:
    mdwiki_exec()
