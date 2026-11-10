#!/usr/bin/env python3
"""Tests for markdown_formatter.py. Run: python3 marks-guardrails/hooks/test_markdown_formatter.py"""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HOOK = Path(__file__).with_name("markdown_formatter.py")
UNTAGGED = "# Doc\n\n```\nprint('hi')\n```\n"


def run_hook(file_path):
    return subprocess.run([sys.executable, str(HOOK)], capture_output=True, text=True,
                          input=json.dumps({"tool_input": {"file_path": str(file_path)}}))


class MarkdownFormatter(unittest.TestCase):
    def setUp(self):
        self.root = Path(tempfile.mkdtemp())
        self.doc = self.root / "docs" / "lab.md"
        self.doc.parent.mkdir()
        self.doc.write_text(UNTAGGED)

    def test_adds_a_language_tag_to_an_untagged_fence(self):
        r = run_hook(self.doc)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertNotIn("```\nprint", self.doc.read_text())

    def test_leaves_files_alone_under_a_no_markdown_format_marker(self):
        (self.root / ".no-markdown-format").write_text("")
        r = run_hook(self.doc)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(self.doc.read_text(), UNTAGGED)
        self.assertEqual(r.stdout, "")

    def test_ignores_non_markdown_files(self):
        other = self.root / "notes.txt"
        other.write_text(UNTAGGED)
        self.assertEqual(run_hook(other).returncode, 0)
        self.assertEqual(other.read_text(), UNTAGGED)


if __name__ == "__main__":
    unittest.main()
