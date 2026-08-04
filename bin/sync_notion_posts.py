#!/usr/bin/env python

"""Sync published Notion pages into _posts/ as Jekyll markdown.

Content is imported in full rather than linked, so posts render with the site's
own layout, styling, search and RSS. Hand-written posts in _posts/ are left
alone: this script only creates, overwrites or deletes files that carry a
notion_page_id in their front matter.

Nothing volatile is written into the generated front matter (no sync timestamp,
no last_edited_time), so an unchanged Notion page produces an unchanged file and
git reports no diff. That keeps the workflow from committing on every run.

The root may be either a database or an ordinary page; a Notion URL exposes the
same ID shape for both, so the type is detected rather than configured.

  database root  each row that passes the status filter becomes a post
  page root      each child page becomes a post; a page with no children is
                 itself the post

Publishing to notion.site does not help here. A published page is readable by a
browser but its body is rendered by JavaScript, so there is no HTML to scrape,
and the API still requires a token and an explicit connection either way.

Required environment:
  NOTION_TOKEN   Personal access token (starts with ntn_). The page or database
                 must be shared with it: ••• menu → Add connections.
  NOTION_ROOT_ID The 32-character ID from the Notion URL. Database or page.
                 NOTION_DATABASE_ID is accepted as a fallback name.

Optional environment:
  NOTION_STATUS_PROPERTY   Database root only. Property gating publication
                           (default "Status"). Set to an empty string to import
                           every row.
  NOTION_STATUS_VALUE      Database root only. Value meaning published
                           (default "Published").
  NOTION_IMPORT_ALL        Page root only. Must be true to write anything, since
                           a child page has no status property to filter on.
  NOTION_SKIP_TITLE_PREFIX Page root only. Comma-separated title prefixes to
                           hold back, for example "draft,WIP".
"""

import os
import re
import sys
import json
import shutil
import mimetypes
import unicodedata
import urllib.error
import urllib.request
from datetime import datetime, timezone

import yaml

API = "https://api.notion.com/v1"

# Pinned deliberately. Notion's API is versioned by release date and the data
# model changes between versions; 2025-09-03 replaced the database query
# endpoint with the data source one used below. Bumping this string requires
# re-reading the upgrade guide, not just editing the number.
NOTION_VERSION = "2026-03-11"

POSTS_DIR = "_posts"
IMAGE_DIR = os.path.join("assets", "img", "notion")
PAGE_SIZE = 100

TOKEN = os.environ.get("NOTION_TOKEN", "").strip()
# Accepts a database ID or an ordinary page ID; a Notion URL looks the same for
# both. NOTION_DATABASE_ID is kept as a fallback for the earlier name.
ROOT_ID = (
    os.environ.get("NOTION_ROOT_ID", "") or os.environ.get("NOTION_DATABASE_ID", "")
).strip()
STATUS_PROPERTY = os.environ.get("NOTION_STATUS_PROPERTY", "Status").strip()
STATUS_VALUE = os.environ.get("NOTION_STATUS_VALUE", "Published").strip()
# "link"  writes a stub carrying only title, date, summary and a redirect to
#         Notion, so readers see the page exactly as Notion renders it.
# "full"  converts the body to markdown and serves it from this site instead,
#         which gains search, RSS and the site's own styling but never looks
#         identical to Notion.
LINK_ONLY = os.environ.get("NOTION_IMPORT_MODE", "link").strip().lower() != "full"
# Page-root mode only; see gate_page_root().
IMPORT_ALL = os.environ.get("NOTION_IMPORT_ALL", "").strip().lower() in ("1", "true", "yes")
SKIP_TITLE_PREFIXES = [
    p.strip() for p in os.environ.get("NOTION_SKIP_TITLE_PREFIX", "").split(",") if p.strip()
]

# Block types that carry no content worth importing. Anything not handled and
# not listed here is reported, so a silently half-imported post is impossible.
IGNORED_BLOCKS = {"table_of_contents", "breadcrumb", "column_list", "column"}

unsupported_seen: set[str] = set()


def request(
    method: str, path: str, body: dict | None = None, allow_status: tuple[int, ...] = ()
):
    """Call the Notion API and return the decoded JSON response.

    Any failure is fatal, because a partial import is worse than none. The
    exception is allow_status, whose codes return None so the caller can react;
    it exists for the database-or-page probe in resolve_root().
    """
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(
        f"{API}{path}",
        data=data,
        method=method,
        headers={
            "Authorization": f"Bearer {TOKEN}",
            "Notion-Version": NOTION_VERSION,
            "Content-Type": "application/json",
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            return json.load(resp)
    except urllib.error.HTTPError as e:
        if e.code in allow_status:
            return None
        detail = e.read().decode(errors="replace")
        print(f"❌ {method} {path} failed: HTTP {e.code}\n   {detail}")
        if e.code == 404:
            print(
                "   A 404 also means the connection cannot see this content.\n"
                "   In Notion open the page, ••• menu → Add connections, and pick your token."
            )
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"❌ {method} {path} failed: {e.reason}")
        sys.exit(1)


def resolve_root(root_id: str) -> tuple[str, str]:
    """Detect whether the configured ID names a database or an ordinary page.

    A Notion URL exposes the same 32-character ID shape for both, and asking
    the user which they have is a question the API can answer. Returns
    ("database", data_source_id) or ("page", page_id).
    """
    # Both codes mean "not a database": 404 when the connection cannot see it,
    # and 400 validation_error when the ID resolves to a page, which is what
    # Notion actually returns for a page ID ("is a page, not a database").
    db = request("GET", f"/databases/{root_id}", allow_status=(400, 404))
    if db is not None:
        sources = db.get("data_sources") or []
        if not sources:
            print(f"❌ Database {root_id} exposes no data sources.")
            sys.exit(1)
        if len(sources) > 1:
            names = ", ".join(s.get("name", "?") for s in sources)
            print(f"⚠️  Database has {len(sources)} data sources ({names}); using the first.")
        return "database", sources[0]["id"]

    # Not a database. A page probe failing is fatal and reports the sharing hint.
    request("GET", f"/pages/{root_id}")
    return "page", root_id


def pages_under_page(root_id: str) -> list[dict]:
    """Collect posts when the root is an ordinary page rather than a database.

    Child pages become one post each. A root with no child pages is itself the
    article, which is the shape of a single published Notion write-up.
    """
    children, cursor = [], None
    while True:
        query = f"?page_size={PAGE_SIZE}" + (f"&start_cursor={cursor}" if cursor else "")
        result = request("GET", f"/blocks/{root_id}/children{query}")
        children.extend(result.get("results", []))
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")

    child_pages = [b for b in children if b.get("type") == "child_page"]
    if not child_pages:
        print("No child pages found; treating the root page itself as a single post.")
        return [request("GET", f"/pages/{root_id}")]

    print(f"Found {len(child_pages)} child page(s) under the root page.")
    return [request("GET", f"/pages/{b['id']}") for b in child_pages]


def gate_page_root(pages: list[dict]) -> list[dict]:
    """Apply the opt-in gate that page-root mode needs instead of a status property.

    A child page carries only a title, so there is nothing to filter on and the
    default would be to publish everything under that parent to a public site.
    That has to be an explicit choice, not a default.
    """
    titles = [extract_metadata(p)["title"] for p in pages]
    skipped = []
    if SKIP_TITLE_PREFIXES:
        keep = []
        for page, title in zip(pages, titles):
            if any(title.lower().startswith(p.lower()) for p in SKIP_TITLE_PREFIXES):
                skipped.append(title)
            else:
                keep.append(page)
        pages = keep

    print("\nPages this run would publish:")
    for title in [extract_metadata(p)["title"] for p in pages]:
        print(f"  • {title}")
    for title in skipped:
        print(f"  – {title} (skipped by NOTION_SKIP_TITLE_PREFIX)")

    if not IMPORT_ALL:
        print(
            "\n⛔ Nothing written. The root is a page, not a database, so there is no\n"
            "   Status property to gate publication and every page listed above would\n"
            "   go live. Review the list, then opt in explicitly:\n"
            "     NOTION_IMPORT_ALL=true\n"
            "   To hold some back, set NOTION_SKIP_TITLE_PREFIX to a comma-separated\n"
            "   list of title prefixes, for example: draft,WIP,TODO"
        )
        sys.exit(0)
    return pages


def query_pages(data_source_id: str) -> list[dict]:
    """Return every page in the data source that passes the status filter."""
    body: dict = {
        "page_size": PAGE_SIZE,
        "sorts": [{"timestamp": "created_time", "direction": "descending"}],
    }
    if STATUS_PROPERTY:
        # status and select properties are queried with different filter keys,
        # and the property's actual type is not known ahead of time, so accept
        # either rather than guessing.
        body["filter"] = {
            "or": [
                {"property": STATUS_PROPERTY, "status": {"equals": STATUS_VALUE}},
                {"property": STATUS_PROPERTY, "select": {"equals": STATUS_VALUE}},
            ]
        }

    pages, cursor = [], None
    while True:
        if cursor:
            body["start_cursor"] = cursor
        result = request("POST", f"/data_sources/{data_source_id}/query", body)
        pages.extend(result.get("results", []))
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
    return pages


def fetch_blocks(block_id: str) -> list[dict]:
    """Fetch a block's children, recursing into nested blocks.

    The API returns only one level at a time, so children are attached under a
    "_children" key for the converter to indent.
    """
    blocks, cursor = [], None
    while True:
        query = f"?page_size={PAGE_SIZE}" + (f"&start_cursor={cursor}" if cursor else "")
        result = request("GET", f"/blocks/{block_id}/children{query}")
        for block in result.get("results", []):
            if block.get("has_children"):
                block["_children"] = fetch_blocks(block["id"])
            blocks.append(block)
        if not result.get("has_more"):
            break
        cursor = result.get("next_cursor")
    return blocks


def rich_text_to_markdown(spans: list[dict]) -> str:
    """Convert Notion rich text spans to inline markdown."""
    out = []
    for span in spans:
        if span.get("type") == "equation":
            out.append(f"${span.get('equation', {}).get('expression', '')}$")
            continue

        text = span.get("plain_text", "")
        if not text:
            continue
        ann = span.get("annotations", {})

        # Code first: markdown emphasis is not parsed inside a code span, so
        # wrapping the other way round would emit literal asterisks.
        if ann.get("code"):
            text = f"`{text}`"
        else:
            if ann.get("bold"):
                text = f"**{text}**"
            if ann.get("italic"):
                text = f"_{text}_"
            if ann.get("strikethrough"):
                text = f"~~{text}~~"

        href = span.get("href")
        if href:
            text = f"[{text}]({href})"
        out.append(text)
    return "".join(out)


def plain_text(spans: list[dict]) -> str:
    return "".join(s.get("plain_text", "") for s in spans)


def download_image(url: str, page_id: str, index: int) -> str | None:
    """Save a Notion-hosted image into the repo and return its site path.

    Notion's file URLs are presigned and expire after one hour, so writing them
    straight into markdown produces images that work during the sync and break
    shortly after.
    """
    target_dir = os.path.join(IMAGE_DIR, page_id)
    os.makedirs(target_dir, exist_ok=True)
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "notion-sync"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            payload = resp.read()
            ext = mimetypes.guess_extension(
                (resp.headers.get_content_type() or "").split(";")[0]
            )
    except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
        print(f"⚠️  Could not download image {index} of {page_id}: {e}")
        return None

    if ext in (None, ".jpe"):
        ext = ".jpg" if ext == ".jpe" else os.path.splitext(url.split("?")[0])[1] or ".png"
    name = f"{index:02d}{ext}"
    with open(os.path.join(target_dir, name), "wb") as f:
        f.write(payload)
    return f"/{IMAGE_DIR}/{page_id}/{name}"


def block_to_markdown(block: dict, page_id: str, counters: dict, depth: int = 0) -> list[str]:
    """Convert one block (and its children) to markdown lines."""
    btype = block.get("type", "")
    data = block.get(btype, {}) if isinstance(block.get(btype), dict) else {}
    spans = data.get("rich_text", [])
    indent = "  " * depth
    lines: list[str] = []

    def children(list_depth: int = depth) -> list[str]:
        out = []
        for child in block.get("_children", []):
            out.extend(block_to_markdown(child, page_id, counters, list_depth))
        return out

    if btype == "paragraph":
        text = rich_text_to_markdown(spans)
        if text:
            lines.append(indent + text)
        lines.extend(children())

    elif btype in ("heading_1", "heading_2", "heading_3"):
        # The post title is the page's h1, so headings shift down one level.
        hashes = {"heading_1": "##", "heading_2": "###", "heading_3": "####"}[btype]
        lines.append(f"{hashes} {rich_text_to_markdown(spans)}")
        lines.extend(children())

    elif btype == "bulleted_list_item":
        lines.append(f"{indent}- {rich_text_to_markdown(spans)}")
        lines.extend(children(depth + 1))

    elif btype == "numbered_list_item":
        counters[depth] = counters.get(depth, 0) + 1
        lines.append(f"{indent}{counters[depth]}. {rich_text_to_markdown(spans)}")
        lines.extend(children(depth + 1))

    elif btype == "to_do":
        mark = "x" if data.get("checked") else " "
        lines.append(f"{indent}- [{mark}] {rich_text_to_markdown(spans)}")
        lines.extend(children(depth + 1))

    elif btype == "code":
        language = (data.get("language") or "").replace(" ", "-")
        language = "" if language == "plain-text" else language
        lines.append(f"```{language}")
        lines.extend(plain_text(spans).split("\n"))
        lines.append("```")

    elif btype == "quote":
        for line in rich_text_to_markdown(spans).split("\n"):
            lines.append(f"> {line}")
        # Nested content stays inside the quote, so it is prefixed too.
        for line in children(0):
            lines.append(f"> {line}" if line else ">")

    elif btype == "callout":
        icon = (data.get("icon") or {}).get("emoji", "")
        body = rich_text_to_markdown(spans)
        lines.append(f"> {icon} {body}".rstrip())

    elif btype == "divider":
        lines.append("---")

    elif btype == "equation":
        lines.append("$$")
        lines.append(data.get("expression", ""))
        lines.append("$$")

    elif btype == "image":
        source = data.get("file", {}).get("url") or data.get("external", {}).get("url")
        caption = rich_text_to_markdown(data.get("caption", []))
        if source:
            counters["images"] = counters.get("images", 0) + 1
            if data.get("file"):
                path = download_image(source, page_id, counters["images"])
            else:
                path = source  # externally hosted; no expiry to work around
            if path:
                lines.append(f"![{caption}]({path})")
                if caption:
                    lines.append("")
                    lines.append(f"_{caption}_")

    elif btype == "toggle":
        lines.append("<details>")
        lines.append(f"<summary>{rich_text_to_markdown(spans)}</summary>")
        lines.append("")
        lines.extend(children())
        lines.append("")
        lines.append("</details>")

    elif btype in ("bookmark", "embed", "link_preview", "video", "file", "pdf"):
        url = data.get("url") or data.get("external", {}).get("url") or data.get("file", {}).get("url", "")
        caption = rich_text_to_markdown(data.get("caption", [])) or url
        if url:
            lines.append(f"[{caption}]({url})")

    elif btype == "table":
        rows = block.get("_children", [])
        for row_index, row in enumerate(rows):
            cells = row.get("table_row", {}).get("cells", [])
            lines.append("| " + " | ".join(rich_text_to_markdown(c) for c in cells) + " |")
            if row_index == 0:
                lines.append("| " + " | ".join("---" for _ in cells) + " |")

    elif btype in IGNORED_BLOCKS:
        lines.extend(children())

    else:
        unsupported_seen.add(btype)
        text = rich_text_to_markdown(spans)
        if text:
            lines.append(indent + text)

    return lines


LIST_BLOCKS = ("bulleted_list_item", "numbered_list_item", "to_do")


def blocks_to_markdown(blocks: list[dict], page_id: str) -> str:
    """Convert a page's blocks to a markdown body.

    Blank lines are inserted *between* rendered blocks rather than after each
    one, and skipped only between consecutive items of the same list kind. The
    distinction matters: kramdown absorbs a fenced code block into the
    preceding list item when no blank line separates them, and reads a numbered
    list that directly follows a bulleted one as a continuation of it.
    """
    out: list[str] = []
    counters: dict = {}
    previous = ""
    for block in blocks:
        btype = block.get("type", "")
        # Numbering restarts whenever another kind of block interrupts the run.
        if btype != "numbered_list_item" and previous == "numbered_list_item":
            counters = {k: v for k, v in counters.items() if k == "images"}

        rendered = block_to_markdown(block, page_id, counters)
        if rendered:
            if out and not (btype in LIST_BLOCKS and previous == btype):
                out.append("")
            out.extend(rendered)
        previous = btype

    body = "\n".join(out)
    return re.sub(r"\n{3,}", "\n\n", body).strip() + "\n"


def blocks_to_plain_text(blocks: list[dict]) -> list[str]:
    """Flatten a page to plain paragraphs, ignoring formatting and layout.

    Used by link mode, which needs a word count for the reading estimate and an
    opening paragraph for the list summary, but not the markdown body.
    """
    out: list[str] = []
    for block in blocks:
        btype = block.get("type", "")
        data = block.get(btype, {}) if isinstance(block.get(btype), dict) else {}
        text = plain_text(data.get("rich_text", []) or []).strip()
        if text:
            out.append(text)
        if btype == "table_row":
            cells = data.get("cells", []) or []
            joined = " ".join(plain_text(c) for c in cells).strip()
            if joined:
                out.append(joined)
        out.extend(blocks_to_plain_text(block.get("_children", [])))
    return out


def summarise(paragraphs: list[str], limit: int = 200) -> str:
    """Take the opening prose as the list summary.

    Headings and table rows make poor summaries, so prefer the first paragraph
    long enough to read like one.
    """
    for text in paragraphs:
        if len(text) >= 40:
            return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"
    return paragraphs[0][:limit] if paragraphs else ""


def property_value(props: dict, names: list[str], kinds: list[str]):
    """Read the first property matching one of `names` with one of `kinds`."""
    for name in names:
        for key, prop in props.items():
            if key.lower() != name.lower():
                continue
            if prop.get("type") not in kinds:
                continue
            return prop
    return None


def format_date(value: datetime) -> str:
    """Format a date for Jekyll front matter, always with an explicit offset.

    A Notion date property may be a bare date with no time zone; Jekyll then
    falls back to the build machine's zone, which differs between a local build
    and the CI runner and would silently shift a post across a day boundary.
    """
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.strftime("%Y-%m-%d %H:%M:%S %z")


def slugify(value: str) -> str:
    """Build a filename-safe slug, transliterating accents and dropping CJK."""
    value = unicodedata.normalize("NFKD", value)
    value = value.encode("ascii", "ignore").decode()
    value = re.sub(r"[^\w\s-]", "", value).strip().lower()
    return re.sub(r"[\s_-]+", "-", value).strip("-")


def extract_metadata(page: dict) -> dict:
    """Pull title, date, description, tags and categories from page properties."""
    props = page.get("properties", {})

    title = ""
    for prop in props.values():
        if prop.get("type") == "title":
            title = plain_text(prop.get("title", []))
            break

    date_prop = property_value(props, ["Date", "Published", "Published at"], ["date"])
    raw_date = (date_prop or {}).get("date", {}).get("start") if date_prop else None
    raw_date = raw_date or page.get("created_time")
    try:
        parsed = datetime.fromisoformat(raw_date.replace("Z", "+00:00"))
    except (AttributeError, ValueError):
        parsed = datetime.now(timezone.utc)

    desc_prop = property_value(props, ["Description", "Summary", "Excerpt"], ["rich_text"])
    description = plain_text((desc_prop or {}).get("rich_text", [])) if desc_prop else ""

    def multi(names: list[str]) -> list[str]:
        prop = property_value(props, names, ["multi_select"])
        if not prop:
            return []
        return [o.get("name", "") for o in prop.get("multi_select", []) if o.get("name")]

    return {
        "title": title or "Untitled",
        "date": parsed,
        "description": description,
        "tags": multi(["Tags", "Tag"]),
        "categories": multi(["Categories", "Category"]),
    }


def write_post(page: dict) -> str:
    """Render one Notion page to a markdown file and return its path."""
    page_id = page["id"].replace("-", "")
    meta = extract_metadata(page)

    blocks = fetch_blocks(page["id"])
    # public_url is set only while the page is published to the web, and it is
    # the one a reader can actually open. `url` points into the private
    # workspace app, so linking that would send readers to a login screen.
    notion_url = page.get("public_url") or page.get("url", "")

    front: dict = {
        "layout": "post",
        "title": meta["title"],
        "date": format_date(meta["date"]),
        "notion_page_id": page_id,
        "notion_url": notion_url,
    }

    if LINK_ONLY:
        print(f"...linking “{meta['title']}”")
        paragraphs = blocks_to_plain_text(blocks)
        if not notion_url.startswith("http"):
            print(
                f"⚠️  “{meta['title']}” has no public URL, so there is nothing to link to.\n"
                "   Publish the page to the web in Notion, or set NOTION_IMPORT_MODE=full."
            )
        # redirect makes /blog/ link straight out and turns the generated post
        # page into a forwarding stub; external_source labels it in the list.
        front["redirect"] = notion_url
        front["external_source"] = "Notion"
        # Only the estimate is kept, not the text it was derived from. al-folio
        # normally word-counts feed_content, but storing the body in front
        # matter would put it in the repository after all, which is the thing
        # link mode exists to avoid.
        words = sum(len(p.split()) + len(re.findall(r"[一-鿿]", p)) for p in paragraphs)
        front["reading_time"] = max(1, round(words / 180))
        if not meta["description"]:
            meta["description"] = summarise(paragraphs)
        body = (
            f"This post lives in Notion and is rendered there.\n\n"
            f"[Open it on Notion]({notion_url})\n"
        )
    else:
        print(f"...importing “{meta['title']}”")
        body = blocks_to_markdown(blocks, page_id)

    if meta["description"]:
        front["description"] = meta["description"]
    if meta["tags"]:
        front["tags"] = meta["tags"]
    if meta["categories"]:
        front["categories"] = meta["categories"]

    slug = slugify(meta["title"]) or page_id[:12]
    path = os.path.join(POSTS_DIR, f"{meta['date'].strftime('%Y-%m-%d')}-{slug}.md")

    # safe_dump so a title containing a colon or quotes cannot break the YAML.
    header = yaml.safe_dump(front, allow_unicode=True, sort_keys=False, default_flow_style=False)
    with open(path, "w", encoding="utf-8") as f:
        f.write(f"---\n{header}---\n\n{body}")
    return path


def generated_posts() -> dict[str, str]:
    """Map notion_page_id to file path for every post this script generated."""
    owned = {}
    if not os.path.isdir(POSTS_DIR):
        return owned
    for name in os.listdir(POSTS_DIR):
        if not name.endswith((".md", ".markdown")):
            continue
        path = os.path.join(POSTS_DIR, name)
        with open(path, encoding="utf-8") as f:
            if f.readline().strip() != "---":
                continue
            raw = []
            for line in f:
                if line.strip() == "---":
                    break
                raw.append(line)
        try:
            front = yaml.safe_load("".join(raw)) or {}
        except yaml.YAMLError:
            continue
        page_id = front.get("notion_page_id")
        if page_id:
            owned[str(page_id)] = path
    return owned


def main() -> None:
    if not TOKEN or not ROOT_ID:
        print(
            "❌ NOTION_TOKEN and NOTION_ROOT_ID must both be set.\n"
            "   Create a personal access token under Personal access tokens in Notion's\n"
            "   developer portal, store it as a repository secret, and share the target\n"
            "   page or database with it: ••• menu → Add connections.\n"
            "   NOTION_ROOT_ID is the 32-character ID from the Notion URL and may name\n"
            "   either a database or an ordinary page."
        )
        sys.exit(1)

    os.makedirs(POSTS_DIR, exist_ok=True)
    before = generated_posts()

    kind, resolved = resolve_root(ROOT_ID)
    if kind == "database":
        print(f"Root is a database; querying data source {resolved}")
        pages = query_pages(resolved)
        filter_note = f" matching {STATUS_PROPERTY} = {STATUS_VALUE}" if STATUS_PROPERTY else ""
        print(f"Found {len(pages)} page(s){filter_note}")
        if STATUS_PROPERTY and not pages:
            print(
                f"⚠️  No pages matched. Check that the “{STATUS_PROPERTY}” property exists and "
                f"that at least one page is set to “{STATUS_VALUE}”."
            )
    else:
        print(f"Root is a page ({resolved})")
        pages = gate_page_root(pages_under_page(resolved))

    seen: set[str] = set()
    for page in pages:
        page_id = page["id"].replace("-", "")
        seen.add(page_id)
        # Regenerate unconditionally; git decides whether anything changed.
        stale = before.get(page_id)
        if stale and os.path.exists(stale):
            os.remove(stale)
        write_post(page)

    for page_id, path in before.items():
        if page_id not in seen:
            print(f"...removing {path} (no longer published in Notion)")
            if os.path.exists(path):
                os.remove(path)
            assets = os.path.join(IMAGE_DIR, page_id)
            if os.path.isdir(assets):
                shutil.rmtree(assets)

    if unsupported_seen:
        print(
            "⚠️  Block types with no dedicated handler (text was kept, formatting was not): "
            + ", ".join(sorted(unsupported_seen))
        )

    print(f"✅ {len(seen)} post(s) in {POSTS_DIR}")


if __name__ == "__main__":
    main()
