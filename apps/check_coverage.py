#!/usr/bin/env python3
"""Run tests with coverage and report overall percent.

Uses the repo .venv python if present, otherwise uses the current interpreter.
If tests fail, this script exits with the pytest exit code (non-zero) so pre-commit fails.
If tests pass but coverage is below threshold, it prints a warning but exits 0 (does not fail pre-commit).
"""
import os
import sys
import subprocess
import xml.etree.ElementTree as ET


REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
VENV_PY = os.path.join(REPO_ROOT, '.venv', 'bin', 'python')
PY = VENV_PY if os.path.exists(VENV_PY) else sys.executable

CMD = [
    PY,
    '-m',
    'pytest',
    '--maxfail=1',
    '-q',
    '--cov=apps',
    '--cov-report=term',
    '--cov-report=xml:coverage.xml',
    '--cov-report=html:htmlcov',
]


def run_tests():
    print('Running pytest with coverage using:', PY)
    proc = subprocess.run(CMD, cwd=REPO_ROOT)
    return proc.returncode


def parse_coverage_xml():
    xml_path = os.path.join(REPO_ROOT, 'coverage.xml')
    if not os.path.exists(xml_path):
        print('coverage.xml not found')
        return None
    try:
        tree = ET.parse(xml_path)
        root = tree.getroot()
        # Cobertura-like attribute
        line_rate = root.get('line-rate')
        if line_rate is not None:
            return float(line_rate) * 100.0
        # try coverage.py format: <coverage percent="..."> (not typical), search summary
        # fallback: scan packages for totals
        for child in root:
            if child.tag == 'packages':
                # not standard for coverage.xml from coverage.py
                continue
        return None
    except Exception as e:
        print('Failed to parse coverage.xml:', e)
        return None


def main():
    rc = run_tests()
    if rc != 0:
        # tests failed — propagate failure so pre-commit aborts
        print('Pytest failed (exit code {}), aborting coverage check.'.format(rc))
        sys.exit(rc)

    percent = parse_coverage_xml()
    if percent is None:
        print('Could not determine coverage percentage')
        sys.exit(0)

    msg = '\nTotal coverage: {:.2f}%'.format(percent)
    print(msg)
    if percent < 80.0:
        warn = '\n>>> COVERAGE WARNING: total coverage {:.2f}% is below threshold 80%. This will NOT fail pre-commit. <<<\n'.format(percent)
        # Print warning to stderr for visibility in pre-commit logs
        sys.stderr.write(warn)
        sys.stderr.flush()
    else:
        print('Coverage meets threshold.')

    # Never fail due to coverage percentage
    sys.exit(0)


if __name__ == '__main__':
    main()
