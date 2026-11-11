import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from _util import SCRIPTS

import check_note as K

BLOG_FM = """---
title: "Prompt Caching"
topic: "LLM Engineering"
tags: [llm, caching]
created: "2026-11-11"
summary: "Reuse the processed prompt prefix."
source_type: blog
{extra}
---

# Prompt Caching

| a | b |
|---|---|
| 1 | 2 |
"""

EXPLAINER = """<!doctype html><html><head><title>Cache lookup</title></head><body>
<nav class="tabs"><a class="tab" href="#explain">Cache lookup</a></nav>
<section class="panel" id="explain"><h2>Cache lookup</h2>
<div class="flow"><div class="node">Prompt</div><div class="arrow"></div><div class="node">Cache</div></div>
</section></body></html>"""


class CheckNoteTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.dir = Path(self.tmp.name)

    def tearDown(self):
        self.tmp.cleanup()

    def check(self, text, name="Prompt_Caching.md"):
        p = self.dir / name
        p.write_text(text)
        errors, warnings = [], []
        K.check_markdown(p, errors, warnings)
        return errors

    def test_blog_single_ok(self):
        self.assertEqual(self.check(BLOG_FM.format(extra='source_url: "https://ex.com/a"')), [])

    def test_blog_missing_source_url(self):
        errs = self.check(BLOG_FM.format(extra='site: "ex.com"'))
        self.assertTrue(any("source_url" in e for e in errs), errs)
        self.assertFalse(any("video_id" in e for e in errs), errs)

    def test_blog_combined_needs_inline_list(self):
        errs = self.check(BLOG_FM.format(extra='source_urls:\n  - "https://ex.com/a"\n  - "https://ex.com/b"'))
        self.assertTrue(any("source_urls" in e for e in errs), errs)
        self.assertEqual(self.check(BLOG_FM.format(extra='source_urls: ["https://ex.com/a", "https://ex.com/b"]')), [])

    def test_missing_explainer_link(self):
        text = BLOG_FM.format(extra='source_url: "https://ex.com/a"') + "\n[[Prompt_Caching__Lookup.html|Step through it]]\n"
        errs = self.check(text)
        self.assertTrue(any("Prompt_Caching__Lookup.html" in e for e in errs), errs)
        (self.dir / "Prompt_Caching__Lookup.html").write_text(EXPLAINER)
        self.assertEqual(self.check(text), [])

    def test_video_note_still_needs_video_keys(self):
        text = BLOG_FM.replace("source_type: blog\n{extra}\n", "")
        errs = self.check(text)
        self.assertTrue(any("video_id" in e for e in errs), errs)

    def run_cli(self, *args):
        return subprocess.run([sys.executable, str(SCRIPTS / "check_note.py"), *args], capture_output=True, text=True)

    def test_explainer_mode(self):
        page = self.dir / "Prompt_Caching__Lookup.html"
        page.write_text(EXPLAINER)
        self.assertEqual(self.run_cli(str(page), "--explainer").returncode, 0, self.run_cli(str(page), "--explainer").stdout)
        r = self.run_cli(str(page))
        self.assertEqual(r.returncode, 1)
        self.assertIn("card not found", r.stdout)


if __name__ == "__main__":
    unittest.main()
