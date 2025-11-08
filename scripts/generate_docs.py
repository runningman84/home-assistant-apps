#!/usr/bin/env python3
"""Generate per-app docs by parsing the app sources.

Produces `docs/<module>.md` files with basic header, description and an options table
derived from `self.args.get('key', default)` and `self.args['key']` usages.

Run from the repository root:
  python scripts/generate_docs.py
"""
from pathlib import Path
import ast
import textwrap
import sys
from typing import Dict, Any, List, Tuple

ROOT = Path(__file__).resolve().parents[1]
APPS_DIR = ROOT / 'apps'
DOCS_DIR = ROOT / 'docs'
DOCS_DIR.mkdir(parents=True, exist_ok=True)


def extract_from_file(path: Path) -> Tuple[str, str, Dict[str, Any]]:
    """Return (title, description, {key: default})"""
    text = path.read_text(encoding='utf8')
    try:
        tree = ast.parse(text)
    except Exception as e:
        print(f"Failed to parse {path}: {e}")
        return "", {}

    module_doc = ast.get_docstring(tree) or ""
    class_doc = ""
    class_name = None

    # collect keys -> defaults
    keys: Dict[str, Any] = {}

    # find classes and docstrings
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            class_name = node.name
            class_doc = ast.get_docstring(node) or ""
            break

    # If no docstrings, try to collect leading comment blocks
    if not module_doc and not class_doc:
        lines = text.splitlines()
        # module-level comment block at top
        mod_comments = []
        for ln in lines:
            s = ln.strip()
            if s.startswith('#'):
                mod_comments.append(s.lstrip('# ').rstrip())
            elif s == '':
                # allow blank lines at top
                continue
            else:
                break
        if mod_comments:
            module_doc = '\n'.join(mod_comments)
        else:
            # try comments immediately before the class definition
            class_lineno = None
            for node in tree.body:
                if isinstance(node, ast.ClassDef):
                    class_lineno = node.lineno
                    break
            if class_lineno:
                # gather comments above class
                pre = []
                # line numbers are 1-indexed
                for i in range(class_lineno - 2, max(class_lineno - 20, 0), -1):
                    line = lines[i].strip()
                    if line.startswith('#'):
                        pre.append(line.lstrip('# ').rstrip())
                    elif line == '':
                        continue
                    else:
                        break
                if pre:
                    class_doc = '\n'.join(reversed(pre))

    # walk AST for calls like self.args.get('foo', default) or self.args['foo']
    for node in ast.walk(tree):
        # self.args.get('key', default)
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
            attr = node.func
            if attr.attr == 'get':
                # check object is self.args or args
                val = attr.value
                is_args = False
                if isinstance(val, ast.Attribute) and getattr(val, 'attr', '') == 'args':
                    is_args = True
                if isinstance(val, ast.Name) and getattr(val, 'id', '') == 'args':
                    is_args = True
                if is_args and len(node.args) >= 1:
                    keynode = node.args[0]
                    if isinstance(keynode, ast.Constant) and isinstance(keynode.value, str):
                        key = keynode.value
                        default = None
                        if len(node.args) >= 2:
                            try:
                                default = ast.literal_eval(node.args[1])
                            except Exception:
                                default = '<complex>'
                        keys.setdefault(key, default)

        # self.args['key'] pattern
        if isinstance(node, ast.Subscript):
            val = node.value
            if isinstance(val, ast.Attribute) and getattr(val, 'attr', '') == 'args':
                sl = node.slice
                # support Constant (py3.8+) or Index/Constant
                key = None
                if isinstance(sl, ast.Constant) and isinstance(sl.value, str):
                    key = sl.value
                elif hasattr(ast, 'Index') and isinstance(sl, ast.Index) and isinstance(sl.value, ast.Constant) and isinstance(sl.value.value, str):
                    key = sl.value.value
                if key:
                    keys.setdefault(key, None)

    desc = class_doc.strip() if class_doc else (module_doc.strip() if module_doc else '')
    title = class_name or path.stem
    return title, desc, keys


def render_doc(module_path: Path, title: str, desc: str, keys: Dict[str, Any]) -> str:
    name = module_path.stem
    lines: List[str] = []
    lines.append(f"# {title}\n")
    if desc:
        lines.append(f"{desc}\n")

    lines.append("## Minimal apps.yaml snippet\n")
    lines.append("```yaml")
    lines.append(f"{name}:")
    lines.append(f"  module: {name}")
    # try to find class name from title
    class_name = title.split()[0] if title else ''
    if class_name:
        lines.append(f"  class: {class_name}")
    lines.append("  # options:")
    for k, default in sorted(keys.items()):
        if default is None:
            lines.append(f"  # {k}: <value>")
        else:
            lines.append(f"  # {k}: {default}")
    lines.append("```")

    if keys:
        lines.append('\n## Options\n')
        lines.append('| key | default |')
        lines.append('| --- | --- |')
        for k, default in sorted(keys.items()):
            lines.append(f"| `{k}` | `{default}` |")

    return '\n'.join(lines)


def main():
    apps = sorted(p for p in APPS_DIR.glob('*.py') if p.name != '__init__.py')
    changed = []
    for app in apps:
        title, desc, keys = extract_from_file(app)
        content = render_doc(app, title, desc, keys)
        out = DOCS_DIR / f"{app.stem}.md"
        if out.exists() and out.read_text(encoding='utf8').strip() == content.strip():
            continue
        out.write_text(content, encoding='utf8')
        changed.append(str(out))

    if changed:
        print('Generated/updated docs:')
        for c in changed:
            print(' -', c)
        return 0
    print('No changes; docs are up to date')
    return 0


if __name__ == '__main__':
    sys.exit(main())
