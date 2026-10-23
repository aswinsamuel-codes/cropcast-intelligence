"""
Tests for the report renderer (`src.reporting.build_report`): formatting requirements.
"""

import tempfile
import unittest
from pathlib import Path

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from docx import Document  # noqa: E402
from docx.enum.text import WD_LINE_SPACING  # noqa: E402
from docx.shared import Inches, Pt  # noqa: E402

from src.reporting.build_report import render  # noqa: E402


class TestRender(unittest.TestCase):
    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        fig, ax = plt.subplots(figsize=(2, 1))
        ax.plot([0, 1], [0, 1])
        fig.savefig(self.dir / "f.png")
        plt.close(fig)
        (self.dir / "r.md").write_text(
            "# A Title\n\n## 1. Introduction\n\nBody with **bold** and *italic* text.\n\n"
            "- point one\n- point two\n\n**Table 1.** Caption.\n\n| A | B |\n|---|---|\n| 1 | 2 |\n\n"
            "![Figure 1. A figure.](f.png)\n\n<!-- pagebreak -->\n\n## References\n\nRef.\n",
            encoding="utf-8")
        self.doc = Document(str(render(self.dir / "r.md", self.dir / "r.docx")))

    def test_body_formatting(self):
        normal = self.doc.styles["Normal"]
        self.assertEqual(normal.font.name, "Times New Roman")
        self.assertEqual(normal.font.size, Pt(12))
        self.assertEqual(normal.paragraph_format.line_spacing_rule, WD_LINE_SPACING.ONE_POINT_FIVE)

    def test_margins_and_page_numbers(self):
        s = self.doc.sections[0]
        for m in (s.top_margin, s.bottom_margin, s.left_margin, s.right_margin):
            self.assertEqual(m, Inches(1))
        self.assertIn("PAGE", s.footer.paragraphs[0]._p.xml)

    def test_content_elements(self):
        texts = [p.text for p in self.doc.paragraphs]
        self.assertEqual(texts[0], "A Title")
        self.assertIn("1. Introduction", texts)
        self.assertEqual(len(self.doc.tables), 1)
        self.assertEqual(self.doc.tables[0].cell(1, 1).text, "2")
        self.assertEqual(len(self.doc.inline_shapes), 1)
        self.assertIn("Figure 1. A figure.", texts)
        runs = [r for p in self.doc.paragraphs for r in p.runs if r.text == "bold"]
        self.assertTrue(runs and runs[0].bold)


class TestRendererRegressions(unittest.TestCase):
    """Bugs found while inspecting the rendered report; each test fails on the earlier renderer."""

    def setUp(self):
        self.dir = Path(tempfile.mkdtemp())
        (self.dir / "r.md").write_text(
            "# T\n\n## 1. A\n\n1. first\n2. second\n\nText.\n\n1. again\n\n- outer\n  - inner\n\n"
            "```\npython -m src.verify\n```\n\n"
            "| Label | A long descriptive column with many words | MAPE % | F1 |\n|---|---|---|---|\n"
            "| x | some fairly long text that can wrap between words easily | 4.01 | 0.025 |\n",
            encoding="utf-8")
        self.doc = Document(str(render(self.dir / "r.md", self.dir / "r.docx")))
        self.texts = [p.text for p in self.doc.paragraphs]

    def test_numbered_lists_restart(self):
        self.assertIn("1.\tfirst", self.texts)
        self.assertIn("1.\tagain", self.texts)

    def test_nested_bullet_uses_level_two_style(self):
        inner = [p for p in self.doc.paragraphs if p.text == "inner"][0]
        self.assertEqual(inner.style.name, "List Bullet 2")

    def test_code_fence_rendered_as_code_not_text(self):
        self.assertNotIn("```", "\n".join(self.texts))
        code = [p for p in self.doc.paragraphs if p.text == "python -m src.verify"][0]
        self.assertEqual(code.runs[0].font.name, "Consolas")

    def test_table_grid_widths_are_set_and_numbers_fit(self):
        from docx.oxml.ns import qn
        from src.reporting.build_report import CELL_PAD_IN, CHAR_IN
        t = self.doc.tables[0]
        grid = [int(g.get(qn("w:w"))) / 1440 for g in t._tbl.tblGrid.findall(qn("w:gridCol"))]
        self.assertGreater(max(grid) - min(grid), 0.5)            # not the equal default
        self.assertAlmostEqual(sum(grid), 6.5, places=2)          # fills the text width
        self.assertGreaterEqual(grid[3], 5 * CHAR_IN + CELL_PAD_IN - 1e-3)  # "0.025" fits
        self.assertGreaterEqual(grid[2], 4 * CHAR_IN * 1.4 + CELL_PAD_IN - 1e-3)  # "MAPE" header fits

    def test_heading_style_has_no_theme_font(self):
        from docx.oxml.ns import qn
        rfonts = self.doc.styles["Heading 1"].element.rPr.rFonts
        self.assertIsNone(rfonts.get(qn("w:asciiTheme")))
        self.assertEqual(rfonts.get(qn("w:ascii")), "Times New Roman")


class TestReportTables(unittest.TestCase):
    """Result tables are generated from saved artifacts; empty placeholders and NaN must be handled."""

    def setUp(self):
        import pandas as pd
        self.tables = Path(tempfile.mkdtemp())
        pd.DataFrame([
            {"series_id": "potato_uttar_pradesh", "method": "robust", "evaluated_days": 10, "label_base_rate": 0.5,
             "tp": 0, "fp": 0, "fn": 5, "precision": float("nan"), "recall": 0.0, "f1": 0.0,
             "null_precision_median": float("nan"), "randomisation_p_precision": float("nan")},
        ]).to_csv(self.tables / "anomaly_weak_label_agreement.csv", index=False)

    def test_empty_placeholder_is_filled_and_nan_shown_as_dash(self):
        from src.reporting.report_tables import refresh
        text = "a\n<!-- BEGIN TABLE:anomaly_weak -->\n<!-- END TABLE:anomaly_weak -->\nb\n"
        out = refresh(text, self.tables)
        row = [l for l in out.splitlines() if l.startswith("| Potato")][0]
        cells = [c.strip() for c in row.strip("|").split("|")]
        self.assertEqual(cells[4], "—")       # precision undefined, not 0
        self.assertEqual(cells[5], "0.000")   # recall genuinely zero
        self.assertEqual(refresh(out, self.tables), out)  # idempotent

    def test_zero_detection_rows_are_shown(self):
        import pandas as pd
        from src.reporting.report_tables import table_anomaly_classes
        pd.DataFrame([{"series_id": sid, "method": m, "Sunday/Monday (composition-prone)": 1, "other": 1}
                      for sid in ("onion_maharashtra", "potato_uttar_pradesh") for m in ("residual", "robust", "composite")
                      if not (sid == "potato_uttar_pradesh" and m == "robust")]
                     ).to_csv(self.tables / "anomaly_event_classes.csv", index=False)
        pd.DataFrame([{"series_id": sid, "method": m, "threshold": 3.0, "scored_days": 100,
                       "detections": 0 if (sid == "potato_uttar_pradesh" and m == "robust") else 2,
                       "rate_pct": 0.0 if (sid == "potato_uttar_pradesh" and m == "robust") else 2.0}
                      for sid in ("onion_maharashtra", "potato_uttar_pradesh") for m in ("residual", "robust", "composite")]
                     ).to_csv(self.tables / "anomaly_threshold_sensitivity.csv", index=False)
        out = table_anomaly_classes(self.tables)
        self.assertIn("| Potato | Robust | 100 | 0 (0.00%) | 0 | 0 |", out)
        self.assertEqual(len([l for l in out.splitlines() if l.startswith(("| Onion", "| Potato"))]), 6)

    def test_check_fails_without_markers(self):
        import subprocess
        import sys
        from src.config import REPO_ROOT
        doc = Path(tempfile.mkdtemp()) / "no_tables.md"
        doc.write_text("# nothing here\n", encoding="utf-8")
        rel = doc.resolve()
        p = subprocess.run([sys.executable, "-m", "src.reporting.report_tables", "--check", "--report", str(rel)],
                           cwd=REPO_ROOT, capture_output=True, text=True)
        self.assertEqual(p.returncode, 1, p.stdout + p.stderr)


if __name__ == "__main__":
    unittest.main()
