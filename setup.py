#!/usr/bin/env python3
from __future__ import annotations

import hashlib
import http
import io
import os.path
import platform
import stat
import sys
import urllib.request
import zipfile

from distutils.command.build import build as orig_build
from distutils.core import Command
from setuptools import setup
from setuptools.command.install import install as orig_install

JPEGOPTIM_VERSION = "1.5.4"
PY_VERSION = "1"  # Python wrapper version

POSTFIX_SHA256 = {
    ("linux", "x86_64"): (
        "x64-linux.zip",
        "75f6975454bc33cce5ff46fd13809c010bec0f2c43de26a7e3b92cc6ece85bb4",
    ),
    ("darwin", "x86_64"): (
        "x64-macos.zip",
        "6a170a50fe0d5aa01636d64ae7647ac615867c184f2fb4ead557c284005deae8",
    ),
    ("win32", "AMD64"): (
        "x64-windows.zip",
        "70d9a26b3bd9c4331d10c03f7431afa8eecef0b1d6ceef30455f70433a3c3311",
    ),
}
POSTFIX_SHA256[("darwin", "arm64")] = POSTFIX_SHA256[("darwin", "x86_64")]


def get_download_url() -> tuple[str, str]:
    postfix, sha256 = POSTFIX_SHA256[(sys.platform, platform.machine())]
    url = (
        f"https://github.com/UnknownPlatypus/jpegoptim/releases/download/"
        f"v{JPEGOPTIM_VERSION}/jpegoptim-{JPEGOPTIM_VERSION}-{postfix}"
    )
    return url, sha256


def download(url: str, sha256: str) -> bytes:
    with urllib.request.urlopen(url) as resp:
        code = resp.getcode()
        if code != http.HTTPStatus.OK:
            raise ValueError(f"HTTP failure. Code: {code}")
        data = resp.read()

    checksum = hashlib.sha256(data).hexdigest()
    if checksum != sha256:
        raise ValueError(f"sha256 mismatch, expected {sha256}, got {checksum}")

    return data


def extract(url: str, data: bytes) -> bytes:
    with io.BytesIO(data) as bio:
        with zipfile.ZipFile(bio) as zipf:
            for info in zipf.infolist():
                if info.filename.startswith("jpegoptim"):
                    return zipf.read(info.filename)

    raise AssertionError(f"unreachable {url}")


def save_executable(data: bytes, base_dir: str):
    exe = "jpegoptim" if sys.platform != "win32" else "jpegoptim.exe"
    output_path = os.path.join(base_dir, exe)
    os.makedirs(base_dir)

    with open(output_path, "wb") as fp:
        fp.write(data)

    # Mark as executable.
    # https://stackoverflow.com/a/14105527
    mode = os.stat(output_path).st_mode
    mode |= stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    os.chmod(output_path, mode)


class build(orig_build):
    sub_commands = orig_build.sub_commands + [("fetch_binaries", None)]


class install(orig_install):
    sub_commands = orig_install.sub_commands + [("install_jpegoptim", None)]


class fetch_binaries(Command):
    build_temp = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        self.set_undefined_options("build", ("build_temp", "build_temp"))

    def run(self):
        # save binary to self.build_temp
        url, sha256 = get_download_url()
        archive = download(url, sha256)
        data = extract(url, archive)
        save_executable(data, self.build_temp)


class install_jpegoptim(Command):
    description = "install the jpegoptim executable"
    outfiles = ()
    build_dir = install_dir = None

    def initialize_options(self):
        pass

    def finalize_options(self):
        # this initializes attributes based on other commands' attributes
        self.set_undefined_options("build", ("build_temp", "build_dir"))
        self.set_undefined_options(
            "install",
            ("install_scripts", "install_dir"),
        )

    def run(self):
        self.outfiles = self.copy_tree(self.build_dir, self.install_dir)

    def get_outputs(self):
        return self.outfiles


command_overrides = {
    "install": install,
    "install_jpegoptim": install_jpegoptim,
    "build": build,
    "fetch_binaries": fetch_binaries,
}


try:
    from wheel.bdist_wheel import bdist_wheel as orig_bdist_wheel
except ImportError:
    pass
else:

    class bdist_wheel(orig_bdist_wheel):
        def finalize_options(self):
            orig_bdist_wheel.finalize_options(self)
            # Mark us as not a pure python package
            self.root_is_pure = False

        def get_tag(self):
            _, _, plat = orig_bdist_wheel.get_tag(self)
            # We don't contain any python source, nor any python extensions
            return "py2.py3", "none", plat

    command_overrides["bdist_wheel"] = bdist_wheel

setup(version=f"{JPEGOPTIM_VERSION}.{PY_VERSION}", cmdclass=command_overrides)
