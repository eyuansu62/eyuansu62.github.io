"""Offline fixtures for automatic imports, duplicate detection and failure safety."""

from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import requests

import sync_scholar_publications as sync


USER = "test_user"
CURATED = """---
---
@article{curated,
  title={A Curated Paper},
  author={Qin, Bowen},
  year={2026},
  google_scholar_id={existing},
  selected={true},
  annotation={Keep my note},
  pdf={https://arxiv.org/abs/2601.12345}
}
"""


def publication(scholar_id="new", title="A New Paper", year="2026", citation=""):
    return {"author_pub_id": f"{USER}:{scholar_id}", "bib": {
        "title": title, "pub_year": year, "citation": citation
    }}


def detail_page(title="A New Paper", date="2026/10/21", authors="Bowen Qin, Yi Xie", url="https://arxiv.org/abs/2610.12345"):
    return f"""<div id="gsc_oci_title"><a class="gsc_oci_title_link" href="{url}">{title}</a></div>
    <div class="gs_scl"><div class="gsc_oci_field">Authors</div><div class="gsc_oci_value">{authors}</div></div>
    <div class="gs_scl"><div class="gsc_oci_field">Publication date</div><div class="gsc_oci_value">{date}</div></div>
    <div class="gs_scl"><div class="gsc_oci_field">Journal</div><div class="gsc_oci_value">arXiv preprint arXiv:2610.12345</div></div>"""


def profile_page(identifier="one", more=False):
    return f"""<div id="gsc_prf_in">A Researcher</div><table><tr class="gsc_a_tr">
    <td><a class="gsc_a_at" href="/citations?citation_for_view={USER}:{identifier}">A Paper &amp; Its Results</a>
    <div class="gs_gray">Bowen Qin</div><div class="gs_gray">arXiv preprint arXiv:2610.12345, 2026</div></td>
    <td><a class="gsc_a_ac">1,234*</a></td><td class="gsc_a_y"><span class="gsc_a_h">2026</span></td>
    </tr></table><button id="gsc_bpf_more" {'disabled' if not more else ''}>More</button>"""


class ProfileFetchTests(unittest.TestCase):
    def setUp(self):
        self.session = Mock()
        self.session.get.return_value = Mock(text=profile_page())
        patcher = patch.object(sync.requests, "Session")
        constructor = patcher.start()
        constructor.return_value.__enter__.return_value = self.session
        self.addCleanup(patcher.stop)

    def test_profile_preserves_ids_titles_years_and_citation_counts(self):
        paper = sync.fetch_profile(USER)["publications"][0]
        self.assertEqual(paper["author_pub_id"], f"{USER}:one")
        self.assertEqual(paper["bib"]["title"], "A Paper & Its Results")
        self.assertEqual(paper["bib"]["pub_year"], "2026")
        self.assertEqual(paper["num_citations"], 1234)

    def test_all_pages_are_fetched_until_more_is_disabled(self):
        self.session.get.side_effect = [Mock(text=profile_page(more=True)), Mock(text=profile_page("two"))]
        papers = sync.fetch_profile(USER)["publications"]
        self.assertEqual(len(papers), 2)
        self.assertEqual(self.session.get.call_args_list[1].kwargs["params"]["cstart"], 1)

    def test_repeated_pagination_and_wrong_author_are_rejected(self):
        self.session.get.return_value = Mock(text=profile_page(more=True))
        with self.assertRaises(ValueError):
            sync.fetch_profile(USER)
        self.session.get.side_effect = None
        self.session.get.return_value = Mock(text=profile_page().replace(USER + ":one", "someone_else:one"))
        with self.assertRaises(ValueError):
            sync.fetch_profile(USER)

    def test_challenge_and_empty_profile_pages_fail(self):
        for page in ("<html>Verify you are human</html>", '<div id="gsc_prf_in">A Researcher</div>'):
            with self.subTest(page=page):
                self.session.get.return_value = Mock(text=page)
                with self.assertRaises(ValueError):
                    sync.fetch_profile(USER)

    def test_http_rejection_does_not_enter_an_unbounded_retry_loop(self):
        self.session.get.return_value.raise_for_status.side_effect = requests.HTTPError("403 Forbidden")
        with self.assertRaises(requests.HTTPError):
            sync.fetch_profile(USER)
        self.session.get.assert_called_once()


class PublicationImportTests(unittest.TestCase):
    def setUp(self):
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        self.curated = Path(directory.name) / "papers.bib"
        self.managed = Path(directory.name) / "scholar.bib"
        self.curated.write_text(CURATED)
        for name, value in (("CURATED_FILE", self.curated), ("MANAGED_FILE", self.managed)):
            patcher = patch.object(sync, name, value)
            patcher.start()
            self.addCleanup(patcher.stop)
        self.response = Mock(text=detail_page())
        patcher = patch.object(sync.requests, "get", return_value=self.response)
        self.get = patcher.start()
        self.addCleanup(patcher.stop)

    def test_import_has_full_authors_date_links_and_stable_id(self):
        candidate = sync.prepare_bibliography([publication()], USER)
        entry = sync.read_entries(candidate)[0]
        self.assertEqual(entry["ID"], "scholar_new")
        self.assertEqual(entry["author"], "Bowen Qin and Yi Xie")
        self.assertEqual((entry["year"], entry["month"], entry["day"]), ("2026", "oct", "21"))
        self.assertEqual(entry["pdf"], "https://arxiv.org/abs/2610.12345")
        self.assertEqual(entry["google_scholar_id"], "new")
        self.assertEqual(self.curated.read_text(), CURATED)
        self.assertFalse(self.managed.exists(), "Preparation must not write partial imports")

    def test_repeat_is_idempotent_and_uses_no_detail_requests(self):
        candidate = sync.prepare_bibliography([publication()], USER)
        self.managed.write_text(candidate)
        self.get.reset_mock()
        self.assertEqual(sync.prepare_bibliography([publication()], USER), candidate)
        self.get.assert_not_called()

    def test_id_title_and_arxiv_preprint_duplicates_are_not_imported(self):
        records = [
            publication("existing", "Renamed Title"),
            publication("alias", "A curated paper!"),
            publication("preprint", "Different preprint title", citation="arXiv preprint arXiv:2601.12345v2, 2026"),
        ]
        self.assertEqual(sync.read_entries(sync.prepare_bibliography(records, USER)), [])
        self.get.assert_not_called()

    def test_detailed_links_deduplicate_different_titles(self):
        # Conference/preprint records can have different titles and IDs.
        self.response.text = detail_page(url="https://arxiv.org/abs/2601.12345v3")
        self.assertEqual(sync.read_entries(sync.prepare_bibliography([publication()], USER)), [])

    def test_doi_identity_is_case_insensitive(self):
        a = sync.identities({"title": "First", "doi": "10.1234/ABC"})
        b = sync.identities({"title": "Second", "html": "https://doi.org/10.1234/abc"})
        self.assertTrue(a.intersection(b))

    def test_openreview_query_ids_distinguish_different_papers(self):
        first = sync.identities({"title": "First", "html": "https://openreview.net/forum?id=paper-one"})
        second = sync.identities({"title": "Second", "html": "https://openreview.net/forum?id=paper-two"})
        self.assertFalse(first.intersection(second))

    def test_shared_publisher_homepages_are_not_paper_identifiers(self):
        first = sync.identities({"title": "First", "html": "https://example.com/"})
        second = sync.identities({"title": "Second", "html": "https://example.com/"})
        self.assertFalse(first.intersection(second))

    def test_curated_override_wins_without_changing_custom_fields(self):
        candidate = sync.prepare_bibliography([publication()], USER)
        self.managed.write_text(candidate)
        self.curated.write_text(CURATED + candidate.replace("scholar_new", "custom_key"))
        self.assertEqual(sync.read_entries(sync.prepare_bibliography([publication()], USER)), [])
        self.assertIn("selected={true}", self.curated.read_text())
        self.assertIn("annotation={Keep my note}", self.curated.read_text())
        self.get.reset_mock()
        sync.prepare_bibliography([publication()], USER)
        self.get.assert_not_called()

    def test_absent_scholar_records_never_remove_imported_papers(self):
        candidate = sync.prepare_bibliography([publication()], USER)
        self.managed.write_text(candidate)
        self.assertEqual(sync.prepare_bibliography([], USER), candidate)

    def test_spurious_year_one_records_are_skipped(self):
        result = sync.prepare_bibliography([publication(year="1")], USER)
        self.assertEqual(sync.read_entries(result), [])
        self.get.assert_not_called()

    def test_year_and_month_precision_do_not_invent_dates(self):
        for date, expected in (("2026", (None, None)), ("2026/7", ("jul", None))):
            with self.subTest(date=date):
                self.response.text = detail_page(date=date)
                entry = sync.fetch_publication(publication(), USER)
                self.assertEqual((entry.get("month"), entry.get("day")), expected)

    def test_bad_dates_missing_authors_and_challenge_pages_fail(self):
        for page in (
            detail_page(date="2026/2/30"), detail_page(date="2026/13"),
            detail_page(authors=""), "<html>Please verify you are human</html>",
        ):
            with self.subTest(page=page):
                self.response.text = page
                with self.assertRaises(ValueError):
                    sync.prepare_bibliography([publication()], USER)
                self.assertFalse(self.managed.exists())
                self.assertEqual(self.curated.read_text(), CURATED)

    def test_rate_limit_propagates_instead_of_emitting_empty_data(self):
        self.response.raise_for_status.side_effect = requests.HTTPError("429 Too Many Requests")
        with self.assertRaises(requests.HTTPError):
            sync.prepare_bibliography([publication()], USER)
        self.assertFalse(self.managed.exists())

    def test_plain_metadata_cannot_inject_html_or_bibtex_entries(self):
        self.response.text = detail_page(
            title="A &lt;script&gt;alert('x')&lt;/script&gt; {test}",
            authors="Bowen Qin, Anne O'Neill",
            url="javascript:alert(1)",
        )
        entries = sync.read_entries(sync.prepare_bibliography([publication()], USER))
        self.assertEqual(len(entries), 1)
        self.assertNotIn("<script>", entries[0]["title"])
        self.assertNotIn("'", entries[0]["author"])
        self.assertTrue(entries[0]["html"].startswith("https://scholar.google.com/"))

    def test_malformed_or_duplicate_managed_data_cannot_be_overwritten(self):
        for content in ("@article{broken, title={unclosed}", CURATED + CURATED):
            with self.subTest(content=content):
                self.managed.write_text(content)
                with self.assertRaises(ValueError):
                    sync.prepare_bibliography([publication()], USER)
                self.assertEqual(self.managed.read_text(), content)


if __name__ == "__main__":
    unittest.main()
