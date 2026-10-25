#!/usr/bin/env python3
"""Quality checks for a generated note (run before saving to Drive / reporting).

  check_note.py <Note_Title>.html --card <Note_Title>.md     # HTML format (default)
  check_note.py <Note_Title>.md                              # markdown format

HTML page:
  * no leftover template blocks (data-example, REPLACE, {{...}}, TODO)
  * no inline event handlers or javascript: URLs (Obsidian's HTML Viewer strips them)
  * every tab has a matching panel; every #link has a target; ids are unique
  * no external scripts/styles/fonts (warning: page wouldn't work offline)
  * at least one illustration
  * loads without JS errors, each tab opens its panel, readable without JS
    (needs Playwright; skipped with a warning if missing)
Markdown (card or note):
  * frontmatter with the required keys; card links to its HTML page
  * inline SVG is well-formed, has no blank lines (they break Obsidian's HTML block), no scripts
  * Mermaid only as a warning (notes use hand-drawn SVG)
Exit code 1 when a hard error is found; warnings don't fail.
"""

from __future__ import annotations

import argparse
import re
import sys
import xml.etree.ElementTree as ET
from html.parser import HTMLParser
from pathlib import Path

REQUIRED = ["title", "topic", "tags", "created", "summary"]
# A single-video note has video_id + video_url; a combined note has video_ids + video_urls.
SINGLE_KEYS, COMBINED_KEYS = ["video_id", "video_url"], ["video_ids", "video_urls"]


# ---------------------------------------------------------------- markdown
def frontmatter_keys(text):
    m = re.match(r"^---\n(.*?)\n---", text, re.S)
    if not m:
        return None, ""
    return set(re.findall(r"^([A-Za-z_][\w-]*):", m.group(1), re.M)), m.group(1)


def check_markdown(path: Path, errors, warnings, is_card=False, page: Path | None = None):
    text = path.read_text(encoding="utf-8")
    keys, fm = frontmatter_keys(text)
    if keys is None:
        errors.append(f"{path.name}: missing YAML frontmatter at the top")
    else:
        missing = [k for k in REQUIRED if k not in keys]
        if "video_ids" in keys:
            missing += [k for k in COMBINED_KEYS if k not in keys]
            ids = re.search(r"^video_ids:\s*\[(.*)\]\s*$", fm, re.M)
            if not ids:
                errors.append(f"{path.name}: video_ids must be an inline list, e.g. video_ids: [\"abc123XYZ00\", \"def456UVW11\"]")
        else:
            missing += [k for k in SINGLE_KEYS if k not in keys]
        if missing:
            errors.append(f"{path.name}: frontmatter missing keys: {', '.join(missing)}")
    body = re.sub(r"```.*?```", "", text, flags=re.S)
    if re.search(r"\{\{[^}]+\}\}|\bTODO\b|\bTBD\b", body):
        errors.append(f"{path.name}: leftover placeholder ({{{{...}}}}, TODO or TBD)")
    if "```mermaid" in text:
        warnings.append(f"{path.name}: contains Mermaid; notes use hand-drawn SVG unless the user asked for Mermaid")
    if is_card:
        if page is not None and f"[[{page.name}" not in text:
            errors.append(f"{path.name}: card doesn't link to its page ([[{page.name}|Open the full note]])")
        return
    svgs = list(re.finditer(r"<svg\b.*?</svg>", body, re.S | re.I))
    if not svgs:
        warnings.append(f"{path.name}: no inline SVG visuals; most notes need at least one picture")
    for i, m in enumerate(svgs, 1):
        block = m.group(0)
        line = text[: text.find(block)].count("\n") + 1
        if re.search(r"\n\s*\n", block):
            errors.append(f"{path.name}: SVG #{i} (line {line}) has a blank line inside; Obsidian will show it as raw text")
        if re.search(r"<script|<style|\son[a-z]+\s*=", block, re.I):
            errors.append(f"{path.name}: SVG #{i} (line {line}) has <script>, <style> or event handlers, which Obsidian strips")
        if re.search(r'\sclass="', block):
            warnings.append(f"{path.name}: SVG #{i} (line {line}) uses CSS classes; in markdown they have no styles, so use attributes")
        try:
            ET.fromstring(block.replace("&nbsp;", " "))
        except ET.ParseError as e:
            errors.append(f"{path.name}: SVG #{i} (line {line}) is not well-formed: {e}")


# ---------------------------------------------------------------- html
class Collector(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.ids, self.dupe_ids, self.hrefs, self.handlers, self.js_urls = set(), set(), [], [], []
        self.external, self.tabs, self.panels, self.examples = [], [], [], 0
        self.figures = self.svgs = 0
        self._in_script = False
        self.text = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or "") for k, v in attrs}
        cls = a.get("class", "").split()
        if "id" in a:
            (self.dupe_ids if a["id"] in self.ids else self.ids).add(a["id"])
        for k, v in a.items():
            if k.startswith("on"):
                self.handlers.append(f"<{tag} {k}=…>")
            if k in ("href", "src", "xlink:href") and v.strip().lower().startswith("javascript:"):
                self.js_urls.append(f"<{tag} {k}={v[:30]}>")
        if "data-example" in a:
            self.examples += 1
        if tag == "a" and a.get("href", "").startswith("#"):
            self.hrefs.append(a["href"])
            if "tab" in cls:
                self.tabs.append(a["href"][1:])
        if "panel" in cls and "id" in a:
            self.panels.append(a["id"])
        if tag == "script" and re.match(r"https?://", a.get("src", "")):
            self.external.append(a["src"])
        if tag == "link" and re.match(r"https?://", a.get("href", "")):
            self.external.append(a["href"])
        if tag == "img" and re.match(r"https?://", a.get("src", "")):
            self.external.append(a["src"])
        if tag == "figure" or "figure" in cls:
            self.figures += 1
        if tag == "svg":
            self.svgs += 1
        if tag == "script":
            self._in_script = True

    def handle_endtag(self, tag):
        if tag == "script":
            self._in_script = False

    def handle_data(self, data):
        if not self._in_script:
            self.text.append(data)


def check_html_static(path: Path, errors, warnings):
    html = path.read_text(encoding="utf-8")
    c = Collector()
    c.feed(re.sub(r"<!--.*?-->", "", html, flags=re.S))
    visible = " ".join(c.text)
    if c.examples:
        errors.append(f"{c.examples} template block(s) marked data-example are still in the page; replace or delete them")
    if re.search(r"\bREPLACE\b", visible):
        errors.append("template text marked REPLACE is still visible in the page")
    if re.search(r"\{\{[^}]+\}\}|\bTODO\b|\bTBD\b", visible):
        errors.append("leftover placeholder ({{...}}, TODO or TBD) in the page")
    if c.handlers:
        errors.append(f"inline event handlers {sorted(set(c.handlers))[:4]}: HTML Viewer strips them; use addEventListener")
    if c.js_urls:
        errors.append(f"javascript: URLs {c.js_urls[:3]}: HTML Viewer neutralises them")
    if c.dupe_ids:
        errors.append(f"duplicate ids (must be unique across the page, incl. SVG markers): {sorted(c.dupe_ids)[:6]}")
    if not c.tabs:
        errors.append("no tabs found (<a class=\"tab\" href=\"#id\">)")
    missing_panels = [t for t in c.tabs if t not in c.panels]
    if missing_panels:
        errors.append(f"tabs without a matching panel: {missing_panels}")
    extra_panels = [p for p in c.panels if p not in c.tabs]
    if extra_panels:
        errors.append(f"panels without a tab (unreachable when JS is on): {extra_panels}")
    broken = sorted({h for h in c.hrefs if h not in ("#",) and h[1:] not in c.ids})
    if broken:
        errors.append(f"in-page links with no target: {broken[:6]}")
    if c.external:
        warnings.append(f"loads from the internet ({c.external[:3]}); the page won't work offline")
    if c.svgs == 0 and c.figures == 0:
        warnings.append("no illustrations (SVG figures); most notes need at least one picture")
    return c


def check_html_runtime(path: Path, c: Collector, errors, warnings):
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        warnings.append("playwright not installed: page not test-loaded (tabs/JS unchecked at runtime)")
        return
    problems = []
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={"width": 1280, "height": 900})
        pg.on("pageerror", lambda e: problems.append(f"JS error: {e}"))
        pg.on("console", lambda m: problems.append(f"console.{m.type}: {m.text}") if m.type == "error" else None)
        pg.goto(path.resolve().as_uri())
        pg.wait_for_timeout(400)
        for tab in c.tabs:
            sel = f'.tab[href="#{tab}"]'
            if not pg.query_selector(sel):
                continue
            pg.click(sel)
            pg.wait_for_timeout(120)
            shown = pg.eval_on_selector_all(".panel", "els => els.filter(e => getComputedStyle(e).display !== 'none').map(e => e.id)")
            if shown != [tab]:
                problems.append(f"clicking tab #{tab} shows {shown}")
        for sel in [".stepper .controls button", ".compare .toggle button", ".expand", ".fab.home", ".fab.top"]:
            for el in pg.query_selector_all(sel)[:2]:
                try:
                    if el.is_visible():
                        el.click()
                        pg.wait_for_timeout(80)
                        pg.keyboard.press("Escape")
                except Exception as e:  # a click failing is worth reporting
                    problems.append(f"clicking {sel} failed: {e}")
        ctx = b.new_context(java_script_enabled=False)
        nojs = ctx.new_page()
        nojs.goto(path.resolve().as_uri())
        visible = nojs.eval_on_selector_all(".panel", "els => els.filter(e => getComputedStyle(e).display !== 'none').length")
        if visible != len(c.panels):
            problems.append(f"without JavaScript only {visible}/{len(c.panels)} panels are visible")
        b.close()
    errors.extend(problems)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("note", help="the .html page (HTML format) or the .md note (markdown format)")
    ap.add_argument("--card", help="the markdown card next to an HTML page")
    a = ap.parse_args()
    note = Path(a.note)
    errors, warnings = [], []
    if not note.exists():
        sys.exit(f"ERROR: {note} not found")
    if note.suffix.lower() in (".html", ".htm"):
        c = check_html_static(note, errors, warnings)
        check_html_runtime(note, c, errors, warnings)
        card = Path(a.card) if a.card else note.with_suffix(".md")
        if card.exists():
            check_markdown(card, errors, warnings, is_card=True, page=note)
        else:
            errors.append(f"markdown card not found: {card.name} (needed for Obsidian search and the index)")
        size = note.stat().st_size // 1024
        print(f"page: {note.name} | {size} KB | {len(c.tabs)} tabs | {c.figures} figure(s), {c.svgs} svg(s)")
        if size > 400:
            warnings.append(f"page is {size} KB; large pages are slow to upload from claude.ai")
    else:
        check_markdown(note, errors, warnings)
        text = note.read_text(encoding="utf-8")
        print(f"note: {note.name} | ~{len(text.split())} words | {len(re.findall(r'<svg', text))} inline SVG(s)")
    for w in warnings:
        print(f"WARN  {w}")
    for e in errors:
        print(f"ERROR {e}")
    print("RESULT: " + ("FAIL - fix the errors above" if errors else "OK"))
    sys.exit(1 if errors else 0)


if __name__ == "__main__":
    main()
