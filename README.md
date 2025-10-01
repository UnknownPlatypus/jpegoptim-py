[![build status](https://github.com/UnknownPlatypus/jpegoptim-py/actions/workflows/main.yml/badge.svg)](https://github.com/UnknownPlatypus/jpegoptim-py/actions/workflows/main.yml)
<!-- [![pre-commit.ci status](https://results.pre-commit.ci/badge/github/shellcheck-py/shellcheck-py/main.svg)](https://results.pre-commit.ci/latest/github/shellcheck-py/shellcheck-py/main) -->

# jpegoptim-py

A python wrapper to provide a pip-installable [jpegoptim](https://github.com/tjko/jpegoptim) binary.

Internally this package provides a convenient way to download the pre-built
jpegoptim binary for your particular platform.

### Installation

```bash
pip install jpegoptim-py
```

### Usage

After installation, the `jpegoptim` binary should be available in your
environment (or `jpegoptim.exe` on windows).

### As a pre-commit hook

See [pre-commit](https://pre-commit.com) for instructions

Sample `.pre-commit-config.yaml`:

```yaml
-   repo: https://github.com/UnknownPlatypus/jpegoptim-py
    rev: v1.5.6.1
    hooks:
    -   id: jpegoptim
```

Lossy compression [is not idempotent](https://github.com/tjko/jpegoptim/issues/9). In that case, consider adding a 
threshold, otherwise you might block the commit for too long.

Sample `.pre-commit-config.yaml` with lossy compression enabled:

```yaml
-   repo: https://github.com/UnknownPlatypus/jpegoptim-py
    rev: v1.5.6.1
    hooks:
    -   id: jpegoptim
        args: [--strip-all, --all-progressive, --max=85, --threshold=3]
```

### References

This is an adaptation of [shellcheck-py](https://github.com/shellcheck-py/shellcheck-py) following the exact same strategy. 
This aims at making it easier to use as a pre-commit hook.
