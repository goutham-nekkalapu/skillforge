import contextlib
import io
import json
import tempfile
import unittest
from pathlib import Path

from _util import isolate_config

import fetch_article as F
import notes_paths as P

A = "https://outcomeschool.com/blog/how-does-prompt-caching-work"
B = "https://outcomeschool.com/blog/how-does-semantic-caching-work"
C3 = "https://example.com/caching-deep-dive"


class NotesPathsTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Notes"
        isolate_config(Path(self.tmp.name), self.root)

    def tearDown(self):
        self.tmp.cleanup()

    def pkg(self, url, title, words=2000, site="outcomeschool.com"):
        h = F.url_hash(url)
        d = self.root / "_sources" / f"{title.replace(' ', '_')}_{h}"
        d.mkdir(parents=True)
        (d / "meta.json").write_text(json.dumps({
            "title": title, "author": "Amit", "site": site, "url": url, "published": "2026-06-09",
            "word_count": words, "hash": h, "article_file": f"article_{h}.md"}))
        return str(d)

    def note(self, topic, title, fm):
        d = self.root / topic / title
        d.mkdir(parents=True)
        lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---", "", "# x"]
        (d / f"{title}.md").write_text("\n".join(lines))
        return d

    def prepare(self, *args):
        out = io.StringIO()
        with contextlib.redirect_stdout(out), contextlib.redirect_stderr(io.StringIO()):
            code = P.main(["prepare", *args])
        text = out.getvalue()
        return code, (json.loads(text) if code == 0 else text)

    def test_prepare_single(self):
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM Engineering", "--title", "Prompt Caching")
        self.assertEqual(code, 0)
        self.assertTrue(r["note_file"].endswith("LLM_Engineering/Prompt_Caching/Prompt_Caching.md"))
        self.assertIsNone(r["card_file"])
        self.assertEqual(r["format"], "markdown")
        self.assertEqual(r["mode"], "distilled")
        self.assertTrue(r["explainer_prefix"].endswith("Prompt_Caching/Prompt_Caching__"))
        p1 = r["posts"][0]
        self.assertEqual(p1["tag"], "P1")
        self.assertEqual(p1["source_wikilink"], f"[[article_{F.url_hash(A)}|Saved article]]")
        self.assertFalse(r["regenerating_existing_note"])

    def test_html_format_and_mode(self):
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM", "--title", "Prompt Caching",
                               "--format", "html", "--mode", "deep", "--critique")
        self.assertTrue(r["note_file"].endswith("Prompt_Caching.html"))
        self.assertTrue(r["card_file"].endswith("Prompt_Caching.md"))
        self.assertEqual((r["mode"], r["critique"]), ("deep", True))

    def test_regenerate_in_place(self):
        d = self.note("Other", "Old_Name", {"title": '"Old Name"', "source_type": "blog", "source_url": f'"{A}?utm_source=x"'})
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM", "--title", "Prompt Caching")
        self.assertEqual(Path(r["note_dir"]), d)
        self.assertTrue(r["regenerating_existing_note"])

    def test_collision_with_video_note(self):
        self.note("LLM_Engineering", "Prompt_Caching", {"title": '"Prompt Caching"', "video_id": '"abc123XYZ00"'})
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM Engineering", "--title", "Prompt Caching")
        self.assertTrue(r["note_file"].endswith(
            "Prompt_Caching_(outcomeschool.com)/Prompt_Caching_(outcomeschool.com).md"), r["note_file"])
        self.assertEqual(r["renamed_for_collision"], "Prompt Caching")
        self.assertEqual(r["title"], "Prompt Caching (outcomeschool.com)")

    def test_collision_twice(self):
        self.note("LLM", "Prompt_Caching", {"title": '"Prompt Caching"', "video_id": '"abc"'})
        self.note("LLM", "Prompt_Caching_(outcomeschool.com)", {"title": '"x"', "source_type": "blog", "source_url": '"https://other"'})
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM", "--title", "Prompt Caching")
        self.assertTrue(r["note_file"].endswith("Prompt_Caching_(outcomeschool.com)_2.md"), r["note_file"])

    def test_unsafe_title(self):
        code, r = self.prepare("--source", self.pkg(A, "x"), "--topic", "LLM", "--title", "Caching: Why? / How")
        folder = Path(r["note_dir"]).name
        for ch in ":?/":
            self.assertNotIn(ch, folder)

    def test_limits(self):
        srcs = []
        for i in range(6):
            srcs += ["--source", self.pkg(f"https://ex.com/p{i}", f"Post {i}", 100)]
        code, msg = self.prepare(*srcs, "--topic", "T", "--title", "Too Many")
        self.assertEqual(code, 1)
        self.assertIn("max_posts", msg)
        code, msg = self.prepare("--source", self.pkg("https://ex.com/big1", "Big 1", 25000),
                                 "--source", self.pkg("https://ex.com/big2", "Big 2", 20000), "--topic", "T", "--title", "Big")
        self.assertEqual(code, 1)
        self.assertIn("max_combined_words", msg)
        code, _ = self.prepare("--source", self.pkg("https://ex.com/huge", "Huge", 45000), "--topic", "T", "--title", "Huge")
        self.assertEqual(code, 0)

    def test_add_post(self):
        d = self.note("LLM", "Caching", {"title": '"Caching"', "source_type": "blog", "source_urls": f'["{A}", "{B}"]'})
        code, r = self.prepare("--source", self.pkg(A, "PC"), "--source", self.pkg(B, "SC"), "--source", self.pkg(C3, "Deep", site="example.com"),
                               "--topic", "LLM", "--title", "Caching")
        self.assertEqual(Path(r["note_dir"]), d)
        self.assertEqual([p["tag"] for p in r["posts"]], ["P1", "P2", "P3"])
        self.assertEqual(r["added_posts"], [C3])
        self.assertTrue(r["combined"])

    def test_index_lists_blog_notes(self):
        code, r = self.prepare("--source", self.pkg(A, "Prompt Caching"), "--topic", "LLM Engineering", "--title", "Prompt Caching")
        Path(r["note_file"]).write_text('---\ntitle: "Prompt Caching"\nsite: "outcomeschool.com"\nsource_type: blog\n'
                                        f'source_url: "{A}"\ncreated: "2026-11-11"\n---\n\n# Prompt Caching\n')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(P.main(["index", "--topic", "LLM Engineering"]), 0)
        idx = (self.root / "LLM_Engineering" / "_index.md").read_text()
        self.assertIn("| outcomeschool.com |", idx)

    def test_needs_yt_notes(self):
        saved = P.YT_NOTES_SCRIPT
        P.YT_NOTES_SCRIPT = Path(self.tmp.name) / "missing.py"
        P._YT = None
        try:
            out = io.StringIO()
            with contextlib.redirect_stdout(out):
                code = P.main(["index", "--all"])
            self.assertEqual(code, 1)
            self.assertIn("yt-notes", out.getvalue())
        finally:
            P.YT_NOTES_SCRIPT = saved
            P._YT = None


if __name__ == "__main__":
    unittest.main()
