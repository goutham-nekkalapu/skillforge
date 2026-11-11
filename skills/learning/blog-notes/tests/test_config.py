import json
import tempfile
import unittest
from pathlib import Path

from _util import LEARNING, SKILL, isolate_config

import ytn_config as C


class ConfigTests(unittest.TestCase):
    def test_defaults(self):
        d = C.DEFAULTS
        self.assertEqual(d["notes_root"], "~/Notes")
        self.assertEqual(d["drive_root"], "Notes")
        self.assertEqual(d["blog_note_format"], "markdown")
        self.assertEqual(d["blog_mode"], "distilled")
        self.assertEqual(d["max_posts"], 5)
        self.assertEqual(d["max_combined_words"], 40000)
        self.assertEqual(d["article_tiers"], ["local", "supadata"])
        self.assertEqual(d["max_explainers"], 2)

    def test_copies_identical(self):
        copies = [LEARNING / s / "scripts" / "ytn_config.py" for s in ("yt-transcript", "yt-notes", "blog-notes")]
        texts = {p.read_bytes() for p in copies}
        self.assertEqual(len(texts), 1, "the three ytn_config.py copies differ")

    def test_old_user_config_wins(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            isolate_config(tmp)
            (tmp / "config.json").write_text(json.dumps({"notes_root": "~/YouTubeNotes"}))
            cfg = C.load(SKILL)
            self.assertEqual(cfg["_root"].name, "YouTubeNotes")


if __name__ == "__main__":
    unittest.main()
