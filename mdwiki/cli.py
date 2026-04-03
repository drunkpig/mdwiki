import argparse

from mdwiki.mdwiki import main as build_site


def mdwiki_exec() -> int:
    parser = argparse.ArgumentParser(
        prog="mdwiki_exec",
        description="Build a static site from a directory of markdown files.",
    )
    parser.add_argument("source_dir", help="Directory containing markdown source files")
    parser.add_argument("dist_dir", help="Directory to write generated HTML files into")
    args = parser.parse_args()
    build_site(args.source_dir, args.dist_dir)
    return 0


def main() -> int:
    return mdwiki_exec()
