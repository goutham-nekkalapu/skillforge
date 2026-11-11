import unittest

from _util import FIXTURES

import article_extract as X

URL = "https://example.com/blog/prompt-caching?utm_source=x"


def load(name):
    raw = (FIXTURES / name).read_bytes()
    return X.extract(X.decode_html(raw, None), URL)


class ExtractTests(unittest.TestCase):
    def setUp(self):
        self._traf = X.trafilatura
        X.trafilatura = None  # always test the stdlib extractor

    def tearDown(self):
        X.trafilatura = self._traf

    def test_metadata_basic(self):
        a = load("basic_article.html")
        self.assertEqual(a["title"], "How Does Prompt Caching Work?")
        self.assertEqual(a["author"], "Jane Writer")
        self.assertEqual(a["published"], "2025-03-02")
        self.assertEqual(a["updated"], "2025-04-10")
        self.assertEqual(a["site"], "example.com")
        self.assertEqual(a["canonical_url"], "https://example.com/blog/prompt-caching")

    def test_markdown_structure(self):
        md = load("basic_article.html")["markdown"]
        self.assertIn("## Why caching matters", md)
        self.assertIn("### The prefix rule", md)
        self.assertIn("- Static content goes first", md)
        self.assertIn("```python\nresponse = client.messages.create(", md)
        self.assertRegex(md, r"\| Cache read \| 0\.1x \|")
        for noise in ("NAVIGATION MENU TEXT", "SIDEBAR RELATED POSTS", "FOOTER COPYRIGHT TEXT"):
            self.assertNotIn(noise, md)

    def test_title_heading_not_duplicated(self):
        md = load("basic_article.html")["markdown"]
        self.assertNotIn("# How Does Prompt Caching Work?", md)

    def test_faq_kept_in_source(self):
        self.assertIn("## FAQs", load("basic_article.html")["markdown"])

    def test_images_absolute(self):
        imgs = load("basic_article.html")["images"]
        self.assertEqual(imgs, [{"src": "https://example.com/blog/img/diagram.png", "alt": "Cache lookup diagram"}])

    def test_latin1(self):
        a = load("latin1.html")
        self.assertIn("café", a["markdown"])
        self.assertIn("crème brûlée", a["markdown"])

    def test_charset_from_header(self):
        raw = (FIXTURES / "latin1.html").read_bytes().replace(b'<meta charset="iso-8859-1">', b"")
        self.assertIn("café", X.decode_html(raw, "text/html; charset=ISO-8859-1"))

    def test_latin1_declared_cp1252_punctuation(self):
        raw = '<html><head><meta charset="iso-8859-1"></head><body><article><p>It\u2019s \u2014 fine</p></article></body></html>'.encode("cp1252")
        text = X.decode_html(raw, None)
        self.assertIn("It\u2019s \u2014 fine", text)

    def test_bom_stripped(self):
        self.assertFalse(X.decode_html("\ufeff<html></html>".encode("utf-8"), None).startswith("\ufeff"))

    def test_lazy_images(self):
        html = ('<html><body><article><p>x</p>'
                '<img src="data:image/gif;base64,R0l" data-src="/lazy.png" alt="lazy">'
                '<img srcset="/small.png 480w, /large.png 1024w" alt="set">'
                '</article></body></html>')
        srcs = [i["src"] for i in X.extract(html, "https://ex.com/post")["images"]]
        self.assertEqual(srcs, ["https://ex.com/lazy.png", "https://ex.com/small.png"])

    def test_word_counts(self):
        a = load("basic_article.html")
        self.assertGreaterEqual(a["word_count"], 300)
        self.assertGreaterEqual(a["page_word_count"], a["word_count"])

    def test_paywall(self):
        for name in ("paywall.html", "js_shell.html"):
            a = load(name)
            self.assertTrue(X.paywall_warnings(a["markdown"], a["word_count"], a["page_word_count"]), name)
        a = load("basic_article.html")
        self.assertEqual(X.paywall_warnings(a["markdown"], a["word_count"], a["page_word_count"]), [])

    def test_paywall_marker_message(self):
        w = X.paywall_warnings("x " * 500 + "Subscribe to continue reading", 501, 600)
        self.assertTrue(any("subscribe to continue" in s.lower() for s in w))


if __name__ == "__main__":
    unittest.main()
