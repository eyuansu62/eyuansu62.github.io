#!/usr/bin/env python

"""Fixture tests for the Notion block to markdown converter.

Runs without a Notion token or network access: the fixtures are recorded block
shapes and image downloads are stubbed. This covers the conversion and file
ownership logic, not the live API calls.

    python bin/test_sync_notion_posts.py
"""

import os
import sys
import tempfile
import importlib.util

HERE = os.path.dirname(os.path.abspath(__file__))
spec = importlib.util.spec_from_file_location("sync", os.path.join(HERE, "sync_notion_posts.py"))
sync = importlib.util.module_from_spec(spec)
spec.loader.exec_module(sync)

failures: list[str] = []


def check(label: str, got, want) -> None:
    if got != want:
        failures.append(f"{label}\n    got:  {got!r}\n    want: {want!r}")
        print(f"  ✗ {label}")
    else:
        print(f"  ✓ {label}")


def rt(text: str, href=None, **flags) -> list[dict]:
    """Build a rich text span list."""
    annotations = {k: flags.get(k, False) for k in ("bold", "italic", "strikethrough", "code")}
    return [{"type": "text", "plain_text": text, "annotations": annotations, "href": href}]


def block(btype: str, payload: dict, children: list | None = None) -> dict:
    b = {"type": btype, btype: payload, "has_children": bool(children)}
    if children:
        b["_children"] = children
    return b


print("rich text")
check("bold", sync.rich_text_to_markdown(rt("x", bold=True)), "**x**")
check("italic", sync.rich_text_to_markdown(rt("x", italic=True)), "_x_")
check("strikethrough", sync.rich_text_to_markdown(rt("x", strikethrough=True)), "~~x~~")
check("link", sync.rich_text_to_markdown(rt("x", href="https://e.com")), "[x](https://e.com)")
check(
    "code span is not also emphasised",
    sync.rich_text_to_markdown(rt("x", code=True, bold=True)),
    "`x`",
)
check(
    "inline equation",
    sync.rich_text_to_markdown([{"type": "equation", "equation": {"expression": "e=mc^2"}}]),
    "$e=mc^2$",
)

print("\nblocks")
sync.download_image = lambda url, page_id, index: f"/assets/img/notion/{page_id}/{index:02d}.png"

body = sync.blocks_to_markdown(
    [
        block("paragraph", {"rich_text": rt("Hello ") + rt("world", bold=True)}),
        block("heading_1", {"rich_text": rt("H1")}),
        block("heading_2", {"rich_text": rt("H2")}),
        block("heading_3", {"rich_text": rt("H3")}),
        block("bulleted_list_item", {"rich_text": rt("a")}),
        block(
            "bulleted_list_item",
            {"rich_text": rt("b")},
            children=[block("bulleted_list_item", {"rich_text": rt("b1")})],
        ),
        block("numbered_list_item", {"rich_text": rt("one")}),
        block("numbered_list_item", {"rich_text": rt("two")}),
        block("to_do", {"rich_text": rt("done"), "checked": True}),
        block("to_do", {"rich_text": rt("todo"), "checked": False}),
        block("code", {"rich_text": rt("print(1)\nprint(2)"), "language": "python"}),
        block("quote", {"rich_text": rt("quoted")}),
        block("callout", {"rich_text": rt("note"), "icon": {"emoji": "💡"}}),
        block("divider", {}),
        block("equation", {"expression": r"\int_0^1 x^2 dx"}),
        block("image", {"file": {"url": "https://s3/presigned?x=1"}, "caption": rt("a cat")}),
        block(
            "table",
            {},
            children=[
                {"type": "table_row", "table_row": {"cells": [rt("h1"), rt("h2")]}},
                {"type": "table_row", "table_row": {"cells": [rt("v1"), rt("v2")]}},
            ],
        ),
        block("bookmark", {"url": "https://ref.com", "caption": rt("ref")}),
        block("mystery_block", {"rich_text": rt("kept text")}),
    ],
    "PAGEID",
)

expected = """\
Hello **world**

## H1

### H2

#### H3

- a
- b
  - b1

1. one
2. two

- [x] done
- [ ] todo

```python
print(1)
print(2)
```

> quoted

> 💡 note

---

$$
\\int_0^1 x^2 dx
$$

![a cat](/assets/img/notion/PAGEID/01.png)

_a cat_

| h1 | h2 |
| --- | --- |
| v1 | v2 |

[ref](https://ref.com)

kept text
"""
check("full document", body, expected)
check("unsupported block reported", "mystery_block" in sync.unsupported_seen, True)

print("\nnumbered list restarts after an interruption")
restart = sync.blocks_to_markdown(
    [
        block("numbered_list_item", {"rich_text": rt("a")}),
        block("numbered_list_item", {"rich_text": rt("b")}),
        block("paragraph", {"rich_text": rt("break")}),
        block("numbered_list_item", {"rich_text": rt("c")}),
    ],
    "P",
)
check("second run starts at 1", "1. c" in restart, True)

print("\nmetadata")
page = {
    "id": "aaaa-bbbb",
    "url": "https://www.notion.so/aaaabbbb",
    "created_time": "2026-01-02T03:04:05.000Z",
    "properties": {
        "Name": {"type": "title", "title": rt("Why: LLM judges drift")},
        "Date": {"type": "date", "date": {"start": "2026-07-15"}},
        "Summary": {"type": "rich_text", "rich_text": rt("A short summary")},
        "Tags": {"type": "multi_select", "multi_select": [{"name": "llm"}, {"name": "eval"}]},
        "Categories": {"type": "multi_select", "multi_select": [{"name": "notes"}]},
        "Status": {"type": "status", "status": {"name": "Published"}},
    },
}
meta = sync.extract_metadata(page)
check("title with a colon", meta["title"], "Why: LLM judges drift")
check("date property wins over created_time", meta["date"].strftime("%Y-%m-%d"), "2026-07-15")
check("description", meta["description"], "A short summary")
check("tags", meta["tags"], ["llm", "eval"])
check("categories", meta["categories"], ["notes"])
check("bare date gets an explicit offset", sync.format_date(meta["date"]).endswith("+0000"), True)

print("\nslugs")
check("colon and case", sync.slugify("Why: LLM Judges Drift"), "why-llm-judges-drift")
check("accents", sync.slugify("Café résumé"), "cafe-resume")
check("cjk falls back to empty", sync.slugify("中文标题"), "")

print("\nfile ownership")
with tempfile.TemporaryDirectory() as tmp:
    posts = os.path.join(tmp, "_posts")
    os.makedirs(posts)
    with open(os.path.join(posts, "2026-01-01-hand-written.md"), "w") as f:
        f.write("---\nlayout: post\ntitle: Mine\n---\n\nbody\n")
    with open(os.path.join(posts, "2026-01-02-from-notion.md"), "w") as f:
        f.write("---\nlayout: post\ntitle: Theirs\nnotion_page_id: abc123\n---\n\nbody\n")
    with open(os.path.join(posts, "2026-01-03-broken.md"), "w") as f:
        f.write("no front matter at all\n")
    original = sync.POSTS_DIR
    sync.POSTS_DIR = posts
    owned = sync.generated_posts()
    sync.POSTS_DIR = original
    check("only notion_page_id files are owned", sorted(owned), ["abc123"])

print("\nroot type detection")


def fake_api(responses: dict):
    """Stub sync.request against a {(method, path_prefix): payload} table.

    A payload of None stands for a 404 that the caller is allowed to absorb.
    """
    calls: list[str] = []

    def request(method, path, body=None, allow_404=False):
        calls.append(f"{method} {path}")
        for (m, prefix), payload in responses.items():
            if m == method and path.startswith(prefix):
                if payload is None and not allow_404:
                    raise AssertionError(f"unexpected fatal 404 for {method} {path}")
                return payload
        raise AssertionError(f"no stub for {method} {path}")

    return request, calls


original_request = sync.request

# A database root resolves through data_sources.
sync.request, calls = fake_api(
    {("GET", "/databases/"): {"data_sources": [{"id": "DS1", "name": "Posts"}]}}
)
check("database root detected", sync.resolve_root("ROOT"), ("database", "DS1"))

# A page root: the database probe 404s, then the page probe succeeds.
sync.request, calls = fake_api(
    {("GET", "/databases/"): None, ("GET", "/pages/"): {"id": "ROOT", "object": "page"}}
)
check("page root detected after 404", sync.resolve_root("ROOT"), ("page", "ROOT"))
check("probed database before page", calls[0].startswith("GET /databases/"), True)

# Page root holding child pages: one post per child.
sync.request, calls = fake_api(
    {
        ("GET", "/blocks/ROOT/children"): {
            "results": [
                {"type": "paragraph", "id": "b1"},
                {"type": "child_page", "id": "c1", "child_page": {"title": "First"}},
                {"type": "child_page", "id": "c2", "child_page": {"title": "Second"}},
            ],
            "has_more": False,
        },
        ("GET", "/pages/c1"): {"id": "c1", "properties": {"title": {"type": "title", "title": rt("First")}}},
        ("GET", "/pages/c2"): {"id": "c2", "properties": {"title": {"type": "title", "title": rt("Second")}}},
    }
)
found = sync.pages_under_page("ROOT")
check("child pages become posts", [p["id"] for p in found], ["c1", "c2"])
check(
    "page-parented title is read from properties.title",
    [sync.extract_metadata(p)["title"] for p in found],
    ["First", "Second"],
)

# Page root with no child pages: the root itself is the post.
sync.request, calls = fake_api(
    {
        ("GET", "/blocks/ROOT/children"): {
            "results": [{"type": "paragraph", "id": "b1"}],
            "has_more": False,
        },
        ("GET", "/pages/ROOT"): {"id": "ROOT", "properties": {"title": {"type": "title", "title": rt("Solo")}}},
    }
)
found = sync.pages_under_page("ROOT")
check("childless root is a single post", [p["id"] for p in found], ["ROOT"])

sync.request = original_request

print("\npage-root publish gate")
pages = [
    {"id": "p1", "properties": {"title": {"type": "title", "title": rt("Real post")}}},
    {"id": "p2", "properties": {"title": {"type": "title", "title": rt("draft: not ready")}}},
]


def gate(pages, import_all, prefixes):
    saved = (sync.IMPORT_ALL, sync.SKIP_TITLE_PREFIXES)
    sync.IMPORT_ALL, sync.SKIP_TITLE_PREFIXES = import_all, prefixes
    try:
        return [p["id"] for p in sync.gate_page_root(list(pages))]
    except SystemExit as e:
        return f"exit {e.code}"
    finally:
        sync.IMPORT_ALL, sync.SKIP_TITLE_PREFIXES = saved


check("writes nothing without an explicit opt-in", gate(pages, False, []), "exit 0")
check("opt-in imports everything", gate(pages, True, []), ["p1", "p2"])
check("prefix holds a draft back", gate(pages, True, ["draft"]), ["p1"])

print("\nyaml safety")
front = sync.yaml.safe_dump(
    {"title": 'Why: "judges" drift', "tags": ["a", "b"]}, allow_unicode=True, sort_keys=False
)
check("round trips a quoted colon title", sync.yaml.safe_load(front)["title"], 'Why: "judges" drift')

print()
if failures:
    print(f"❌ {len(failures)} failure(s):\n")
    for f in failures:
        print(f"  {f}\n")
    sys.exit(1)
print("✅ all converter tests passed")
