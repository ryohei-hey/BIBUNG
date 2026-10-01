"""Run the evaluation cases through Claude Code non-interactively (optional helper).

Creates a blinded input bundle with prepare.py, builds two isolated project folders
(one with BIBUNG under .claude/skills/bibung, one without any skill), runs each
condition with `claude -p` (in one session, or in batches with --batch-size), and
checks the output shape with validate.py.
It does not judge scientific meaning or writing quality; review the outputs by hand
as described in evals/README.md.

Example:
    python evals/run_claude_code.py evals/runs/trial-01
    python evals/run_claude_code.py evals/runs/trial-02 --condition bibung --model claude-sonnet-5
    python evals/run_claude_code.py evals/runs/trial-03 --batch-size 6
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys

sys.path.insert(0, str(Path(__file__).resolve().parent))
from prepare import prepare  # noqa: E402
from validate import check_outputs  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
SKILL_FILES = ('SKILL.md', 'LICENSE', 'references')
OUTPUT_SCHEMA = {
    'type': 'object',
    'properties': {
        'outputs': {
            'type': 'array',
            'items': {
                'type': 'object',
                'properties': {
                    'id': {'type': 'string'},
                    'revised': {'type': 'string'},
                    'reasons': {'type': 'array', 'items': {'type': 'string'}},
                    'queries': {'type': 'array', 'items': {'type': 'string'}},
                },
                'required': ['id', 'revised', 'reasons', 'queries'],
            },
        },
    },
    'required': ['outputs'],
}


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def build_projects(out: Path) -> dict[str, Path]:
    projects = {}
    baseline = out / 'project-baseline' / '.claude'
    baseline.mkdir(parents=True)
    projects['baseline'] = baseline.parent
    skill = out / 'project-bibung' / '.claude' / 'skills' / 'bibung'
    skill.mkdir(parents=True)
    for name in SKILL_FILES:
        src = ROOT / name
        if src.is_dir():
            shutil.copytree(src, skill / name)
        else:
            shutil.copy2(src, skill / name)
    projects['bibung'] = skill.parents[2]
    return projects


def run_batch(claude: str, condition: str, project: Path, out: Path, inputs: list[dict],
              label: str, model: str | None, max_turns: int, timeout: int) -> tuple[list, dict]:
    prompt_file = out / f'{condition}-prompt.txt'
    instruction = prompt_file.read_text(encoding='utf-8').strip()
    if condition == 'bibung':
        instruction = '/bibung ' + instruction
    instruction += ('\n各入力はこの後に続くJSON配列にあります。'
                    '応答は指定の構造化出力のみとし、改稿文以外の説明文を加えないでください。')
    # The prompt goes through stdin, not argv: on Windows the npm shim (claude.cmd) cuts
    # arguments at the first newline and silently drops every flag after it.
    stdin = instruction + '\n\n' + json.dumps(inputs, ensure_ascii=False, indent=2) + '\n'
    cmd = [claude, '-p', '--output-format', 'json',
           '--json-schema', json.dumps(OUTPUT_SCHEMA, ensure_ascii=False),
           '--setting-sources', 'project', '--permission-mode', 'default',
           '--max-turns', str(max_turns), '--no-session-persistence']
    if model:
        cmd += ['--model', model]
    env = {k: v for k, v in os.environ.items() if not k.startswith('CLAUDE')}
    proc = subprocess.run(cmd, cwd=project, input=stdin.encode('utf-8'),
                          capture_output=True, timeout=timeout, env=env)
    (out / f'{label}-stderr.txt').write_bytes(proc.stderr)
    raw_path = out / f'{label}-raw.json'
    raw_path.write_bytes(proc.stdout)
    if proc.returncode != 0:
        raise RuntimeError(f'{label}: claude exited with {proc.returncode}; see {raw_path.name} and stderr')
    try:
        raw = json.loads(proc.stdout.decode('utf-8'))
    except json.JSONDecodeError:
        # Usually means the flags never reached the CLI (e.g. a wrapper that mangles argv).
        raise RuntimeError(f'{label}: claude did not return JSON (plain text in {raw_path.name}); '
                           'check that --output-format reached the CLI') from None
    outputs = raw.get('structured_output')
    if isinstance(outputs, dict):
        outputs = outputs.get('outputs')
    if outputs is None:
        text = raw.get('result', '')
        start, end = text.find('['), text.rfind(']')
        if start < 0 or end < 0:
            raise RuntimeError(f'{label}: no JSON array in result; see {raw_path.name}')
        outputs = json.loads(text[start:end + 1])
    usage_by_model = raw.get('modelUsage') or {}
    main_model = max(usage_by_model, key=lambda m: usage_by_model[m].get('outputTokens', 0), default=None)
    return outputs, {
        'model': main_model,
        'model_usage': {m: u.get('outputTokens') for m, u in usage_by_model.items()},
        'num_turns': raw.get('num_turns'),
        'duration_ms': raw.get('duration_ms'),
        'usage': raw.get('usage'),
        'session_id': raw.get('session_id'),
    }


def run_condition(claude: str, condition: str, project: Path, out: Path, model: str | None,
                  max_turns: int, timeout: int, batch_size: int) -> dict:
    inputs = json.loads((out / 'inputs.json').read_text(encoding='utf-8'))
    size = batch_size if batch_size > 0 else len(inputs)
    batches = [inputs[i:i + size] for i in range(0, len(inputs), size)]
    outputs, infos = [], []
    for n, batch in enumerate(batches, 1):
        label = condition if len(batches) == 1 else f'{condition}-{n:02d}'
        if len(batches) > 1:
            print(f'  batch {n}/{len(batches)}: {batch[0]["id"]}-{batch[-1]["id"]}', flush=True)
        batch_outputs, info = run_batch(claude, condition, project, out, batch, label,
                                        model, max_turns, timeout)
        outputs += batch_outputs
        infos.append(info | {'ids': [c['id'] for c in batch]})
    (out / f'{condition}.json').write_text(
        json.dumps(outputs, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    if len(infos) == 1:
        return {k: v for k, v in infos[0].items() if k != 'ids'}
    return {'model': infos[0]['model'], 'batch_size': size, 'batches': infos}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument('out', type=Path, help='A new directory, normally under evals/runs/')
    parser.add_argument('--claude', default='claude', help='Claude Code executable (default: claude on PATH)')
    parser.add_argument('--condition', choices=('both', 'bibung', 'baseline'), default='both')
    parser.add_argument('--model', help='Model alias or ID passed to claude --model (default: session default)')
    parser.add_argument('--max-turns', type=int, default=20)
    parser.add_argument('--timeout', type=int, default=1800, help='Seconds per claude session')
    parser.add_argument('--batch-size', type=int, default=0,
                        help='Cases per claude session (default 0: all cases in one session)')
    args = parser.parse_args()

    claude = shutil.which(args.claude) or args.claude
    if not Path(claude).exists():
        print(f'ERROR: Claude Code executable not found: {args.claude}', file=sys.stderr)
        return 2
    out = args.out.resolve()
    prepare(out)
    projects = build_projects(out)
    cases = json.loads((ROOT / 'evals/cases.json').read_text(encoding='utf-8'))
    conditions = ('bibung', 'baseline') if args.condition == 'both' else (args.condition,)
    metadata = {
        'claude_executable': claude,
        'model_requested': args.model,
        'conditions': {},
        'skill_sha256': {f'{name}': sha256(ROOT / name) for name in ('SKILL.md',)}
        | {f'references/{p.name}': sha256(p) for p in sorted((ROOT / 'references').glob('*.md'))}
        | {'evals/cases.json': sha256(ROOT / 'evals/cases.json')},
        'note': 'Structure-only run; scientific meaning and writing quality need manual review (evals/README.md).',
    }
    errors = []
    for condition in conditions:
        print(f'Running {condition} ...', flush=True)
        info = run_condition(claude, condition, projects[condition], out, args.model, args.max_turns,
                             args.timeout, args.batch_size)
        outputs = json.loads((out / f'{condition}.json').read_text(encoding='utf-8'))
        shape_errors = check_outputs(cases, outputs)
        info['shape_errors'] = shape_errors
        metadata['conditions'][condition] = info
        errors += [f'{condition}: {e}' for e in shape_errors]
        print(f'  {condition}: {len(outputs)} outputs, {len(shape_errors)} shape errors, model={info.get("model")}')
    (out / 'metadata.json').write_text(json.dumps(metadata, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    for error in errors:
        print(f'ERROR: {error}', file=sys.stderr)
    print('Outputs saved to', out)
    print('Scientific meaning and writing quality require separate review.')
    return 1 if errors else 0


if __name__ == '__main__':
    raise SystemExit(main())
