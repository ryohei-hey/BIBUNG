"""Offline checks for this skill package, not a prose-quality or AI detector.

Two modes:
  python evals/validate.py                  # repository: skill files + docs + evals
  python evals/validate.py --installed --root ~/.claude/skills/bibang
                                            # a deployed copy or zip root: skill files only
"""
from __future__ import annotations

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
import sys
from urllib.parse import unquote, urlsplit

import yaml

# What an installed copy (Codex, Claude Code, claude.ai zip, Skills API) must contain.
SKILL_FILES = (
    'SKILL.md', 'LICENSE', 'references/japanese-editing.md',
    'references/scientific-fidelity.md', 'references/genre-guidance.md',
    'references/sources.md',
)
# Everything else the repository ships for humans, evaluation and CI.
REPO_FILES = (
    'README.md', 'CHANGELOG.md', 'CONTRIBUTING.md', '.gitignore', '.gitattributes',
    'agents/openai.yaml', 'examples/paper.md', 'examples/grant.md',
    'examples/explanation.md', 'evals/cases.json', 'evals/README.md',
    'evals/RESULTS.md', 'evals/prepare.py', 'evals/run_claude_code.py',
    'evals/test_validate.py', 'evals/requirements.txt', '.github/workflows/validate.yml',
)
# Folders an installed copy may link to from SKILL.md (README's install steps copy these).
INSTALLED_TOP_LEVEL = {'references', 'agents', 'LICENSE'}
# Agent Skills specification fields. claude.ai and the Skills API reject anything else.
PORTABLE_KEYS = {'name', 'description', 'license', 'compatibility', 'metadata', 'allowed-tools'}
NAME_RE = re.compile(r'[a-z0-9]+(?:-[a-z0-9]+)*')
MIN_CASES = {'rewrite': 12, 'good': 6, 'fragile': 6}
GENRES = {'paper', 'grant', 'explanation'}
HASHED_FILES = ('SKILL.md', 'references/*.md', 'evals/cases.json')


def frontmatter(text: str) -> tuple[dict, str]:
    match = re.match(r'\A---\r?\n(.*?)\r?\n---(?:\r?\n|$)', text, re.S)
    if not match:
        raise ValueError('YAML frontmatter is missing or unclosed')
    data = yaml.safe_load(match[1])
    if not isinstance(data, dict):
        raise ValueError('YAML frontmatter must be a mapping')
    return data, text[match.end():]


def check_frontmatter(data: dict, body: str) -> list[str]:
    errors = []
    extra = sorted(set(data) - PORTABLE_KEYS)
    if extra:
        errors.append(f'Non-portable frontmatter keys (rejected by claude.ai / Skills API upload): {extra}')
    name = data.get('name')
    if name != 'bibang' or not NAME_RE.fullmatch(name) or len(name) > 64:
        errors.append('Skill name must be "bibang" (lowercase letters, digits, single hyphens, <=64 chars)')
    desc = data.get('description')
    if not isinstance(desc, str) or not desc.strip() or len(desc) > 1024 or re.search(r'<[^>]+>', desc):
        errors.append('Description must be a nonempty string of at most 1024 characters without XML tags')
    if data.get('license') != 'MIT':
        errors.append('Skill license must be MIT')
    meta = data.get('metadata')
    if not isinstance(meta, dict) or any(not isinstance(v, str) for v in meta.values()):
        errors.append('metadata must map string keys to string values')
    else:
        version = meta.get('version', '')
        if not re.fullmatch(r'\d+\.\d+\.\d+', version):
            errors.append('Skill metadata.version must be a quoted semantic version')
    if body.count('\n') > 500:
        errors.append('SKILL.md body must stay under 500 lines')
    if re.search(r'\$ARGUMENTS|\$bibang|/bibang', body):
        errors.append('SKILL.md body must not contain platform-specific invocation syntax')
    return errors


def check_openai_yaml(path: Path) -> list[str]:
    errors = []
    try:
        ui = yaml.safe_load(path.read_text(encoding='utf-8'))
        interface = ui['interface']
        for key in ('display_name', 'short_description', 'default_prompt'):
            if not isinstance(interface.get(key), str) or not interface[key].strip():
                errors.append(f'UI interface.{key} must be a nonempty string')
        if '$bibang' not in interface.get('default_prompt', ''):
            errors.append('UI default_prompt must mention $bibang')
        if ui.get('policy', {}).get('allow_implicit_invocation') is not True:
            errors.append('Implicit invocation must remain enabled')
    except (OSError, ValueError, yaml.YAMLError, KeyError, TypeError) as exc:
        errors.append(f'agents/openai.yaml: {exc}')
    return errors


def package_files(root: Path):
    for path in sorted(root.rglob('*')):
        rel = path.relative_to(root)
        if any(p in {'.git', '.local', '.venv', '__pycache__', 'runs', 'dist'} for p in rel.parts):
            continue
        if path.is_file():
            yield path


def check_documents(root: Path, installed: bool) -> list[str]:
    errors = []
    for path in package_files(root):
        if path.suffix not in {'.md', '.yml', '.yaml'}:
            continue
        text = path.read_text(encoding='utf-8')
        rel = path.relative_to(root)
        if re.search(r'\b(?:TODO|TBD|FIXME)\b|<YOUR[-_][A-Z_]+>', text):
            errors.append(f'{rel}: unfinished scaffold marker')
        if path.suffix in {'.yml', '.yaml'}:
            try:
                yaml.safe_load(text)
            except yaml.YAMLError as exc:
                errors.append(f'{rel}: invalid YAML: {exc}')
            continue
        # Repository prose uses inline Markdown links; code examples are excluded.
        prose = re.sub(r'^```[^\n]*\n.*?^```\s*$', '', text, flags=re.M | re.S)
        for target in re.findall(r'\[[^\]\n]*\]\(([^\s)]+)\)', prose):
            target = target.strip('<>')
            parts = urlsplit(target)
            if parts.scheme or parts.netloc or not parts.path:
                continue
            resolved = (path.parent / unquote(parts.path)).resolve()
            if not resolved.is_relative_to(root.resolve()) or not resolved.exists():
                errors.append(f'{rel}: broken or out-of-package link: {target}')
                continue
            if rel.name == 'SKILL.md' and rel.parent == Path('.'):
                top = resolved.relative_to(root.resolve()).parts[0]
                if top not in INSTALLED_TOP_LEVEL:
                    errors.append(f'SKILL.md: link leaves the installed set {sorted(INSTALLED_TOP_LEVEL)}: {target}')
    return errors


def check_cases(cases: list) -> list[str]:
    errors = []
    if not isinstance(cases, list) or any(not isinstance(c, dict) for c in cases):
        return ['evals/cases.json must be an array of objects']
    counts = Counter(c.get('group') for c in cases)
    unknown = sorted(str(g) for g in set(counts) - set(MIN_CASES))
    if unknown:
        errors.append(f'Unknown case groups: {unknown}')
    short = {g: n for g, n in MIN_CASES.items() if counts[g] < n}
    if short:
        errors.append(f'Too few cases: need at least {short}, have {dict(counts)}')
    ids = [c.get('id') for c in cases]
    if len(ids) != len(set(ids)):
        errors.append('Duplicate case IDs')
    for c in cases:
        cid = c.get('id', 'unknown')
        for key in ('id', 'group', 'genre', 'request', 'text', 'invariants', 'criteria'):
            if not c.get(key):
                errors.append(f'{cid}: missing case field {key}')
        if c.get('genre') not in GENRES:
            errors.append(f'{cid}: invalid genre')
        for flag in ('protected', 'expect_unchanged'):
            if flag in c and not isinstance(c[flag], bool):
                errors.append(f'{cid}: {flag} must be true or false')
    return errors


def validate(root: Path, installed: bool = False) -> list[str]:
    errors = []
    required = SKILL_FILES if installed else SKILL_FILES + REPO_FILES
    for name in required:
        if not (root / name).is_file():
            errors.append(f'Missing required file: {name}')
    if installed and root.resolve().name != 'bibang':
        errors.append(f'Installed skill folder must be named bibang, not {root.resolve().name}')
    try:
        data, body = frontmatter((root / 'SKILL.md').read_text(encoding='utf-8'))
        errors += check_frontmatter(data, body)
    except (OSError, ValueError, yaml.YAMLError, AttributeError) as exc:
        errors.append(f'SKILL.md: {exc}')
    ui_path = root / 'agents/openai.yaml'
    if ui_path.is_file():
        errors += check_openai_yaml(ui_path)
    errors += check_documents(root, installed)
    if not installed:
        try:
            errors += check_cases(json.loads((root / 'evals/cases.json').read_text(encoding='utf-8')))
        except (OSError, ValueError) as exc:
            errors.append(f'evals/cases.json: {exc}')
    return errors


def protected_spans(text: str) -> Counter:
    """Conservative extraction for `protected` cases only; not a general Markdown parser."""
    text = text.replace('\r\n', '\n')
    patterns = (
        r'\A---\n.*?\n---', r'^```[^\n]*\n.*?^```',
        r'\$[^$\n]+\$', r'(?<!\w)@[A-Za-z][\w:.-]*',
        r'\{#[\w:.-]+\}', r'^>[^\n]*',
        r'\]\(([^)\s]+)\)',
    )
    spans = []
    for pattern in patterns:
        spans.extend(re.findall(pattern, text, re.M | re.S))
    return Counter(spans)


def check_outputs(cases: list[dict], outputs: list[dict]) -> list[str]:
    errors = []
    if not isinstance(outputs, list) or any(not isinstance(o, dict) for o in outputs):
        return ['Output must be an array of objects']
    ids = [o.get('id') for o in outputs]
    if Counter(ids) != Counter(c['id'] for c in cases):
        errors.append('Output case IDs must match inputs exactly once')
    by_id = {o.get('id'): o for o in outputs}
    for c in cases:
        o = by_id.get(c['id'], {})
        if not isinstance(o.get('revised'), str) or not o['revised'].strip():
            errors.append(f'{c["id"]}: missing revised text')
            continue
        for key in ('reasons', 'queries'):
            if not isinstance(o.get(key), list) or any(not isinstance(v, str) for v in o[key]):
                errors.append(f'{c["id"]}: {key} must be an array of strings')
        if c.get('protected') and protected_spans(c['text']) != protected_spans(o['revised']):
            errors.append(f'{c["id"]}: protected Markdown/Quarto spans changed')
        if c.get('expect_unchanged') and o['revised'].replace('\r\n', '\n') != c['text'].replace('\r\n', '\n'):
            errors.append(f'{c["id"]}: review-only request but revised text differs from the input')
    return errors


def good_group_identity(cases: list[dict], outputs: list[dict]) -> tuple[int, int]:
    """Count good-group outputs identical to their input (information only)."""
    by_id = {o.get('id'): o for o in outputs if isinstance(o, dict)}
    good = [c for c in cases if c.get('group') == 'good']
    kept = sum(1 for c in good if by_id.get(c['id'], {}).get('revised') == c['text'])
    return kept, len(good)


def print_hashes(root: Path) -> None:
    files = ['SKILL.md'] + sorted(p.relative_to(root).as_posix() for p in (root / 'references').glob('*.md'))
    if (root / 'evals/cases.json').is_file():
        files.append('evals/cases.json')
    for rel in files:
        data = (root / rel).read_bytes().replace(b'\r\n', b'\n')
        print(f'{hashlib.sha256(data).hexdigest()}  {rel}')


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1])
    parser.add_argument('--installed', action='store_true', help='Validate a deployed copy or zip root (skill files only)')
    parser.add_argument('--outputs', type=Path, help='Check output shape, protected spans and review-only cases')
    parser.add_argument('--cases', type=Path, help='cases.json the outputs were produced from (default: evals/cases.json)')
    parser.add_argument('--sha256', action='store_true', help='Print SHA-256 of SKILL.md, references/*.md and evals/cases.json over LF-normalized bytes')
    args = parser.parse_args()
    if args.sha256:
        print_hashes(args.root)
        return 0
    errors = validate(args.root, installed=args.installed)
    if args.outputs:
        try:
            cases_path = args.cases or args.root / 'evals/cases.json'
            cases = json.loads(cases_path.read_text(encoding='utf-8'))
            outputs = json.loads(args.outputs.read_text(encoding='utf-8'))
            errors += check_outputs(cases, outputs)
            kept, total = good_group_identity(cases, outputs)
            print(f'good-group outputs identical to input: {kept}/{total} (information only; synonymous edits are not errors)')
        except (OSError, ValueError, TypeError) as exc:
            errors.append(f'Outputs: {exc}')
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)
    scope = 'installed skill' if args.installed else 'package structure'
    print('FAIL' if errors else f'PASS: {scope}' + (' and output shape' if args.outputs else ''))
    print('Scientific meaning and writing quality require separate review.')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
