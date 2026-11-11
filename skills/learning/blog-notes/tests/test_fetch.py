import contextlib
import io
import json
import os
import re
import tempfile
import unittest
from pathlib import Path

from _util import FIXTURES, isolate_config

import article_extract
import fetch_article as F

URL = "https://example.com/blog/prompt-caching"
IMG = "https://example.com/blog/img/diagram.png"
PNG = b"\x89PNG\r\n\x1a\n" + b"0" * 100


class FakeWeb:
    """Stands in for fetch_article.http_get: url -> (status, content_type, bytes) or an exception."""

    def __init__(self, pages):
        self.pages = pages
        self.calls = []

    def __call__(self, url, headers=None, timeout=20):
        self.calls.append(url)
        for key, val in self.pages.items():
            if url.startswith(key):
                if isinstance(val, Exception):
                    raise val
                return val
        return 404, "text/html", b"not found"


def run(argv):
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = F.main(argv)
    text = out.getvalue()
    m = re.search(r"=== RESULT JSON ===\n(.*)\n=== END RESULT ===", text, re.S)
    return code, (json.loads(m.group(1)) if m else None), text


class FetchTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "Notes"
        isolate_config(Path(self.tmp.name), self.root)
        self._http = F.http_get
        self._traf = article_extract.trafilatura
        article_extract.trafilatura = None

    def tearDown(self):
        F.http_get = self._http
        article_extract.trafilatura = self._traf
        os.environ.pop("SUPADATA_API_KEY", None)
        self.tmp.cleanup()

    def web(self, pages):
        F.http_get = FakeWeb(pages)
        return F.http_get

    def page(self, name="basic_article.html"):
        return 200, "text/html; charset=utf-8", (FIXTURES / name).read_bytes()

    # ---------------------------------------------------------------- urls
    def test_normalize_same_hash(self):
        self.assertEqual(F.url_hash("https://Example.com/post/?utm_source=x&ref=hn#faq"),
                         F.url_hash("https://example.com/post"))
        self.assertNotEqual(F.url_hash("https://example.com/post?id=1"), F.url_hash("https://example.com/post?id=2"))

    def test_youtube_rejected(self):
        web = self.web({})
        code, _, text = run(["https://youtu.be/abc123XYZ00", URL])
        self.assertEqual(code, 5)
        self.assertIn("yt-notes", text)
        self.assertEqual(web.calls, [])

    # ---------------------------------------------------------------- package
    def test_package_layout(self):
        self.web({URL: self.page(), IMG: (200, "image/png", PNG)})
        code, res, _ = run([URL, "--tiers", "local"])
        self.assertEqual(code, 0)
        post = res["posts"][0]
        self.assertEqual(post["status"], "ok")
        d = Path(post["source_dir"])
        h = F.url_hash(URL)
        self.assertEqual(d.parent, self.root / "_sources")
        self.assertEqual(d.name, f"How_Does_Prompt_Caching_Work_{h}")
        meta = json.loads((d / "meta.json").read_text())
        self.assertEqual(meta["author"], "Jane Writer")
        self.assertEqual(meta["fetch_method"], "local")
        self.assertTrue((d / meta["images"][0]["file"]).exists())
        art = (d / f"article_{h}.md").read_text()
        self.assertIn(f'source_url: "{URL}"', art)
        self.assertIn("# How Does Prompt Caching Work?", art)
        self.assertIn("](images/", art)

    def test_cached(self):
        self.web({URL: self.page(), IMG: (200, "image/png", PNG)})
        run([URL, "--tiers", "local"])
        web = self.web({})
        code, res, _ = run([URL + "?utm_source=newsletter", "--tiers", "local"])
        self.assertEqual(code, 0)
        self.assertEqual(res["posts"][0]["status"], "cached")
        self.assertEqual(web.calls, [])

    def test_duplicate_urls_fetched_once(self):
        web = self.web({URL: self.page(), IMG: (200, "image/png", PNG)})
        code, res, _ = run([URL, URL + "/", "--tiers", "local"])
        self.assertEqual(len(res["posts"]), 1)
        self.assertEqual(web.calls.count(URL), 1)

    def test_image_failures_and_caps(self):
        html = (FIXTURES / "basic_article.html").read_text()
        extra = "".join(f'<img src="img/s{i}.png" alt="s{i}">' for i in range(25))
        html = html.replace("<h2>FAQs</h2>", f'<p><img src="img/big.png" alt="big"><img src="img/gone.png" alt="gone">{extra}</p><h2>FAQs</h2>')
        self.web({URL: (200, "text/html", html.encode()),
                  "https://example.com/blog/img/big.png": (200, "image/png", b"0" * (6 * 1024 * 1024)),
                  "https://example.com/blog/img/gone.png": (404, "text/html", b""),
                  "https://example.com/blog/img/": (200, "image/png", PNG)})
        code, res, _ = run([URL, "--tiers", "local"])
        self.assertEqual(code, 0)
        post = res["posts"][0]
        warn = " ".join(post["warnings"])
        self.assertIn("big.png", warn)
        self.assertIn("gone.png", warn)
        files = list((Path(post["source_dir"]) / "images").iterdir())
        self.assertLessEqual(len(files), 20)
        self.assertLessEqual(sum(f.stat().st_size for f in files), 5 * 1024 * 1024)

    def test_no_images_flag(self):
        web = self.web({URL: self.page(), IMG: (200, "image/png", PNG)})
        run([URL, "--tiers", "local", "--no-images"])
        self.assertNotIn(IMG, web.calls)

    # ---------------------------------------------------------------- statuses
    def test_truncated_status(self):
        self.web({URL: self.page("paywall.html")})
        code, res, _ = run([URL, "--tiers", "local"])
        self.assertEqual(code, 0)
        post = res["posts"][0]
        self.assertEqual(post["status"], "truncated")
        self.assertTrue(post["warnings"])
        self.assertTrue(Path(post["source_dir"], "meta.json").exists())

    def test_js_shell_truncated(self):
        self.web({URL: self.page("js_shell.html")})
        _, res, _ = run([URL, "--tiers", "local"])
        self.assertEqual(res["posts"][0]["status"], "truncated")

    def test_truncated_cached_stays_truncated(self):
        self.web({URL: self.page("paywall.html")})
        run([URL, "--tiers", "local"])
        self.web({})
        _, res, _ = run([URL, "--tiers", "local"])
        self.assertEqual(res["posts"][0]["status"], "truncated")

    def test_from_file_short_is_truncated(self):
        f = Path(self.tmp.name) / "scraped.md"
        f.write_text("# Teaser\n\nSemantic caching matches by meaning. Subscribe to continue reading.")
        _, res, _ = run(["--from-file", str(f), "--url", URL])
        self.assertEqual(res["posts"][0]["status"], "truncated")
        _, res, _ = run(["--from-file", str(f), "--url", URL, "--trust"])
        self.assertEqual(res["posts"][0]["status"], "ok")

    def test_from_file_html_latin1(self):
        f = Path(self.tmp.name) / "saved.html"
        f.write_bytes((FIXTURES / "latin1.html").read_bytes())
        _, res, _ = run(["--from-file", str(f), "--url", URL, "--trust"])
        art = next(Path(res["posts"][0]["source_dir"]).glob("article_*.md")).read_text(encoding="utf-8")
        self.assertIn("café", art)

    def test_from_file(self):
        f = Path(self.tmp.name) / "pasted.md"
        f.write_text("# My Pasted Post\n\n" + "word " * 400)
        code, res, _ = run(["--from-file", str(f), "--url", URL, "--trust"])
        self.assertEqual(code, 0)
        meta = json.loads(Path(res["posts"][0]["source_dir"], "meta.json").read_text())
        self.assertEqual(meta["fetch_method"], "user-provided")
        self.assertEqual(meta["title"], "My Pasted Post")

    def test_missing_key_exit3(self):
        self.web({URL: (403, "text/html", b"blocked")})
        code, res, text = run([URL])
        self.assertEqual(code, 3)
        self.assertIn("=== CREDENTIALS NEEDED ===", text)
        self.assertIn("SUPADATA_API_KEY", text)
        self.assertEqual(res["posts"][0]["status"], "failed")

    def test_network_blocked_exit4(self):
        self.web({URL: F.NetworkError("no route"), "https://api.supadata.ai": F.NetworkError("no route")})
        os.environ["SUPADATA_API_KEY"] = "k"
        code, _, _ = run([URL])
        self.assertEqual(code, 4)

    def test_supadata_tier(self):
        os.environ["SUPADATA_API_KEY"] = "k"
        body = json.dumps({"url": URL, "name": "Supa Title", "content": "## Intro\n\n" + "text " * 400}).encode()
        self.web({URL: (403, "text/html", b"blocked"), "https://api.supadata.ai/v1/web/scrape": (200, "application/json", body)})
        code, res, _ = run([URL])
        self.assertEqual(code, 0)
        self.assertEqual(res["posts"][0]["fetch_method"], "supadata")
        self.assertEqual(res["credits_used"], 1)

    def test_partial_failure_still_exit0(self):
        other = "https://example.com/blog/gone"
        self.web({URL: self.page(), IMG: (200, "image/png", PNG)})
        code, res, _ = run([URL, other, "--tiers", "local"])
        self.assertEqual(code, 0)
        self.assertEqual([p["status"] for p in res["posts"]], ["ok", "failed"])


if __name__ == "__main__":
    unittest.main()
