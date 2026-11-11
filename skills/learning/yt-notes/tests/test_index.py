import tempfile
import unittest
from pathlib import Path

import _util  # noqa: F401

import notes_paths as N


def note(root, topic, title, fm):
    d = root / topic / title
    d.mkdir(parents=True)
    lines = ["---"] + [f"{k}: {v}" for k, v in fm.items()] + ["---", "", "# x"]
    (d / f"{title}.md").write_text("\n".join(lines))


class IndexTests(unittest.TestCase):
    def test_source_column(self):
        with tempfile.TemporaryDirectory() as t:
            root = Path(t)
            note(root, "LLM", "Prompt_Caching", {"title": '"Prompt Caching"', "site": '"outcomeschool.com"',
                                                 "source_type": "blog", "created": '"2026-11-11"'})
            note(root, "LLM", "Caching_Talk", {"title": '"Caching Talk"', "channel": '"Some Channel"', "created": '"2026-11-10"'})
            note(root, "LLM", "Caching_Roundup", {"title": '"Caching Roundup"', "source_type": "blog",
                                                  "source_urls": '["https://a", "https://b"]', "created": '"2026-11-09"'})
            N.rebuild_topic_index(root, "LLM")
            N.rebuild_root_index(root)
            idx = (root / "LLM" / "_index.md").read_text()
            self.assertIn("| Note | Summary | Source | Added | Status |", idx)
            self.assertIn("| outcomeschool.com |", idx)
            self.assertIn("| Some Channel |", idx)
            self.assertIn("| 2 posts |", idx)
            top = (root / "_index.md").read_text()
            self.assertIn("# Notes", top)
            self.assertIn('title: "Notes - index"', top)


if __name__ == "__main__":
    unittest.main()
