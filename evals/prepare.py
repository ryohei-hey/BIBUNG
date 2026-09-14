"""Prepare blinded input bundles without calling a model or changing the skill."""
import argparse
import json
from pathlib import Path
import shutil


def prepare(out: Path) -> None:
    root = Path(__file__).resolve().parents[1]
    out.mkdir(parents=True, exist_ok=False)
    cases = json.loads((root / 'evals/cases.json').read_text(encoding='utf-8'))
    inputs = [{k: c[k] for k in ('id', 'request', 'text')} for c in cases]
    (out / 'inputs.json').write_text(json.dumps(inputs, ensure_ascii=False, indent=2)+'\n', encoding='utf-8')
    # Snapshot the corpus so results stay checkable after cases are added later.
    shutil.copyfile(root / 'evals/cases.json', out / 'cases.snapshot.json')
    instruction = ('各入力は独立した依頼です。科学的な意味を保ち、各入力のrequestに従って推敲してください。'
                   '他の入力の情報を転用しないでください。'
                   '出力はid、revised（改稿文。本文を直さない依頼では原文をそのまま入れる）、'
                   'reasons（主要な修正理由の配列）、queries（要確認事項の配列）を持つオブジェクトのJSON配列としてください。'
                   '評価基準や正解例は読まず、外部検索は行わないでください。\n')
    (out / 'baseline-prompt.txt').write_text(instruction, encoding='utf-8')
    (out / 'bibung-prompt.txt').write_text(
        'BIBUNGのSKILL.mdと、そこから参照されるreferences/の資料だけを読み、そのスキルを適用してください。'
        'README.md、examples/、evals/は読まないでください。\n'+instruction,
        encoding='utf-8')
    print(f'Prepared {len(inputs)} cases in {out}. No model was called.')


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('out', type=Path, help='A new directory, normally under evals/runs/')
    prepare(parser.parse_args().out)
