import argparse
import contextlib
import io
import json
import os
import tempfile
import unittest
from pathlib import Path

import _util  # noqa: F401

import notes_paths as N
import ytn_config as C


class PrepareCollisionTests(unittest.TestCase):
    def test_video_note_does_not_overwrite_blog_note(self):
        with tempfile.TemporaryDirectory() as t:
            tmp = Path(t)
            os.environ.update(YT_NOTES_CONFIG=str(tmp / "c.json"), YT_NOTES_ENV="local", YT_NOTES_ROOT=str(tmp / "Notes"))
            cfg = C.load(N.SKILL_DIR)
            root = cfg["_root"]
            blog = root / "LLM" / "Prompt_Caching"
            blog.mkdir(parents=True)
            (blog / "Prompt_Caching.md").write_text('---\ntitle: "Prompt Caching"\nsource_type: blog\nsource_url: "https://a"\n---\n')
            src = root / "_sources" / "Vid_abc123XYZ00"
            src.mkdir(parents=True)
            (src / "meta.json").write_text(json.dumps({"video_id": "abc123XYZ00", "title": "Vid", "channel": "Chan X"}))
            args = argparse.Namespace(source=[str(src)], topic="LLM", title="Prompt Caching", format="markdown", new_location=False)
            with contextlib.redirect_stdout(io.StringIO()):
                out = N.cmd_prepare(cfg, args)
            self.assertTrue(out["note_file"].endswith("Prompt_Caching_(Chan_X)/Prompt_Caching_(Chan_X).md"), out["note_file"])
            self.assertEqual(out["renamed_for_collision"], "Prompt Caching")
            os.environ.pop("YT_NOTES_ROOT")


if __name__ == "__main__":
    unittest.main()
