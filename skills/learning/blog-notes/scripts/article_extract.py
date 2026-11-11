#!/usr/bin/env python3
"""Turn a blog post's HTML into clean markdown plus metadata (stdlib only).

  decode_html(raw_bytes, content_type) -> str
  extract(html, url) -> {title, author, site, published, updated, canonical_url,
                         markdown, images, word_count, page_word_count}
  paywall_warnings(markdown, word_count, page_word_count) -> [str]   # non-empty = truncated

If the optional `trafilatura` package is installed, its main-content extraction
is used for the markdown when it finds more text; metadata and the image list
always come from the built-in parser below.
"""

from __future__ import annotations

import json
import re
from html.parser import HTMLParser
from urllib.parse import urljoin, urlparse

try:  # optional, better extraction on messy pages
    import trafilatura  # type: ignore
except Exception:  # pragma: no cover - depends on the machine
    trafilatura = None

# ------------------------------------------------------------------ decoding
_META_CHARSET = re.compile(rb"""<meta[^>]+charset\s*=\s*["']?\s*([A-Za-z0-9_\-:.]+)""", re.I)


def decode_html(raw: bytes, content_type: str | None) -> str:
    """Bytes to text: charset from the HTTP header, then <meta>, then UTF-8, then cp1252."""
    candidates = []
    if content_type:
        m = re.search(r"charset\s*=\s*[\"']?([A-Za-z0-9_\-:.]+)", content_type, re.I)
        if m:
            candidates.append(m.group(1))
    m = _META_CHARSET.search(raw[:8192])
    if m:
        candidates.append(m.group(1).decode("ascii", "ignore"))
    candidates.append("utf-8")
    for enc in candidates:
        try:
            return raw.decode(enc)
        except (LookupError, UnicodeDecodeError):
            continue
    return raw.decode("cp1252", errors="replace")


# ------------------------------------------------------------------ tiny DOM
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
AUTO_CLOSE = {"p": {"p"}, "li": {"li"}, "tr": {"tr"}, "td": {"td", "th"}, "th": {"td", "th"},
              "dt": {"dt", "dd"}, "dd": {"dt", "dd"}, "option": {"option"}}
SKIP = {"nav", "header", "footer", "aside", "script", "style", "noscript", "form", "svg", "button",
        "iframe", "template", "select", "input", "textarea", "canvas", "dialog"}


class Node:
    __slots__ = ("tag", "attrs", "children", "parent")

    def __init__(self, tag: str, attrs: dict, parent: "Node | None"):
        self.tag, self.attrs, self.children, self.parent = tag, attrs, [], parent

    def iter(self):
        yield self
        for c in self.children:
            if isinstance(c, Node):
                yield from c.iter()

    def find(self, tag: str) -> "Node | None":
        return next((n for n in self.iter() if n.tag == tag), None)

    def text(self, skip: set = frozenset()) -> str:
        out = []
        for c in self.children:
            if isinstance(c, str):
                out.append(c)
            elif c.tag not in skip:
                out.append(c.text(skip))
        return "".join(out)

    def classes(self) -> str:
        return self.attrs.get("class") or ""


class _Builder(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.cur = self.root

    def handle_starttag(self, tag, attrs):
        closes = AUTO_CLOSE.get(tag)
        if closes:  # <p> inside an open <p>, <li> after <li>, ...
            n = self.cur
            while n is not self.root and n.tag not in ("ul", "ol", "table", "div", "article", "section", "body"):
                if n.tag in closes:
                    self.cur = n.parent
                    break
                n = n.parent
        node = Node(tag, {k: (v or "") for k, v in attrs}, self.cur)
        self.cur.children.append(node)
        if tag not in VOID:
            self.cur = node

    def handle_startendtag(self, tag, attrs):
        self.cur.children.append(Node(tag, {k: (v or "") for k, v in attrs}, self.cur))

    def handle_endtag(self, tag):
        n = self.cur
        while n is not self.root and n.tag != tag:
            n = n.parent
        if n is not self.root:
            self.cur = n.parent

    def handle_data(self, data):
        self.cur.children.append(data)


def parse(html: str) -> Node:
    b = _Builder()
    b.feed(html)
    b.close()
    return b.root


# ------------------------------------------------------------------ metadata
def _date(v) -> str | None:
    m = re.match(r"\s*(\d{4}-\d{2}-\d{2})", str(v or ""))
    return m.group(1) if m else None


def _name(v) -> str | None:
    if isinstance(v, list):
        names = [_name(x) for x in v]
        names = [n for n in names if n]
        return ", ".join(names) or None
    if isinstance(v, dict):
        return _name(v.get("name"))
    return str(v).strip() or None if v else None


def _jsonld_article(root: Node) -> dict:
    types = {"article", "blogposting", "newsarticle", "techarticle", "scholarlyarticle", "report", "webpage"}
    best = {}
    for n in root.iter():
        if n.tag != "script" or "ld+json" not in n.attrs.get("type", ""):
            continue
        try:
            data = json.loads(n.text())
        except ValueError:
            continue
        stack = data if isinstance(data, list) else [data]
        while stack:
            d = stack.pop(0)
            if not isinstance(d, dict):
                continue
            stack.extend(d.get("@graph") or [])
            t = d.get("@type")
            t = " ".join(t) if isinstance(t, list) else str(t or "")
            if any(x in t.lower().split() for x in types):
                if "webpage" not in t.lower() or not best:
                    best = d
    return best


def _metas(root: Node) -> dict:
    out = {}
    for n in root.iter():
        if n.tag == "meta":
            key = (n.attrs.get("property") or n.attrs.get("name") or "").lower()
            if key and n.attrs.get("content") and key not in out:
                out[key] = n.attrs["content"].strip()
    return out


def _clean_title(t: str, site: str | None) -> str:
    t = re.sub(r"\s+", " ", t or "").strip()
    parts = re.split(r"\s+[|–—]\s+|\s+-\s+", t)
    if len(parts) > 1 and len(parts[0]) >= 12:
        return parts[0].strip()
    return t


# ------------------------------------------------------------------ main content
def _p_text_len(n: Node) -> int:
    return sum(len(c.text().strip()) for c in n.children if isinstance(c, Node) and c.tag == "p")


def _pick_root(root: Node) -> Node:
    for tag in ("article", "main"):
        found = [n for n in root.iter() if n.tag == tag]
        if found:
            return max(found, key=lambda n: len(n.text(SKIP)))
    cands = [n for n in root.iter() if n.tag in ("div", "section", "td")]
    best = max(cands, key=_p_text_len, default=None)
    if best is not None and _p_text_len(best) > 200:
        return best
    return root.find("body") or root


def _ws(s: str) -> str:
    return re.sub(r"\s+", " ", s)


class _Md:
    BLOCK = {"p", "div", "section", "article", "main", "h1", "h2", "h3", "h4", "h5", "h6", "ul", "ol", "pre",
             "blockquote", "table", "figure", "figcaption", "hr", "dl", "details", "summary", "body", "center"}

    def __init__(self, base_url: str, title: str | None):
        self.base = base_url
        self.title = (title or "").strip().lower()
        self.images: list[dict] = []

    # inline ------------------------------------------------------------
    def inline(self, n) -> str:
        if isinstance(n, str):
            return _ws(n)
        t = n.tag
        if t in SKIP:
            return ""
        if t == "br":
            return "  \n"
        if t == "img":
            return self.img(n)
        inner = "".join(self.inline(c) for c in n.children)
        if t in ("strong", "b") and inner.strip():
            return f"**{inner.strip()}** "
        if t in ("em", "i") and inner.strip():
            return f"*{inner.strip()}* "
        if t == "code":
            return f"`{n.text().strip()}`"
        if t == "a":
            href = n.attrs.get("href", "")
            if inner.strip() and href and not href.startswith(("#", "javascript:", "mailto:")):
                return f"[{inner.strip()}]({urljoin(self.base, href)})"
        return inner

    def img(self, n: Node) -> str:
        src = n.attrs.get("src") or n.attrs.get("data-src") or ""
        if not src or src.startswith("data:"):
            return ""
        src = urljoin(self.base, src)
        alt = _ws(n.attrs.get("alt", "")).strip()
        if not any(i["src"] == src for i in self.images):
            self.images.append({"src": src, "alt": alt})
        return f"![{alt}]({src})"

    # blocks ------------------------------------------------------------
    def blocks(self, n: Node) -> list[str]:
        out, buf = [], []

        def flush():
            text = re.sub(r"[ \t]+", " ", "".join(buf)).strip()
            if text:
                out.append(text)
            buf.clear()

        for c in n.children:
            if isinstance(c, str) or (c.tag not in self.BLOCK and c.tag not in ("li", "tr", "dt", "dd")):
                if isinstance(c, Node) and c.tag in SKIP:
                    continue
                if isinstance(c, Node) and any(isinstance(d, Node) and d.tag in self.BLOCK for d in c.iter() if d is not c):
                    flush()
                    out.extend(self.blocks(c))  # e.g. <span> wrapping blocks
                else:
                    buf.append(self.inline(c))
                continue
            flush()
            out.extend(self.block(c))
        flush()
        return out

    def block(self, n: Node) -> list[str]:
        t = n.tag
        if t in SKIP:
            return []
        if t in ("h1", "h2", "h3", "h4", "h5", "h6"):
            text = _ws("".join(self.inline(c) for c in n.children)).strip()
            if not text or (t == "h1" and text.lower() == self.title):
                return []
            return ["#" * int(t[1]) + " " + text]
        if t == "pre":
            code = n.text()
            lang = ""
            for x in [n] + [c for c in n.children if isinstance(c, Node) and c.tag == "code"]:
                m = re.search(r"(?:language|lang)-([\w+#-]+)", x.classes())
                if m:
                    lang = m.group(1)
            return [f"```{lang}\n{code.strip(chr(10))}\n```"]
        if t in ("ul", "ol"):
            return [self.list_md(n)]
        if t == "blockquote":
            inner = "\n\n".join(self.blocks(n))
            return ["\n".join("> " + line if line else ">" for line in inner.splitlines())] if inner else []
        if t == "table":
            return [self.table(n)]
        if t == "hr":
            return ["---"]
        return self.blocks(n)

    def list_md(self, n: Node, depth: int = 0) -> str:
        lines, i = [], 0
        for li in n.children:
            if not isinstance(li, Node) or li.tag != "li":
                continue
            i += 1
            marker = f"{i}." if n.tag == "ol" else "-"
            text_parts, nested = [], []
            for c in li.children:
                if isinstance(c, Node) and c.tag in ("ul", "ol"):
                    nested.append(self.list_md(c, depth + 1))
                elif isinstance(c, Node) and c.tag == "pre":
                    nested.append("\n".join("  " * (depth + 1) + x for x in self.block(c)[0].splitlines()))
                else:
                    text_parts.append(self.inline(c) if not (isinstance(c, Node) and c.tag in self.BLOCK)
                                      else " ".join(self.blocks(c)))
            text = re.sub(r"\s+", " ", "".join(text_parts)).strip()
            lines.append("  " * depth + f"{marker} {text}")
            lines.extend(nested)
        return "\n".join(lines)

    def table(self, n: Node) -> str:
        rows = []
        for tr in n.iter():
            if tr.tag != "tr":
                continue
            cells = [_ws("".join(self.inline(c) for c in td.children)).strip().replace("|", "\\|")
                     for td in tr.children if isinstance(td, Node) and td.tag in ("td", "th")]
            if cells:
                rows.append(cells)
        if not rows:
            return ""
        width = max(len(r) for r in rows)
        rows = [r + [""] * (width - len(r)) for r in rows]
        lines = ["| " + " | ".join(rows[0]) + " |", "|" + "---|" * width]
        lines += ["| " + " | ".join(r) + " |" for r in rows[1:]]
        return "\n".join(lines)


def _strip_code(md: str) -> str:
    return re.sub(r"```.*?```", " ", md, flags=re.S)


def _words(text: str) -> int:
    return len(re.findall(r"\w+", text))


def extract(html: str, url: str) -> dict:
    root = parse(html)
    meta = _metas(root)
    ld = _jsonld_article(root)

    canonical = url
    for n in root.iter():
        if n.tag == "link" and "canonical" in n.attrs.get("rel", "").lower().split() and n.attrs.get("href"):
            canonical = urljoin(url, n.attrs["href"])
            break
    host = urlparse(canonical).netloc.lower()
    site = host[4:] if host.startswith("www.") else host

    title_tag = root.find("title")
    title = (_ws(str(ld.get("headline") or "")).strip()
             or meta.get("og:title")
             or _clean_title(title_tag.text() if title_tag else "", site)
             or url)
    og_author = meta.get("article:author", "")
    author = (_name(ld.get("author"))
              or (og_author if og_author and not og_author.startswith("http") else None)
              or meta.get("author"))
    published = _date(ld.get("datePublished")) or _date(meta.get("article:published_time")) or _date(meta.get("date"))
    updated = _date(ld.get("dateModified")) or _date(meta.get("article:modified_time"))

    main = _pick_root(root)
    md_builder = _Md(url, title)
    markdown = "\n\n".join(b for b in md_builder.blocks(main) if b.strip())
    markdown = re.sub(r"\n{3,}", "\n\n", markdown).strip()

    if trafilatura is not None:
        try:
            alt = trafilatura.extract(html, url=url, output_format="markdown", include_tables=True,
                                      include_images=True, include_formatting=True, include_links=True)
        except Exception:
            alt = None
        if alt and _words(_strip_code(alt)) > _words(_strip_code(markdown)) * 1.1:
            markdown = alt.strip()

    body = root.find("body") or root
    page_words = _words(body.text(SKIP))
    return {
        "title": title,
        "author": author,
        "site": site,
        "published": published,
        "updated": updated,
        "canonical_url": canonical,
        "markdown": markdown,
        "images": md_builder.images,
        "word_count": _words(_strip_code(markdown)),
        "page_word_count": page_words,
    }


# ------------------------------------------------------------------ paywall
PAYWALL_MARKERS = [
    "subscribe to continue", "subscribe to read", "members only", "member-only story", "sign in to read",
    "log in to continue", "login to continue", "for paid subscribers", "this post is for subscribers",
    "become a member to read", "continue reading with a subscription", "to keep reading", "create a free account to continue",
]
MIN_WORDS = 300


def paywall_warnings(markdown: str, word_count: int, page_word_count: int) -> list[str]:
    """Reasons to think the text is not the whole article. Empty list = looks complete."""
    w = []
    low = (markdown or "").lower()
    for m in PAYWALL_MARKERS:
        if m in low:
            w.append(f'paywall text found: "{m}"; the article is probably cut off')
            break
    if word_count < MIN_WORDS:
        w.append(f"only {word_count} words extracted; the page may be paywalled, truncated or rendered by JavaScript")
    elif page_word_count > 0 and word_count < 0.25 * page_word_count:
        w.append(f"extracted {word_count} of ~{page_word_count} words on the page; the article may be cut off")
    return w
