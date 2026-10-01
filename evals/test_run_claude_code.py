"""Checks how the optional Claude Code runner calls the CLI, without calling a model."""
import json
from pathlib import Path
import subprocess
import tempfile
import unittest
from unittest import mock

import run_claude_code


class RunBatchTests(unittest.TestCase):
    def run_with(self, stdout, batch_size=0):
        calls = []

        def fake_run(cmd, cwd, input, capture_output, timeout, env):
            calls.append((cmd, input.decode('utf-8')))
            body = stdout(json.loads(input.decode('utf-8').split('\n\n', 1)[1]))
            return subprocess.CompletedProcess(cmd, 0, body.encode('utf-8'), b'')

        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp)
            (out / 'bibung-prompt.txt').write_text('一行目\n二行目', encoding='utf-8')
            inputs = [{'id': f'X{i}', 'request': '推敲して', 'text': '本文'} for i in range(3)]
            (out / 'inputs.json').write_text(json.dumps(inputs, ensure_ascii=False), encoding='utf-8')
            with mock.patch.object(run_claude_code.subprocess, 'run', fake_run):
                info = run_claude_code.run_condition('claude', 'bibung', out, out, None, 20, 60, batch_size)
            outputs = json.loads((out / 'bibung.json').read_text(encoding='utf-8'))
        return calls, info, outputs

    @staticmethod
    def envelope(batch):
        outputs = [{'id': c['id'], 'revised': c['text'], 'reasons': [], 'queries': []} for c in batch]
        return json.dumps({'structured_output': {'outputs': outputs}, 'modelUsage': {}})

    def test_prompt_goes_through_stdin_not_argv(self):
        calls, _, outputs = self.run_with(self.envelope)
        cmd, stdin = calls[0]
        self.assertFalse(any('\n' in arg for arg in cmd))
        self.assertIn('--output-format', cmd)
        self.assertTrue(stdin.startswith('/bibung 一行目\n二行目'))
        self.assertEqual([o['id'] for o in outputs], ['X0', 'X1', 'X2'])

    def test_batches_are_merged_in_order(self):
        calls, info, outputs = self.run_with(self.envelope, batch_size=2)
        self.assertEqual(len(calls), 2)
        self.assertEqual([b['ids'] for b in info['batches']], [['X0', 'X1'], ['X2']])
        self.assertEqual([o['id'] for o in outputs], ['X0', 'X1', 'X2'])

    def test_plain_text_reply_is_reported(self):
        with self.assertRaisesRegex(RuntimeError, 'did not return JSON'):
            self.run_with(lambda batch: '## X0\n改稿文')


if __name__ == '__main__':
    unittest.main()
