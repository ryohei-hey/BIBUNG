"""Behavioral checks of the release validator, not text-editing quality."""
import copy
import json
from pathlib import Path
import shutil
import tempfile
import unittest

from validate import (SKILL_FILES, check_cases, check_frontmatter, check_outputs, frontmatter,
                      good_group_identity, validate)

ROOT = Path(__file__).resolve().parents[1]
CASES = json.loads((ROOT / 'evals/cases.json').read_text(encoding='utf-8'))
IGNORE = shutil.ignore_patterns('.local', '.git', '.venv', 'runs', 'dist', '__pycache__')


def case(case_id):
    return next(c for c in CASES if c['id'] == case_id)


class FrontmatterTests(unittest.TestCase):
    def test_missing_and_invalid_frontmatter(self):
        for text in ('plain text', '---\nname: [broken\n---\n'):
            with self.assertRaises(Exception):
                frontmatter(text)

    def test_shipped_frontmatter_is_portable(self):
        data, body = frontmatter((ROOT / 'SKILL.md').read_text(encoding='utf-8'))
        self.assertEqual(check_frontmatter(data, body), [])

    def test_non_portable_key_and_invocation_syntax_are_rejected(self):
        data, body = frontmatter((ROOT / 'SKILL.md').read_text(encoding='utf-8'))
        bad = dict(data, **{'argument-hint': '[text]'})
        self.assertTrue(any('Non-portable' in e for e in check_frontmatter(bad, body)))
        self.assertTrue(any('platform-specific' in e for e in check_frontmatter(data, body + '\n$ARGUMENTS\n')))
        self.assertTrue(check_frontmatter(dict(data, name='Bibang'), body))
        self.assertTrue(check_frontmatter(dict(data, description='<skill>x</skill>'), body))


class CaseCorpusTests(unittest.TestCase):
    def test_minimums_allow_growth_but_not_shrinkage(self):
        self.assertEqual(check_cases(CASES), [])
        extra = CASES + [dict(case('G01'), id='G99')]
        self.assertEqual(check_cases(extra), [])
        fewer = [c for c in CASES if c['group'] != 'good']
        self.assertTrue(any('Too few cases' in e for e in check_cases(fewer)))
        odd = CASES + [dict(case('G01'), id='Z01', group='mystery')]
        self.assertTrue(any('Unknown case groups' in e for e in check_cases(odd)))


class OutputTests(unittest.TestCase):
    def test_quarto_protection_and_prose_edit(self):
        cases = [case('F06')]
        outputs = [dict(id='F06', revised=cases[0]['text'].replace('結果の提示を @fig-flow において行う', '結果を @fig-flow に示す'), reasons=[], queries=[])]
        self.assertEqual(check_outputs(cases, outputs), [])
        for old, new in [('format: html', 'format: pdf'), ('n <- 80', 'n <- 90'),
                         ('@sample2025', '@sample2026'), ('figures/flow.png', 'flow.svg'),
                         ('$p < 0.05$', '$p < 0.01$')]:
            bad = copy.deepcopy(outputs)
            bad[0]['revised'] = bad[0]['revised'].replace(old, new)
            self.assertTrue(check_outputs(cases, bad), old)

    def test_citation_keys_are_protected_by_flag(self):
        cases = [case('N04')]
        self.assertTrue(cases[0].get('protected'))
        ok = [dict(id='N04', revised=cases[0]['text'].replace('本研究では、服薬中断の理由についても面接で調べる。', '理由も面接で調べる。'), reasons=[], queries=[])]
        self.assertEqual(check_outputs(cases, ok), [])
        dropped = [dict(id='N04', revised=cases[0]['text'].replace(' [@sato2019]', ''), reasons=[], queries=[])]
        self.assertTrue(check_outputs(cases, dropped))

    def test_review_only_case_must_be_unchanged(self):
        cases = [case('N06')]
        same = [dict(id='N06', revised=cases[0]['text'], reasons=[], queries=['要確認：人数'])]
        self.assertEqual(check_outputs(cases, same), [])
        edited = [dict(id='N06', revised=cases[0]['text'].replace('解析の実施を行った', '解析した'), reasons=[], queries=[])]
        self.assertTrue(any('review-only' in e for e in check_outputs(cases, edited)))

    def test_duplicate_and_missing_outputs(self):
        cases = [dict(id='X', text='example')]
        output = dict(id='X', revised='example', reasons=[], queries=[])
        self.assertTrue(check_outputs(cases, []))
        self.assertTrue(check_outputs(cases, [output, output]))

    def test_good_group_identity_count(self):
        cases = [case('G01'), case('G02')]
        outputs = [dict(id='G01', revised=cases[0]['text'], reasons=[], queries=[]),
                   dict(id='G02', revised='変えた', reasons=[], queries=[])]
        self.assertEqual(good_group_identity(cases, outputs), (1, 2))


class PackageTests(unittest.TestCase):
    def test_repository_passes(self):
        self.assertEqual(validate(ROOT), [])

    def test_broken_link_and_scaffold(self):
        with tempfile.TemporaryDirectory(prefix='bibang-validate-') as tmp:
            target = Path(tmp).resolve() / 'package'
            shutil.copytree(ROOT, target, ignore=IGNORE)
            self.assertEqual(validate(target), [])
            with (target / 'README.md').open('a', encoding='utf-8') as handle:
                handle.write('\n[broken](missing-file.md)\n' + 'TO' + 'DO' + '\n')
            errors = validate(target)
            self.assertTrue(any('broken or out-of-package link' in e for e in errors))
            self.assertTrue(any('unfinished scaffold' in e for e in errors))

    def test_skill_links_stay_inside_installed_set(self):
        with tempfile.TemporaryDirectory(prefix='bibang-validate-') as tmp:
            target = Path(tmp).resolve() / 'package'
            shutil.copytree(ROOT, target, ignore=IGNORE)
            with (target / 'SKILL.md').open('a', encoding='utf-8') as handle:
                handle.write('\n[例](examples/paper.md)\n')
            self.assertTrue(any('leaves the installed set' in e for e in validate(target)))

    def test_installed_copy_validates_without_repo_files(self):
        with tempfile.TemporaryDirectory(prefix='bibang-installed-') as tmp:
            dest = Path(tmp).resolve() / 'bibang'
            for name in SKILL_FILES:
                (dest / name).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(ROOT / name, dest / name)
            shutil.copytree(ROOT / 'agents', dest / 'agents')
            self.assertEqual(validate(dest, installed=True), [])
            self.assertTrue(any('Missing required file' in e for e in validate(dest, installed=False)))
            renamed = dest.with_name('bibang-main')
            dest.rename(renamed)
            self.assertTrue(any('must be named bibang' in e for e in validate(renamed, installed=True)))


if __name__ == '__main__':
    unittest.main()
