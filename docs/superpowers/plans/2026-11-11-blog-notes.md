# blog-notes Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** A `blog-notes` skill that turns 1..N blog post URLs into distilled markdown notes (HTML explainers only where a concept moves), saved by topic next to yt-notes' notes, plus the shared rename of the notes root to `Notes`.

**Architecture:** Two stdlib-only scripts in the new skill: `article_extract.py` (pure HTML → markdown + metadata + paywall heuristics) and `fetch_article.py` (CLI: tiers, source package, cache), plus `notes_paths.py` (where / prepare / index, index delegated to yt-notes). The note-writing behaviour lives in `SKILL.md` and three references. yt-notes gets small changes: blog-aware checker, explainer check mode, "Source" index column, `Notes` naming.

**Tech Stack:** Python 3.10+ stdlib (urllib, html.parser, json, hashlib, unittest); optional `trafilatura`; Supadata web scrape API; existing yt-notes template and checker.

**Spec:** `docs/superpowers/specs/2026-11-11-blog-notes-design.md`

## Global Constraints

- Branch `feature/blog-notes`; PR to `develop`. Commit messages end with `Co-Authored-By: Claude Opus 5.5 <noreply@anthropic.com>`.
- Scripts are stdlib-only; `trafilatura` is used only if importable. No new required dependencies.
- File/folder names use underscores (`ytn_config.safe_name`); titles inside notes keep spaces.
- All three copies of `ytn_config.py` (yt-transcript, yt-notes, blog-notes) stay byte-identical.
- New config defaults: `notes_root: "~/Notes"`, `drive_root: "Notes"`, `blog_note_format: "markdown"`, `blog_mode: "distilled"`, `max_posts: 5`, `max_combined_words: 40000`, `article_tiers: ["local", "supadata"]`, `max_explainers: 2`.
- Source package: `<notes_root>/_sources/<Post_Title>_<urlhash>/` with `meta.json`, `article_<urlhash>.md`, `images/` (≤ 20 images, ≤ 5 MB total). `urlhash` = first 10 hex of SHA-1 of the normalised canonical URL.
- fetch exit codes: 0 ok, 2 failed, 3 credentials needed, 4 network blocked, 5 bad input (incl. YouTube URLs).
- Combined-note tags `P1…P5`; explainer files `<Note_Title>__<Concept>.html`; collision title `<Title> (<site>)`.
- Root `_index.md` title "Notes", `type: yt-notes-index` unchanged.
- Tests: `python3 -m unittest discover -s skills/learning/<skill>/tests -v`; fixtures are saved HTML files, no network in tests.

## Review Focus

1. **Odd encodings** (page declares `charset=iso-8859-1` or has no charset, bytes not UTF-8) → text decodes correctly, no mojibake. Test in Task 2.
2. **JS-rendered / near-empty pages** (app shell with `<div id="root"></div>`) → status `truncated` with a warning, never a silently thin note. Test in Task 2/3.
3. **Same post given twice or with tracking params / trailing slash / `#fragment`** (`?utm_source=x`, `/post/`, `/post#faq`) → one package, one hash. Test in Task 3.
4. **Titles with `: ? / |` and title collisions with an existing video note** → safe folder name; `<Title> (<site>)` folder, never an overwrite. Test in Task 4.
5. **Images that are relative, `data:` URIs, too big, or 404** → relative resolved against the page URL, `data:` skipped, caps respected, download failure is a warning not a failure. Test in Task 3.

---

### Task 1: Shared config — `Notes` rename and blog defaults

**Files:**
- Modify: `skills/learning/yt-transcript/scripts/ytn_config.py` (DEFAULTS, `location_banner` heading "📁 NOTES LOCATION", docstring "~/Notes")
- Create: `skills/learning/yt-notes/scripts/ytn_config.py`, `skills/learning/blog-notes/scripts/ytn_config.py` (copies of the above)
- Modify: `skills/learning/yt-transcript/config.json` (`drive_root` → `"Notes"`; edit that one value only, don't print the file)
- Modify: `skills/learning/yt-notes/scripts/notes_paths.py` (root index title "Notes", docstrings)
- Modify: mentions of `YouTubeNotes` / "YouTube Notes" in `yt-notes/SKILL.md`, `yt-notes/README.md`, `yt-transcript/SKILL.md`, `yt-notes/examples/sample-output/_index.md`
- Test: `skills/learning/blog-notes/tests/test_config.py`

**Interfaces:**
- Produces: `ytn_config.DEFAULTS` with the Global Constraints keys; everything else in the module unchanged.

- [ ] **Step 1: Write the failing test** `test_config.py`:
  - `test_defaults`: `DEFAULTS["notes_root"] == "~/Notes"`, `DEFAULTS["drive_root"] == "Notes"`, and each blog key equals its Global Constraints value.
  - `test_copies_identical`: the three `ytn_config.py` files have identical bytes.
  - `test_old_user_config_wins`: with `YT_NOTES_CONFIG` pointing at a temp file containing `{"notes_root": "~/YouTubeNotes"}` and `YT_NOTES_ENV=local`, `load(skill_dir)["_root"]` ends with `YouTubeNotes` (existing users aren't moved).
- [ ] **Step 2: Run** `python3 -m unittest discover -s skills/learning/blog-notes/tests -v` → FAIL.
- [ ] **Step 3: Implement** the defaults, banner text, copies, config.json value, index title, and doc mentions; add to yt-notes and yt-transcript READMEs a short "Moving from YouTubeNotes" note (rename the folder, then update `notes_root`/`drive_root`).
- [ ] **Step 4: Run** the tests → PASS; `grep -rn "YouTubeNotes\|YouTube Notes" skills` shows only the README migration notes.
- [ ] **Step 5: Commit** `notes: rename default notes root to Notes; add blog-notes config defaults`.

### Task 2: `article_extract.py` — HTML to article markdown

**Files:**
- Create: `skills/learning/blog-notes/scripts/article_extract.py`
- Create: `skills/learning/blog-notes/tests/fixtures/` — `basic_article.html` (JSON-LD author/date, `<article>` with h2/h3, p, ul, `<pre><code class="language-python">`, table, img relative src, nav/footer/aside noise, FAQ section), `latin1.html` (bytes in ISO-8859-1 with `<meta charset="iso-8859-1">` and "café"), `paywall.html` (short teaser + "Subscribe to continue reading"), `js_shell.html` (`<div id="root"></div>` + scripts)
- Test: `skills/learning/blog-notes/tests/test_extract.py`

**Interfaces:**
- Produces:
  - `decode_html(raw: bytes, content_type: str | None) -> str` — charset from header, then `<meta charset>`, then UTF-8, falling back to cp1252.
  - `extract(html: str, url: str) -> dict` with keys `title, author, site, published, updated, canonical_url, markdown, images (list of {"src": absolute url, "alt": str}), word_count, page_word_count`. Uses trafilatura for `markdown` when importable, else the stdlib extractor; metadata always from JSON-LD → OpenGraph/`article:*` meta → `<title>`/`<meta name=author>`.
  - `paywall_warnings(markdown: str, word_count: int, page_word_count: int) -> list[str]` — non-empty means truncated. Triggers: `word_count < 300`; any paywall marker (case-insensitive: "subscribe to continue", "subscribe to read", "members only", "member-only story", "sign in to read", "log in to continue", "for paid subscribers", "this post is for subscribers", "become a member to read"); `page_word_count > 0 and word_count < 0.25 * page_word_count`.

- [ ] **Step 1: Write failing tests** (force the stdlib path by patching `article_extract.trafilatura = None`):
  - `test_metadata_basic`: title, author, `published == "2025-03-02"` (date part of the JSON-LD value), `site == "example.com"`, canonical from `<link rel=canonical>`.
  - `test_markdown_structure`: contains `## `, `### `, `- ` list items, a fenced block starting ```` ```python ````, a markdown table row `| ... |`; does not contain nav/footer text.
  - `test_faq_kept_in_source`: the FAQ heading is present (skipping happens at note-writing time).
  - `test_images_absolute`: relative `img/diagram.png` → `https://example.com/blog/img/diagram.png`; `data:` src excluded.
  - `test_latin1`: `extract(decode_html(raw, None), url)["markdown"]` contains "café".
  - `test_paywall`: `paywall_warnings(...)` non-empty for `paywall.html` and `js_shell.html`, empty for `basic_article.html` (fixture body ≥ 300 words).
- [ ] **Step 2: Run** → FAIL (module missing).
- [ ] **Step 3: Implement.** Stdlib extractor: an `HTMLParser` that picks the first `<article>`, else `<main>`, else the `<div>` with the most `<p>` text; skips `nav, header, footer, aside, script, style, noscript, form, svg, button`; emits markdown for `h1–h4, p, ul/ol/li, pre/code (language from class), blockquote, table, img, a, strong/em`.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `blog-notes: article extraction and paywall detection`.

### Task 3: `fetch_article.py` — tiers, source package, cache

**Files:**
- Create: `skills/learning/blog-notes/scripts/fetch_article.py`
- Test: `skills/learning/blog-notes/tests/test_fetch.py`

**Interfaces:**
- Consumes: `article_extract.decode_html, extract, paywall_warnings`; `ytn_config.load, location_banner, safe_name`.
- Produces:
  - `normalize_url(url: str) -> str` — lowercase scheme/host, drop `#fragment`, drop `utm_*`, `ref`, `source`, `fbclid`, `gclid` params, strip trailing `/` (except root).
  - `url_hash(url: str) -> str` — `sha1(normalize_url(url))[:10]`.
  - `is_youtube(url: str) -> bool`.
  - `find_cached(sources: Path, url: str) -> Path | None` — folder ending `_<hash>` containing `meta.json`.
  - `write_package(sources: Path, article: dict, url: str, fetch_method: str, warnings: list[str], fetch_images: bool = True) -> Path` — writes `meta.json` (article fields minus `markdown`, plus `url, fetch_method, warnings, fetched`, `images[].file`), `article_<hash>.md` (frontmatter `title, source_url, author, site, published, fetch_method`, then `# Title`, then markdown with image links rewritten to `images/<file>` when downloaded), `images/`.
  - CLI: `fetch_article.py URL [URL...] [--force] [--tiers local,supadata] [--root PATH] [--no-images]`, `fetch_article.py --where`, `fetch_article.py --from-file FILE --url URL [--title TITLE]`. Prints log lines, then `=== RESULT JSON ===` / `=== END RESULT ===` around `{"posts": [{"url", "status": "ok"|"cached"|"truncated"|"failed", "source_dir", "title", "word_count", "fetch_method", "warnings", "error"}], "credits_used": int}`.
  - Exit: 5 if any URL is invalid or YouTube (message names yt-notes); otherwise 0 if ≥ 1 post is ok/cached/truncated; else 3 if every failure was a missing Supadata key after local failed; 4 if every failure was a network error; else 2.
- Tiers: `local` = urllib GET with a browser-like User-Agent (generic, no user details), 20 s timeout, `decode_html` + `extract`; `supadata` = `GET https://api.supadata.ai/v1/web/scrape?url=<url>` with header `x-api-key`, uses returned `content` (markdown) and `name`/`description`, `credits_used += 1`. A tier result with `paywall_warnings` is kept only if no later tier does better (more words without warnings); final status `truncated` if warnings remain.
- `--from-file`: reads markdown (or HTML if it starts with `<`), `fetch_method: "user-provided"`, same package layout.

- [ ] **Step 1: Write failing tests** (no network: monkeypatch `fetch_article.http_get(url, headers) -> (status, content_type, bytes)`):
  - `test_normalize_same_hash`: `https://Ex.com/post/?utm_source=x#faq` and `https://ex.com/post` → same `url_hash`.
  - `test_youtube_rejected`: `main(["https://youtu.be/abc"])` returns 5.
  - `test_package_layout`: fetching `basic_article.html` writes `<Title>_<hash>/meta.json`, `article_<hash>.md` with frontmatter `source_url`, and `images/` with the downloaded image; `meta.json["images"][0]["file"]` set.
  - `test_cached`: second run returns status `cached` without calling `http_get` for the page.
  - `test_image_failures`: a 404 image and a 6 MB image → package still written, warnings mention both, total images ≤ 20 and ≤ 5 MB.
  - `test_truncated_status`: `paywall.html` with `--tiers local` → status `truncated`, package written, exit 0.
  - `test_from_file`: markdown file in → package with `fetch_method == "user-provided"`.
  - `test_missing_key_exit3`: local fails (http 403) and no Supadata key → exit 3 and a `=== CREDENTIALS NEEDED ===` block naming `SUPADATA_API_KEY`.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement** as specified; `main(argv: list[str] | None = None) -> int` so tests can call it.
- [ ] **Step 4: Run** → PASS.
- [ ] **Step 5: Commit** `blog-notes: fetch_article source packages with local and Supadata tiers`.

### Task 4: `notes_paths.py` for blog notes

**Files:**
- Create: `skills/learning/blog-notes/scripts/notes_paths.py`
- Test: `skills/learning/blog-notes/tests/test_notes_paths.py`

**Interfaces:**
- Consumes: package `meta.json` from Task 3; `ytn_config`; yt-notes `notes_paths.py` (index only), loaded with `importlib.util.spec_from_file_location` from `<skill_dir>/../yt-notes/scripts/notes_paths.py`; clear error "blog-notes needs the yt-notes skill installed next to it" if absent.
- Produces CLI:
  - `notes_paths.py where` — banner + `existing topics` list.
  - `notes_paths.py prepare --source DIR [--source DIR ...] --topic T --title T [--format markdown|html] [--mode quick|distilled|deep] [--critique] [--new-location]` → JSON: `format, mode, critique, note_dir, note_file, card_file (html only, else null), note_exists, regenerating_existing_note, renamed_for_collision (null or the original title), explainer_prefix ("<note_dir>/<Title>__"), embed_dir (vault-relative note_dir or null), posts [{tag, title, author, site, url, published, word_count, source_dir, source_wikilink "[[article_<hash>|Saved article]]"}], combined, total_words, previous_posts, added_posts, topic, drive_dir, drive_files, today, max_posts, max_combined_words, max_explainers, existing_topics`.
  - Combined limits: more than `max_posts` sources or `total_words > max_combined_words` → exit 1 with a message suggesting split by subtopic or one note per post plus a hub note.
  - Existing note lookup by frontmatter `source_url` / `source_urls` (same single/subset/superset rule as yt-notes `find_existing_note`).
  - Collision: target `<Topic>/<Title>/<Title>.md` exists and isn't the matched note → title becomes `<Title> (<site of P1>)`; if that exists too, append ` 2`, ` 3`….
  - `notes_paths.py index [--topic T | --all]` → delegates to yt-notes' `cmd_index`.

- [ ] **Step 1: Write failing tests** with a temp `YT_NOTES_ROOT` and fake packages:
  - `test_prepare_single`: markdown format → `note_file` ends `LLM_Engineering/Prompt_Caching/Prompt_Caching.md`, `card_file is None`, `posts[0]["tag"] == "P1"`.
  - `test_regenerate_in_place`: an existing note with `source_url` matching under topic "Other" → returned `note_dir` is that one, `regenerating_existing_note` true.
  - `test_collision_with_video_note`: existing `LLM_Engineering/Prompt_Caching/Prompt_Caching.md` with `video_id` → `note_file` ends `Prompt_Caching_(outcomeschool.com)/Prompt_Caching_(outcomeschool.com).md`, `renamed_for_collision == "Prompt Caching"`.
  - `test_unsafe_title`: title `"Caching: Why? / How"` → folder name has no `: ? /`.
  - `test_limits`: 6 sources → exit 1; 2 sources totalling 45,000 words → exit 1; single source of 45,000 words → OK.
  - `test_add_post`: existing combined note with 2 `source_urls`; prepare with those + 1 → same note, `added_posts` has the new URL, new tag `P3`.
  - `test_index_lists_blog_notes`: after prepare + writing a note with `site`, `index --topic` produces a row whose Source column shows the site.
- [ ] **Step 2: Run** → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** → PASS (test_index_lists_blog_notes needs Task 5's column change; implement Task 5's index part first if running strictly in order, or mark that test to run after Task 5).
- [ ] **Step 5: Commit** `blog-notes: notes_paths prepare/index`.

### Task 5: yt-notes changes — blog-aware checker, explainer mode, index Source column

**Files:**
- Modify: `skills/learning/yt-notes/scripts/check_note.py` (`check_markdown`, `main`)
- Modify: `skills/learning/yt-notes/scripts/notes_paths.py` (`rebuild_topic_index`)
- Test: `skills/learning/yt-notes/tests/test_check_note.py`, `skills/learning/yt-notes/tests/test_index.py`

**Interfaces:**
- Produces:
  - `check_markdown`: when frontmatter has `source_type: blog`, require `source_url` (single) or `source_urls` as an inline list (combined) instead of the video keys; and every `[[<name>.html` link in a non-card markdown note must exist in the note's folder (error).
  - `check_note.py <page.html> --explainer`: runs the HTML checks but doesn't require a card.
  - Index column header `Source` (was `Channel`): `channel`, else `site`, else `"N videos"` / `"N posts"` for combined notes.

- [ ] **Step 1: Write failing tests:** blog note with `source_url` passes; blog note missing it fails naming `source_url`; combined blog note with block-list `source_urls` fails; markdown note linking `[[Missing__X.html|…]]` fails; an explainer page built from the template with one tab passes with `--explainer` and fails without it (missing card); index row for a blog note shows its site; video notes still show channel (regression).
- [ ] **Step 2: Run** `python3 -m unittest discover -s skills/learning/yt-notes/tests -v` → FAIL.
- [ ] **Step 3: Implement.**
- [ ] **Step 4: Run** both skills' test suites → PASS.
- [ ] **Step 5: Commit** `yt-notes: blog-aware checker, explainer check mode, Source index column`.

### Task 6: SKILL.md, references, README

**Files:**
- Create: `skills/learning/blog-notes/SKILL.md`, `README.md`, `references/note-structure.md`, `references/grouping.md`, `references/explainers.md`

**Content decisions (from the spec; wording is the builder's, in yt-notes' style):**
- SKILL.md steps: 1 where (every run) → 2 fetch all URLs (`fetch_article.py`; claude.ai: Supadata connector `supadata_scrape` + `--from-file`; WebFetch never as the body; truncated/failed posts are skipped and reported, the run continues) → 3 read every article fully + look at downloaded images → 4 group (same-concept test, announce in one line, proceed; ask only if the user said "one note" for clearly different concepts) → 5 plan (title, topic reusing existing, mode, which concepts earn an explainer, max `max_explainers`) → 6 `prepare` per note → 7 write markdown note (and explainers via yt-notes template, one tab) → 8 `check_note.py` (note, and each explainer with `--explainer`) → 9 `index` → 10 Drive on claude.ai (gdrive-save, `replace`; skip `images/`) → 11 report (paths, grouping, mode/format, explainers, warnings, credits, skipped posts).
- Modes table, critique add-on, overrides ("no HTML", "full HTML"/"as HTML" → yt-notes HTML format + card), boilerplate skip list, code verbatim rule, staleness callout, opinions attributed, frontmatter example — all as in spec §4–§7, placed in `references/note-structure.md`.
- `references/grouping.md`: the same-concept test, the umbrella-title trap, the table of cases, worked examples (prompt caching + semantic caching → 2 notes; 3 consistent-hashing posts → 1; Part 1–3 → 1; 3+2 mixed → 2), partial-failure gaps.
- `references/explainers.md`: when an explainer earns its place (moves / interactive; static never), single-panel page from `../yt-notes/assets/note-template.html`, naming, placement in the markdown (html-embed block when `embed_dir` is set, plus `[[<file>|Step through it]]`), components pointer to yt-notes `references/html-notes.md` and `visuals.md`.
- Description: trigger on blog/article/post URLs + notes/summary/breakdown/"learn this"; hand YouTube links to yt-notes and local transcript files to lecture-distiller. Draft and sanity-check it with the `anthropic-skills:skill-creator` guidance (no eval run needed).

- [ ] **Step 1:** Write the files.
- [ ] **Step 2:** Verify every script command and flag named in SKILL.md exists: run each with `--help` / `where`.
- [ ] **Step 3: Commit** `blog-notes: SKILL.md, references and README`.

### Task 7: End-to-end sample on the user's reference posts

**Files:**
- Create: `skills/learning/blog-notes/examples/sample-output/LLM_Engineering/Prompt_Caching/Prompt_Caching.md` (+ explainer if one is earned), `.../Semantic_Caching/Semantic_Caching.md`, topic and root `_index.md`

- [ ] **Step 1:** Run the skill's workflow against `https://outcomeschool.com/blog/how-does-prompt-caching-work` and `https://outcomeschool.com/blog/how-does-semantic-caching-work` with `--root` set to a scratch folder.
- [ ] **Step 2:** Expect: grouping says 2 notes; FAQs skipped; `##`/`###` structure; `check_note.py` → `RESULT: OK` for each note and explainer.
- [ ] **Step 3:** Copy the notes and indexes (not `_sources/`) into `examples/sample-output/`.
- [ ] **Step 4: Commit** `blog-notes: sample output`.

### Task 8: Catalog docs and PR

**Files:**
- Modify: `README.md` (Learning table row), `skills/learning/README.md` (table row, "which skill" rule: YouTube link → yt-notes, blog/article URL → blog-notes, files you have → lecture-distiller; install note: blog-notes needs yt-notes and yt-transcript)

- [ ] **Step 1:** Update docs; check `install.sh learning` picks up the new folder (dry read of the script).
- [ ] **Step 2:** Run all tests: both `unittest discover` commands → OK.
- [ ] **Step 3: Commit** `docs: add blog-notes to catalog`, push, `gh pr create --base develop` with a summary, test results, and the user-facing migration note (rename Drive folder, update `~/.yt-notes/config.json`).
