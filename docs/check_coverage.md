# check_coverage

Run tests with coverage and report overall percent.

Uses the repo .venv python if present, otherwise uses the current interpreter.
If tests fail, this script exits with the pytest exit code (non-zero) so pre-commit fails.
If tests pass but coverage is below threshold, it prints a warning but exits 0 (does not fail pre-commit).

## Minimal apps.yaml snippet

```yaml
check_coverage:
  module: check_coverage
  class: check_coverage
  # options:
```