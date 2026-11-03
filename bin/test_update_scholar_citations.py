"""Offline regression tests: python -m unittest discover -s bin -p 'test_update_scholar_citations.py'."""

import importlib.util
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

import yaml


class CitationUpdateTests(unittest.TestCase):
    def setUp(self):
        self.client = Mock()
        spec = importlib.util.spec_from_file_location(
            "citations", Path(__file__).with_name("update_scholar_citations.py")
        )
        self.sync = importlib.util.module_from_spec(spec)
        with patch.dict("sys.modules", {"scholarly": Mock(scholarly=self.client)}):
            spec.loader.exec_module(self.sync)
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.output = Path(self.directory.name) / "citations.yml"
        self.sync.OUTPUT_FILE = str(self.output)
        self.paper_id = f"{self.sync.SCHOLAR_USER_ID}:paper"
        self.client.fill.return_value = {
            "publications": [
                {
                    "author_pub_id": self.paper_id,
                    "bib": {"title": "A paper", "pub_year": "2026"},
                    "num_citations": 3,
                }
            ]
        }

    def test_first_run_creates_citation_file(self):
        self.sync.get_scholar_citations()
        data = yaml.safe_load(self.output.read_text())
        self.assertEqual(data["papers"][self.paper_id]["citations"], 3)

    def test_unchanged_counts_still_record_successful_check(self):
        self.output.write_text(
            yaml.safe_dump(
                {
                    "metadata": {"last_updated": "2020-01-01"},
                    "papers": {
                        self.paper_id: {"title": "A paper", "year": "2026", "citations": 3}
                    },
                }
            )
        )
        self.sync.get_scholar_citations()
        data = yaml.safe_load(self.output.read_text())
        self.assertEqual(
            data["metadata"]["last_updated"], self.sync.datetime.now().strftime("%Y-%m-%d")
        )

    def test_successful_check_today_skips_network(self):
        self.output.write_text(
            yaml.safe_dump(
                {"metadata": {"last_updated": self.sync.datetime.now().strftime("%Y-%m-%d")}}
            )
        )
        self.sync.get_scholar_citations()
        self.client.search_author_id.assert_not_called()

    def test_empty_or_failed_fetch_preserves_existing_data(self):
        original = "metadata:\n  last_updated: '2020-01-01'\npapers: {}\n"
        for result in ({"publications": []}, {"publications": [{"bib": {"title": "No ID"}}]}):
            with self.subTest(result=result):
                self.output.write_text(original)
                self.client.fill.return_value = result
                with self.assertRaises(SystemExit):
                    self.sync.get_scholar_citations()
                self.assertEqual(self.output.read_text(), original)
        self.client.fill.side_effect = RuntimeError("Scholar unavailable")
        with self.assertRaises(SystemExit):
            self.sync.get_scholar_citations()
        self.assertEqual(self.output.read_text(), original)


if __name__ == "__main__":
    unittest.main()
