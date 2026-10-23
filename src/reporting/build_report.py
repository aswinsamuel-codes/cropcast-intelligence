"""
Render the final report from Markdown source to .docx (and optionally PDF via Microsoft Word).

Supported Markdown subset: `#`/`##`/`###` headings, paragraphs, `-` and `1.` lists, pipe tables,
images `![Figure N. caption](path)`, table captions as a paragraph starting with `Table N.`,
**bold**, *italic*, `code`, and a `<!-- pagebreak -->` marker.

Formatting: Times New Roman 12 pt body, 1.5 line spacing, 1-inch margins, page numbers in the footer.

Usage:
    python -m src.reporting.build_report reports/final_report.md --pdf
"""

from __future__ import annotations

import argparse
import re
import subprocess
from pathlib import Path
from typing import List

from docx import Document
from docx.enum.section import WD_SECTION
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Inches, Pt

from src.config import REPO_ROOT

FONT = "Times New Roman"
FIGURE_WIDTH_IN = 5.2
TABLE_WIDTH_IN = 6.5  # page width (8.5 in) minus two 1-inch margins
CHAR_IN = 0.072       # approximate width of one Times New Roman character at 9.5 pt
CELL_PAD_IN = 0.16    # left + right cell margins
# Back matter (references, appendices) is single-spaced at 11 pt; the body keeps 12 pt at 1.5 spacing
BACK_MATTER_PREFIXES = ("References", "Appendix")
INLINE = re.compile(r"(\*\*[^*]+\*\*|\*[^*]+\*|`[^`]+`)")


def _set_font(run, size: float | None = None, bold=None, italic=None) -> None:
    run.font.name = FONT
    run._element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold
    if italic is not None:
        run.italic = italic


def add_inline(par, text: str, size: float | None = None, base_bold=False, base_italic=False) -> None:
    for part in INLINE.split(text):
        if not part:
            continue
        if part.startswith("**") and part.endswith("**"):
            _set_font(par.add_run(part[2:-2]), size, bold=True, italic=base_italic)
        elif part.startswith("*") and part.endswith("*") and len(part) > 2:
            _set_font(par.add_run(part[1:-1]), size, bold=base_bold, italic=True)
        elif part.startswith("`") and part.endswith("`"):
            r = par.add_run(part[1:-1])
            _set_font(r, size, bold=base_bold, italic=base_italic)
            r.font.name = "Consolas"
        else:
            _set_font(par.add_run(part), size, bold=base_bold, italic=base_italic)


def _page_number_footer(section) -> None:
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    run = p.add_run()
    for tag, text in (("begin", None), (None, "PAGE"), ("end", None)):
        if tag:
            el = OxmlElement("w:fldChar")
            el.set(qn("w:fldCharType"), tag)
        else:
            el = OxmlElement("w:instrText")
            el.set(qn("xml:space"), "preserve")
            el.text = text
        run._r.append(el)
    _set_font(run, 11)


def _style_document(doc: Document) -> None:
    normal = doc.styles["Normal"]
    normal.font.name = FONT
    normal.element.rPr.rFonts.set(qn("w:eastAsia"), FONT)
    normal.font.size = Pt(12)
    pf = normal.paragraph_format
    pf.line_spacing_rule = WD_LINE_SPACING.ONE_POINT_FIVE
    pf.space_after = Pt(6)
    for lvl, size in ((1, 14), (2, 13), (3, 12)):
        st = doc.styles[f"Heading {lvl}"]
        st.font.name = FONT
        rfonts = st.element.rPr.rFonts
        # Heading styles default to theme fonts (Calibri Light), which override the font name
        for attr in ("w:asciiTheme", "w:hAnsiTheme", "w:eastAsiaTheme", "w:cstheme"):
            if rfonts.get(qn(attr)) is not None:
                del rfonts.attrib[qn(attr)]
        rfonts.set(qn("w:eastAsia"), FONT)
        rfonts.set(qn("w:cs"), FONT)
        st.font.size = Pt(size)
        st.font.bold = True
        st.font.color.rgb = None
        st.paragraph_format.space_before = Pt(12 if lvl == 1 else 8)
        st.paragraph_format.space_after = Pt(4)
        st.paragraph_format.keep_with_next = True
    for s in doc.sections:
        s.top_margin = s.bottom_margin = s.left_margin = s.right_margin = Inches(1)
        _page_number_footer(s)


def _table(doc: Document, rows: List[List[str]]) -> None:
    header, body = rows[0], [r for r in rows[1:] if not re.fullmatch(r"[\s:|-]+", "|".join(r))]
    t = doc.add_table(rows=1 + len(body), cols=len(header))
    t.style = "Table Grid"
    t.alignment = WD_TABLE_ALIGNMENT.CENTER
    # Size columns by content (equal widths break words in narrow columns). Each column first gets an
    # absolute minimum that fits its longest unbreakable word at 9.5 pt (bold headers ~15% wider, plus
    # cell padding); the remaining width is shared in proportion to typical cell length.
    rows_all = [header] + body
    mins, hard, typical = [], [], []
    numeric = re.compile(r"^[<>≤≥+\-−–]?[\d.,]+(%|e[-+]?\d+)?$")
    for j in range(len(header)):
        cells = [r[j].strip().replace("`", "").replace("**", "") for r in rows_all[1:] if j < len(r)] or [""]
        tokens = [w for c in cells for w in c.split()]
        body_word = max((len(w) for w in tokens), default=1)
        head_word = max((len(w) for w in header[j].strip().replace("**", "").split()), default=1)
        mins.append(max(body_word * CHAR_IN, head_word * CHAR_IN * 1.15) + CELL_PAD_IN)
        # Numbers must never split; text can wrap between (or, if it must, within) words
        num_word = max((len(w) for w in tokens if numeric.match(w)), default=0)
        # Short header words (e.g. "MAPE") must not split either; bold capitals are about 1.4x wider
        short_head = max((len(w) for w in header[j].strip().replace("**", "").split() if len(w) <= 6), default=0)
        hard.append(max(num_word * CHAR_IN, short_head * CHAR_IN * 1.4, 2 * CHAR_IN) + CELL_PAD_IN)
        typical.append(max(sorted(len(c) for c in cells)[len(cells) // 2], 1))
    spare = TABLE_WIDTH_IN - sum(mins)
    if spare >= 0:
        widths = [m + spare * tw / sum(typical) for m, tw in zip(mins, typical)]
    else:
        # Not every word fits: give each column its hard (numeric) minimum, then share the remaining
        # width in proportion to how much more each column wanted
        give = TABLE_WIDTH_IN - sum(hard)
        want = [max(m - h, 0) for m, h in zip(mins, hard)]
        widths = [h + give * w / sum(want) if sum(want) else h for h, w in zip(hard, want)]
    t.autofit = False
    # A fixed-layout table is sized by its grid (w:gridCol), not by cell widths, so set both
    for g, w in zip(t._tbl.tblGrid.findall(qn("w:gridCol")), widths):
        g.set(qn("w:w"), str(int(round(w * 1440))))
    for j, w in enumerate(widths):
        for cell in t.columns[j].cells:
            cell.width = Inches(w)
    # Keep rows intact across pages and repeat the header row on continuation pages
    for r_i, row in enumerate(t.rows):
        tr_pr = row._tr.get_or_add_trPr()
        tr_pr.append(OxmlElement("w:cantSplit"))
        if r_i == 0:
            tr_pr.append(OxmlElement("w:tblHeader"))
    for i, row in enumerate([header] + body):
        for j, cell in enumerate(row):
            c = t.cell(i, j)
            c.text = ""
            p = c.paragraphs[0]
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            p.paragraph_format.space_after = Pt(0)
            # Keep each row with the next so a short table is not split from its header
            p.paragraph_format.keep_with_next = i < len(body)
            add_inline(p, cell.strip(), size=9.5, base_bold=(i == 0))
    doc.add_paragraph().paragraph_format.space_after = Pt(2)


def render(md_path: Path, out_path: Path) -> Path:
    lines = md_path.read_text(encoding="utf-8").splitlines()
    doc = Document()
    _style_document(doc)
    base = md_path.parent
    i = 0
    title_done = False
    back_matter = False

    def compact(p) -> None:
        if back_matter:
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            p.paragraph_format.space_after = Pt(3)

    while i < len(lines):
        line = lines[i].rstrip()
        if not line.strip():
            i += 1
            continue
        if line.strip().startswith("```"):
            i += 1
            while i < len(lines) and not lines[i].strip().startswith("```"):
                p = doc.add_paragraph()
                p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
                p.paragraph_format.space_after = Pt(0)
                r = p.add_run(lines[i].rstrip())
                _set_font(r, 10)
                r.font.name = "Consolas"
                i += 1
            i += 1  # closing fence
            continue
        if line.strip() == "<!-- pagebreak -->":
            doc.add_page_break()
            i += 1
            continue
        if line.startswith("<!--"):
            while "-->" not in lines[i]:
                i += 1
            i += 1
            continue
        m = re.match(r"^(#{1,3})\s+(.*)", line)
        if m:
            level, text = len(m.group(1)), m.group(2)
            if level == 1 and not title_done:
                p = doc.add_paragraph()
                p.alignment = WD_ALIGN_PARAGRAPH.CENTER
                add_inline(p, text, size=16, base_bold=True)
                title_done = True
            else:
                back_matter = back_matter or text.startswith(BACK_MATTER_PREFIXES)
                h = doc.add_heading(level=max(1, level - 1))
                add_inline(h, text, size={1: 14, 2: 13, 3: 12}[max(1, level - 1)], base_bold=True)
            i += 1
            continue
        if line.startswith("|"):
            rows = []
            while i < len(lines) and lines[i].startswith("|"):
                rows.append([c for c in lines[i].strip().strip("|").split("|")])
                i += 1
            _table(doc, rows)
            continue
        m = re.match(r"^!\[(.*?)\]\((.*?)\)", line)
        if m:
            caption, src = m.group(1), m.group(2)
            p = doc.add_paragraph()
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.add_run().add_picture(str((base / src).resolve()), width=Inches(FIGURE_WIDTH_IN))
            c = doc.add_paragraph()
            c.alignment = WD_ALIGN_PARAGRAPH.CENTER
            c.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            add_inline(c, caption, size=10, base_italic=False)
            i += 1
            continue
        m = re.match(r"^(\s*)([-*]|\d+\.)\s+(.*)", line)
        if m:
            nested = len(m.group(1)) >= 2
            if m.group(2)[0].isdigit():
                # Word's "List Number" style shares one counter across the document, so every list
                # would continue the previous one's numbering. Render the Markdown number with a
                # hanging indent instead, so each list restarts where the source does.
                p = doc.add_paragraph()
                indent = 0.5 if nested else 0.25
                p.paragraph_format.left_indent = Inches(indent + 0.25)
                p.paragraph_format.first_line_indent = Inches(-0.25)
                p.paragraph_format.space_after = Pt(2)
                add_inline(p, f"{m.group(2)}\t{m.group(3)}", size=11 if back_matter else None)
                p.paragraph_format.tab_stops.add_tab_stop(Inches(indent + 0.25))
            else:
                p = doc.add_paragraph(style="List Bullet 2" if nested else "List Bullet")
                p.paragraph_format.space_after = Pt(2)
                add_inline(p, m.group(3), size=11 if back_matter else None)
            compact(p)
            i += 1
            continue
        # Paragraph: merge consecutive non-special lines
        buf = [line.strip()]
        i += 1
        while i < len(lines) and lines[i].strip() and not re.match(r"^(#|\||!\[|\s*([-*]|\d+\.)\s|<!--|```)", lines[i]):
            buf.append(lines[i].strip())
            i += 1
        text = " ".join(buf)
        p = doc.add_paragraph()
        if re.match(r"^\*\*Table \d+\.", text) or re.match(r"^Table \d+\.", text):
            p.alignment = WD_ALIGN_PARAGRAPH.CENTER
            p.paragraph_format.keep_with_next = True
            p.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
            add_inline(p, text, size=10)
        else:
            p.alignment = WD_ALIGN_PARAGRAPH.JUSTIFY
            add_inline(p, text, size=11 if back_matter else None)
            compact(p)
    doc.save(out_path)
    return out_path


def to_pdf(docx_path: Path) -> Path:
    """Export with Microsoft Word through COM (Windows); returns the PDF path."""
    pdf = docx_path.with_suffix(".pdf")
    script = (f"$w = New-Object -ComObject Word.Application; $w.Visible = $false; "
              f"$d = $w.Documents.Open('{docx_path}'); $d.Fields.Update() | Out-Null; "
              f"$d.SaveAs([ref]'{pdf}', [ref]17); $d.Close(); $w.Quit()")
    subprocess.run(["powershell", "-NoProfile", "-Command", script], check=True)
    return pdf


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("markdown", type=str)
    parser.add_argument("--pdf", action="store_true")
    args = parser.parse_args()
    md = (REPO_ROOT / args.markdown).resolve()
    out = render(md, md.with_suffix(".docx"))
    print("Wrote", out)
    if args.pdf:
        print("Wrote", to_pdf(out))


if __name__ == "__main__":
    main()
