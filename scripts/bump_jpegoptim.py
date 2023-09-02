from __future__ import annotations

import argparse
import hashlib
import re
import subprocess
from pathlib import Path
from typing import Sequence

import urllib3

SETUP_PY_FILE_PATH = Path(__file__).parents[1] / "setup.py"
README_FILE_PATH = Path(__file__).parents[1] / "README.md"

_JPEGOPTIM_VERSION_RE = re.compile(r'JPEGOPTIM_VERSION = "(\d+\.\d+\.\d+)"')
_PY_VERSION_RE = re.compile(r'PY_VERSION = "(\d)"')


def _get_sha_dict(target_version: str) -> dict[str, str]:
    sha_dict = {}
    for suffix in ["x64-linux.zip", "x64-osx.zip", "x64-windows.zip"]:
        download_url = (
            f"https://github.com/tjko/jpegoptim/releases/download/"
            f"v{target_version}/jpegoptim-{target_version}-{suffix}"
        )
        print(f"Fetching Jpegoptim zip file for {suffix}...")
        r = urllib3.request("GET", download_url)
        sha_dict[suffix] = hashlib.sha256(r.data).hexdigest()
    return sha_dict


def _update_setup_py_file(
    args: argparse.Namespace, sha_dict: dict[str, str] | None
) -> str:
    with open(SETUP_PY_FILE_PATH) as f:
        content = f.read()

    # Update py version
    current_py_version = re.search(_PY_VERSION_RE, content)[1]
    next_py_version = int(current_py_version) + 1 if args.bump_minor else 1
    content = re.sub(
        _PY_VERSION_RE,
        f'PY_VERSION = "{next_py_version}"',
        content,
    )
    # Update jpegoptim version
    next_jpegoptim_version = re.search(_JPEGOPTIM_VERSION_RE, content)[1]
    if sha_dict is not None:
        next_jpegoptim_version = args.target_version
        content = re.sub(
            _JPEGOPTIM_VERSION_RE,
            f'JPEGOPTIM_VERSION = "{next_jpegoptim_version}"',
            content,
        )
        for postfix, sha in sha_dict.items():
            content = re.sub(
                rf'{postfix}",(\n\s*)".*"',
                rf'{postfix}",\1"{sha}"',
                content,
            )

    with open(SETUP_PY_FILE_PATH, "w") as file:
        file.write(content)

    next_jpegoptim_py_version = f"{next_jpegoptim_version}.{next_py_version}"
    return next_jpegoptim_py_version


def _update_readme_file(next_jpegoptim_py_version: str) -> None:
    with open(README_FILE_PATH) as f:
        content = f.read()

    content = re.sub(
        r"rev: v\d.\d.\d.(\d)",
        rf"rev: v{next_jpegoptim_py_version}",
        content,
    )

    with open(README_FILE_PATH, "w") as file:
        file.write(content)


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser()
    mutex = parser.add_mutually_exclusive_group(required=True)
    mutex.add_argument(
        "--target-version",
        help="The jpegoptim version to update to.",
    )
    mutex.add_argument(
        "--bump-minor",
        action="store_true",
        help="Bump minor jpegoptim version",
    )
    args = parser.parse_args(argv)

    # 1. Fetch release page and compute checksums.
    sha_dict = None
    if not args.bump_minor:
        sha_dict = _get_sha_dict(args.target_version)

    # 2. Update setup.py file.
    next_jpegoptim_py_version = _update_setup_py_file(args, sha_dict)

    # 3. Update README file.
    _update_readme_file(next_jpegoptim_py_version)

    subprocess.call(["git", "add", SETUP_PY_FILE_PATH, README_FILE_PATH])
    subprocess.call(
        [
            "git",
            "commit",
            "-m",
            f"Bump jpegoptim-py to v{next_jpegoptim_py_version}",
        ]
    )
    subprocess.call(["git", "tag", f"v{next_jpegoptim_py_version}"])
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
