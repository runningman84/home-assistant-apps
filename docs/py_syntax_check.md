# py_syntax_check

Syntax check staged or provided Python files.

This script is intended to be executed by pre-commit inside its venv so
dependencies (python) are the venv's interpreter and no system-wide tools
are required.

## Minimal apps.yaml snippet

```yaml
py_syntax_check:
  module: py_syntax_check
  class: py_syntax_check
  # options:
```