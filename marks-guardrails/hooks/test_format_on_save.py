#!/usr/bin/env python3
"""Tests for format-on-save.sh. Run: python3 marks-guardrails/hooks/test_format_on_save.py"""
import json
import os
import subprocess
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name("format-on-save.sh")


class FormatOnSave(unittest.TestCase):
    """A stub `prettier` on PATH records each file it is asked to format."""

    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.bin = self.root / "bin"
        self.bin.mkdir()
        self.calls = self.root / "calls"
        stub = self.bin / "prettier"
        stub.write_text(f'#!/usr/bin/env bash\necho "$2" >> "{self.calls}"\n')
        stub.chmod(0o755)
        self.repo = self.root / "repo"
        (self.repo / "docs").mkdir(parents=True)

    def run_hook(self, file_path):
        file_path.write_text("x\n")
        env = {**os.environ, "PATH": f"{self.bin}:{os.environ['PATH']}"}
        r = subprocess.run([str(HOOK)], capture_output=True, text=True, env=env,
                           input=json.dumps({"tool_input": {"file_path": str(file_path)}}))
        self.assertEqual(r.returncode, 0, r.stderr)
        return self.calls.read_text().split() if self.calls.exists() else []

    def test_markdown_without_prettier_config_is_left_alone(self):
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [])

    def test_other_types_without_prettier_config_are_still_formatted(self):
        for name in ("a.ts", "a.json", "a.yaml"):
            src = self.repo / "docs" / name
            self.assertIn(str(src), self.run_hook(src))

    def test_a_prettierrc_in_a_parent_directory_turns_prettier_on(self):
        (self.repo / ".prettierrc").write_text("{}\n")
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [str(doc)])

    def test_a_prettier_key_in_package_json_turns_prettier_on(self):
        (self.repo / "package.json").write_text(json.dumps({"prettier": {}}))
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [str(doc)])

    def test_a_package_json_without_a_prettier_key_does_not(self):
        (self.repo / "package.json").write_text(json.dumps({"name": "x"}))
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [])

    def test_prettier_config_js_turns_prettier_on(self):
        (self.repo / "prettier.config.js").write_text("module.exports = {}\n")
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [str(doc)])

    def test_no_markdown_format_skips_markdown_even_with_a_config(self):
        (self.repo / ".prettierrc").write_text("{}\n")
        (self.repo / ".no-markdown-format").write_text("")
        doc = self.repo / "docs" / "a.md"
        self.assertEqual(self.run_hook(doc), [])

    def test_no_markdown_format_does_not_skip_other_files(self):
        (self.repo / ".prettierrc").write_text("{}\n")
        (self.repo / ".no-markdown-format").write_text("")
        src = self.repo / "docs" / "a.ts"
        self.assertEqual(self.run_hook(src), [str(src)])


if __name__ == "__main__":
    unittest.main()
