"""Basic regression checks for static UI controls in docs/index.html."""
from pathlib import Path
import unittest


REPO_ROOT = Path(__file__).resolve().parents[1]
INDEX_HTML = REPO_ROOT / "docs" / "index.html"


class TestDocsUiFeatures(unittest.TestCase):
    def setUp(self) -> None:
        self.html = INDEX_HTML.read_text(encoding="utf-8")

    def test_sort_controls_present(self) -> None:
        self.assertIn('id="sort-column"', self.html)
        self.assertIn('id="sort-direction"', self.html)
        self.assertIn('data-sort-key="symbol"', self.html)
        self.assertIn('data-sort-key="action_signal"', self.html)

    def test_export_controls_present(self) -> None:
        self.assertIn('id="export-csv"', self.html)
        self.assertIn('id="export-xlsx"', self.html)

    def test_export_and_sort_logic_present(self) -> None:
        self.assertIn("function getDisplayedRows()", self.html)
        self.assertIn("function exportCsv()", self.html)
        self.assertIn("function exportXlsx()", self.html)
        self.assertIn("function makeXlsxBytes(aoa)", self.html)


if __name__ == "__main__":
    unittest.main()
