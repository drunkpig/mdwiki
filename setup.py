from pathlib import Path
import re

import setuptools


ROOT = Path(__file__).parent


def read_text(path: str) -> str:
    return (ROOT / path).read_text(encoding="utf-8")


def read_version() -> str:
    match = re.search(
        r'^__version__\s*=\s*"([^"]+)"',
        read_text("mdwiki/__init__.py"),
        re.MULTILINE,
    )
    if not match:
        raise RuntimeError("Unable to find package version.")
    return match.group(1)


def read_requirements(path: str) -> list:
    requirements = []
    for line in read_text(path).splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        requirements.append(line)
    return requirements


setuptools.setup(
    name="mdwiki",
    version=read_version(),
    author="niceMachine",
    author_email="xuchaoo@gmail.com",
    description="zero config static blog builder",
    long_description=read_text("README.MD"),
    long_description_content_type="text/markdown",
    url="https://github.com/drunkpig/mdwiki",
    packages=setuptools.find_packages(),
    classifiers=[
        "Programming Language :: Python :: 3",
        "License :: OSI Approved :: MIT License",
        "Operating System :: OS Independent",
    ],
    scripts=["mdwiki/bin/mdpub"],
    entry_points={
        "console_scripts": [
            "mdwiki_exec=mdwiki.cli:main",
        ],
    },
    install_requires=read_requirements("requirements.txt"),
    include_package_data=True,
    python_requires=">=3.7",
)
