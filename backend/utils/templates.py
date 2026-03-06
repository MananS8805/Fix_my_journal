"""
Template path resolver.
If neither a journal-specific nor the default template exists on disk,
auto-generates a minimal default.docx so Pandoc (or the fallback) always
has something to work with.
"""

from pathlib import Path
from typing import Optional


REPO_ROOT    = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"


def get_template_path(journal_name: str) -> Path:
    """
    Return the path to the best available .docx template for *journal_name*.

    Priority:
    1. templates/{journal_name}.docx   (e.g. templates/nature.docx)
    2. templates/default.docx          (auto-created if missing)
    """
    TEMPLATES_DIR.mkdir(parents=True, exist_ok=True)

    # 1. Journal-specific template
    journal_tpl = TEMPLATES_DIR / f"{journal_name.lower()}.docx"
    if journal_tpl.exists():
        return journal_tpl

    # 2. Generic default — create it on the fly if needed
    default_tpl = TEMPLATES_DIR / "default.docx"
    if not default_tpl.exists():
        _create_default_template(default_tpl)

    return default_tpl


# ─────────────────────────────────────────────────────────────────────────────
# Auto-generator
# ─────────────────────────────────────────────────────────────────────────────

def _create_default_template(path: Path) -> None:
    """
    Build a minimal Word document that Pandoc can use as a --reference-doc.

    Sets:
    - Times New Roman 12 pt body
    - 1-inch margins all round
    - Heading 1-4 styles defined
    """
    try:
        from docx import Document
        from docx.shared import Pt, Inches
        from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
    except ImportError:
        # python-docx not available; leave no file → fallback renderer will be used
        print("[templates] python-docx not installed; skipping default template creation.")
        return

    doc = Document()

    # ── Page layout ───────────────────────────────────────────────────────
    sec = doc.sections[0]
    for attr in ("top_margin", "bottom_margin", "left_margin", "right_margin"):
        setattr(sec, attr, Inches(1.0))

    # ── Normal (body) style ───────────────────────────────────────────────
    normal = doc.styles["Normal"]
    normal.font.name = "Times New Roman"
    normal.font.size = Pt(12)
    normal.paragraph_format.line_spacing = Pt(24)   # ~double-spaced at 12pt
    normal.paragraph_format.space_after  = Pt(0)

    # ── Heading styles ────────────────────────────────────────────────────
    heading_sizes = {1: 16, 2: 14, 3: 12, 4: 12}
    for level, size in heading_sizes.items():
        style_name = f"Heading {level}"
        try:
            h = doc.styles[style_name]
        except KeyError:
            h = doc.styles.add_style(style_name, 1)   # 1 = paragraph style
        h.font.name = "Times New Roman"
        h.font.size = Pt(size)
        h.font.bold = True
        if level == 1:
            h.paragraph_format.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

    # ── Placeholder paragraph (Pandoc needs at least one) ─────────────────
    doc.add_paragraph("")

    doc.save(str(path))
    print(f"[templates] Created default template at {path}")