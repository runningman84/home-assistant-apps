#!/usr/bin/env python3
"""Verify sample_config/apps.yaml options against app code.

The script collects option keys used in each app by scanning for
patterns like `self.args.get("key")`, `self.args['key']`, or `args.get('key')`.
It also merges keys found in `apps/base.py` (shared options).

Run this from the repo root: `python3 scripts/verify_sample_config.py`
"""
from pathlib import Path
import re
import sys

try:
    import yaml
except Exception:
    print("PyYAML is required. Please install with: python -m pip install pyyaml")
    raise

ROOT = Path(__file__).resolve().parents[1]
APPS_PY = ROOT / 'apps'
SAMPLE = ROOT / 'sample_config' / 'apps.yaml'

KEY_RE = re.compile(r"args\.get\(\s*['\"]([^'\"]+)['\"]")
KEY_RE2 = re.compile(r"args\[['\"]([^'\"]+)['\"]\]")

def collect_keys_from_file(path: Path):
    text = path.read_text(encoding='utf8')
    keys = set(KEY_RE.findall(text))
    keys.update(KEY_RE2.findall(text))
    # also look for self.args.get('foo', default) or self.args.get("foo", ...)
    keys.update(re.findall(r"self\.args\.get\(\s*['\"]([^'\"]+)['\"]", text))
    keys.update(re.findall(r"self\.args\[['\"]([^'\"]+)['\"]\]", text))
    return keys

def main():
    if not SAMPLE.exists():
        print(f"Sample config not found: {SAMPLE}")
        sys.exit(2)

    data = yaml.safe_load(SAMPLE.read_text(encoding='utf8')) or {}

    # collect base keys
    base_file = APPS_PY / 'base.py'
    base_keys = set()
    if base_file.exists():
        base_keys = collect_keys_from_file(base_file)

    problems = []

    for app_name, cfg in data.items():
        if not isinstance(cfg, dict):
            continue
        module = cfg.get('module')
        class_name = cfg.get('class')
        if not module:
            problems.append((app_name, 'missing module', None))
            continue
        module_file = APPS_PY / f"{module}.py"
        if not module_file.exists():
            problems.append((app_name, 'module file missing', str(module_file)))
            continue

        keys_in_code = collect_keys_from_file(module_file) | base_keys

        # keys present in sample config
        sample_keys = set(cfg.keys()) - {'module', 'class'}

        unknown = sample_keys - keys_in_code
        if unknown:
            problems.append((app_name, 'unknown options', sorted(unknown)))

    if not problems:
        print('OK: all sample_config options appear in code or base.py')
        return 0

    print('Found issues in sample_config:')
    for app, kind, detail in problems:
        print(f'- {app}: {kind}: {detail}')
    return 1


if __name__ == '__main__':
    raise SystemExit(main())
