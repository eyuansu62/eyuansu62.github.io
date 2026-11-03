"""Import new Scholar papers without rewriting the curated bibliography."""

import calendar
from datetime import datetime
from html import escape, unescape
from pathlib import Path
import re
import unicodedata
from urllib.parse import parse_qs, urlsplit, urlunsplit

import bibtexparser
from bibtexparser.bibdatabase import BibDatabase
from bibtexparser.bwriter import BibTexWriter
from bs4 import BeautifulSoup
import requests


CURATED_FILE = Path("_bibliography/papers.bib")
MANAGED_FILE = Path("_bibliography/scholar.bib")
HEADER = "% Automatically imported from Google Scholar. Put customizations in papers.bib.\n\n"
ARXIV_ID = re.compile(r"arxiv(?:\.org/(?:abs|pdf)/|:\s*)(\d{4}\.\d{4,5})", re.I)


def publication_id(publication: dict, scholar_user_id: str) -> str:
    value = publication.get("author_pub_id") or publication.get("pub_id", "")
    match = re.fullmatch(re.escape(scholar_user_id) + r":([\w-]+)", str(value), re.ASCII)
    if not match:
        raise ValueError(f"Invalid Scholar publication ID: {value!r}")
    return match[1]


def valid_year(value) -> bool:
    return bool(re.fullmatch(r"\d{4}", str(value))) and 1900 <= int(value) <= datetime.now().year + 1


def identities(entry: dict) -> set[str]:
    """Strong identifiers and normalized titles catch preprint/venue duplicates."""
    result = set()
    if entry.get("google_scholar_id"):
        result.add("scholar:" + entry["google_scholar_id"])
    title = unicodedata.normalize("NFKC", unescape(entry.get("title", ""))).casefold()
    title = "".join(c for c in title if c.isalnum())
    if title:
        result.add("title:" + title)
    for key in ("pdf", "html", "url", "journal", "booktitle", "citation", "doi"):
        value = unescape(str(entry.get(key, "")))
        for match in ARXIV_ID.finditer(value):
            result.add("arxiv:" + match[1])
        doi = re.search(r"10\.\d{4,9}/[^\s?#{}]+", value, re.I)
        if doi:
            result.add("doi:" + doi[0].rstrip(".,)").casefold())
        if key in ("pdf", "html", "url") and value:
            parts = urlsplit(value)
            if parts.scheme in ("http", "https") and parts.hostname and not parts.hostname.startswith("scholar.google."):
                # Query parameters identify papers on OpenReview and many publishers.
                query = "?" + parts.query if parts.query else ""
                if parts.path.rstrip("/") or query:
                    result.add("url:" + parts.netloc.casefold() + parts.path.rstrip("/") + query)
    return result


def safe_url(value: str) -> str:
    parts = urlsplit(value)
    if parts.scheme not in ("http", "https") or not parts.hostname:
        return ""
    return urlunsplit(parts)


def bibtex_text(value: str) -> str:
    # Scholar metadata is plain text, not HTML, BibTeX commands or inline JS.
    value = " ".join(value.split()).translate(str.maketrans({
        "\\": "∖", "{": "｛", "}": "｝", "'": "’", '"': "”"
    }))
    return escape(value, quote=False)


def fetch_profile(scholar_user_id: str) -> dict:
    """Fetch paginated profile records with bounded requests and no proxy fallback."""
    papers = []
    seen = set()
    with requests.Session() as session:
        session.headers.update({"User-Agent": "Mozilla/5.0"})
        for _ in range(100):
            response = session.get(
                "https://scholar.google.com/citations",
                params={"user": scholar_user_id, "hl": "en", "sortby": "pubdate", "pagesize": 100, "cstart": len(papers)},
                timeout=15,
            )
            response.raise_for_status()
            soup = BeautifulSoup(response.text, "html.parser")
            rows = soup.select("tr.gsc_a_tr")
            if soup.select_one("#gsc_prf_in") is None or not rows:
                raise ValueError("Scholar did not return a complete profile page")
            for row in rows:
                title = row.select_one("a.gsc_a_at")
                if title is None:
                    raise ValueError("Scholar returned an incomplete publication row")
                query = parse_qs(urlsplit(title.get("href", "")).query)
                identifier = query.get("citation_for_view", [""])[0]
                paper = {"author_pub_id": identifier, "bib": {"title": title.get_text(" ", strip=True)}}
                publication_id(paper, scholar_user_id)
                if identifier in seen:
                    raise ValueError("Scholar pagination repeated a publication instead of advancing")
                seen.add(identifier)
                year = row.select_one(".gsc_a_y .gsc_a_h")
                if year is not None:
                    paper["bib"]["pub_year"] = year.get_text(strip=True)
                details = row.select("div.gs_gray")
                paper["bib"]["citation"] = details[1].get_text(" ", strip=True) if len(details) > 1 else ""
                count = row.select_one("a.gsc_a_ac")
                value = re.sub(r"[,*\s]", "", count.get_text()) if count is not None else ""
                paper["num_citations"] = int(value) if value else 0
                papers.append(paper)
            more = soup.select_one("#gsc_bpf_more")
            if more is not None and more.has_attr("disabled"):
                return {"publications": papers}
            if more is None and len(rows) < 100:
                return {"publications": papers}
        raise ValueError("Scholar profile exceeded the pagination safety limit")


def fetch_publication(publication: dict, scholar_user_id: str) -> dict:
    """Read full authors and the complete date from one Scholar detail page."""
    scholar_id = publication_id(publication, scholar_user_id)
    url = (
        "https://scholar.google.com/citations?view_op=view_citation&hl=en"
        f"&citation_for_view={scholar_user_id}:{scholar_id}"
    )
    response = requests.get(url, timeout=15, headers={"User-Agent": "Mozilla/5.0"})
    response.raise_for_status()
    soup = BeautifulSoup(response.text, "html.parser")
    title_node = soup.select_one("#gsc_oci_title")
    if title_node is None:
        raise ValueError(f"Scholar did not return publication details for {scholar_id}")
    title = title_node.get_text(" ", strip=True)
    if title.endswith("…"):
        merged = soup.select_one("#gsc_oci_merged_snippet div")
        if merged:
            title = merged.get_text(" ", strip=True)
    fields = {}
    for row in soup.select(".gs_scl"):
        label, value = row.select_one(".gsc_oci_field"), row.select_one(".gsc_oci_value")
        if label is not None and value is not None:
            fields[label.get_text(strip=True).casefold()] = value.get_text(" ", strip=True)
    author = fields.get("authors", "")
    date = fields.get("publication date", str(publication["bib"].get("pub_year", "")))
    parts = date.split("/")
    if not title or not author or not valid_year(parts[0]):
        raise ValueError(f"Incomplete Scholar metadata for {scholar_id}: {title!r}")
    if len(parts) > 3:
        raise ValueError(f"Invalid publication date: {date!r}")
    entry = {
        "ID": "scholar_" + scholar_id,
        "ENTRYTYPE": "inproceedings" if fields.get("conference") else "article",
        "title": bibtex_text(title),
        "author": bibtex_text(" and ".join(name.strip() for name in author.split(","))),
        "year": parts[0],
        "google_scholar_id": scholar_id,
        "html": url,
    }
    if len(parts) >= 2:
        month = int(parts[1])
        if not 1 <= month <= 12:
            raise ValueError(f"Invalid publication date: {date!r}")
        entry["month"] = calendar.month_abbr[month].lower()
        if len(parts) == 3:
            day = int(parts[2])
            datetime(int(parts[0]), month, day)  # Validate leap years and month lengths.
            entry["day"] = f"{day:02}"
    for source, target in (
        ("journal", "journal"), ("conference", "booktitle"), ("volume", "volume"),
        ("issue", "number"), ("pages", "pages"), ("publisher", "publisher"),
    ):
        if fields.get(source):
            entry[target] = bibtex_text(fields[source])
    link = soup.select_one("a.gsc_oci_title_link")
    target = safe_url(link.get("href", "")) if link else ""
    if target:
        arxiv = ARXIV_ID.search(target)
        if arxiv:
            entry["pdf"] = "https://arxiv.org/abs/" + arxiv[1]
            if "journal" not in entry and "booktitle" not in entry:
                entry["journal"] = "arXiv preprint arXiv:" + arxiv[1]
            if entry.get("journal", "").casefold().startswith("arxiv"):
                entry["abbr"] = "arXiv"
        elif urlsplit(target).path.lower().endswith(".pdf"):
            entry["pdf"] = escape(target, quote=True)
        else:
            entry["html"] = escape(target, quote=True)
    return entry


def read_entries(text: str) -> list[dict]:
    parser = bibtexparser.bparser.BibTexParser(common_strings=True)
    parser.ignore_nonstandard_types = False
    entries = bibtexparser.loads(text, parser=parser).entries
    # bibtexparser treats some broken entries as comments; never silently drop them.
    expected = len(re.findall(r"(?mi)^\s*@(?!(?:comment|preamble|string)\b)\w+\s*[{(]", text))
    if len(entries) != expected or len({e["ID"] for e in entries}) != len(entries):
        raise ValueError("Bibliography contains malformed or duplicate entries")
    return entries


def prepare_bibliography(publications: list[dict], scholar_user_id: str) -> str:
    """Return an updated managed file; fetch/validation failures write nothing."""
    curated = read_entries(CURATED_FILE.read_text(encoding="utf-8"))
    existing_text = MANAGED_FILE.read_text(encoding="utf-8") if MANAGED_FILE.exists() else ""
    known = set().union(*(identities(entry) for entry in curated))
    managed = []
    existing = read_entries(existing_text)
    for entry in existing:
        # Moving an auto-import into papers.bib gives the curated entry priority.
        if not known.intersection(identities(entry)):
            managed.append(entry)
            known.update(identities(entry))
    for publication in publications:
        bib = publication.get("bib", {})
        if not valid_year(bib.get("pub_year", "")):
            print(f"Skipping undated/invalid-year Scholar record: {bib.get('title', 'Unknown')}")
            continue
        scholar_id = publication_id(publication, scholar_user_id)
        summary = {**bib, "google_scholar_id": scholar_id}
        if known.intersection(identities(summary)):
            continue
        entry = fetch_publication(publication, scholar_user_id)
        matches = known.intersection(identities(entry))
        if matches:
            known.add("scholar:" + scholar_id)
            print(f"Skipping duplicate Scholar record: {bib.get('title')} ({', '.join(sorted(matches))})")
            continue
        managed.append(entry)
        known.update(identities(entry))
        print(f"Importing publication: {unescape(entry['title'])}")
    if managed == existing and existing_text:
        return existing_text
    database = BibDatabase()
    database.entries = managed
    writer = BibTexWriter()
    writer.indent = "  "
    candidate = HEADER + writer.write(database)
    read_entries(candidate)
    return candidate
