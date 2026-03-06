"""
Compliance checker: compares parsed manuscript against journal profile
and returns structured warnings and passes — no AI required.

Checks:
  - Abstract word count
  - Required sections present
  - Section-level word count advisories
  - Keywords (required / not required / count limit)
  - Title case
  - References present + count
  - DOI in references
  - Page limit estimate
  - Font / spacing / margins reminder
  - Column layout reminder
"""

import re
from typing import Dict, List, Any


# ── helpers ───────────────────────────────────────────────────────────────────

def _margin_to_inches(margin_str) -> float:
    """Convert '1-inch', '1.25-inch', or a float to a float."""
    if isinstance(margin_str, (int, float)):
        return float(margin_str)
    try:
        return float(str(margin_str).replace("-inch", "").replace("inch", "").strip())
    except Exception:
        return 1.0


def _extract_sections(body: str) -> Dict[str, str]:
    """
    Parse Markdown body into {heading: content} dict.
    Handles ## and ### headings.
    """
    sections = {}
    current_heading = None
    current_lines = []

    for line in body.splitlines():
        h_match = re.match(r"^#{1,4}\s+(.*)", line)
        if h_match:
            if current_heading is not None:
                sections[current_heading.strip().lower()] = "\n".join(current_lines).strip()
            current_heading = h_match.group(1)
            current_lines = []
        else:
            if current_heading is not None:
                current_lines.append(line)

    if current_heading is not None:
        sections[current_heading.strip().lower()] = "\n".join(current_lines).strip()

    return sections


def _word_count(text: str) -> int:
    return len(text.split()) if text.strip() else 0


# ── section word limit advisories ─────────────────────────────────────────────

SECTION_WORD_ADVISORIES = {
    "introduction":          {"soft": 600,  "hard": 900},
    "abstract":              {"soft": 200,  "hard": 350},
    "methods":               {"soft": 800,  "hard": 1500},
    "methodology":           {"soft": 800,  "hard": 1500},
    "materials and methods": {"soft": 800,  "hard": 1500},
    "results":               {"soft": 800,  "hard": 1200},
    "discussion":            {"soft": 800,  "hard": 1200},
    "conclusion":            {"soft": 300,  "hard": 500},
    "conclusions":           {"soft": 300,  "hard": 500},
    "related work":          {"soft": 500,  "hard": 800},
    "literature review":     {"soft": 600,  "hard": 1000},
}


# ── main checker ──────────────────────────────────────────────────────────────

def check_compliance(manuscript: Dict[str, Any], journal_name: str) -> Dict[str, Any]:
    """
    Compare manuscript content against journal profile rules.

    Returns a structured compliance report with:
    - passes:   things already correct
    - warnings: things the user needs to fix manually
    - score:    percentage of checks passed
    """
    from core.journal_profiles import get_journal_profile

    profile = get_journal_profile(journal_name)
    if not profile:
        return {
            "error": f"Journal '{journal_name}' not found.",
            "passes": [],
            "warnings": [],
            "score": 0,
        }

    passes   = []
    warnings = []

    metadata        = manuscript.get("metadata", {}) or {}
    abstract        = manuscript.get("abstract", "") or ""
    body            = manuscript.get("body", "") or ""
    references      = manuscript.get("references", "") or ""
    journal_display = profile.get("name", journal_name)

    # Parse body into sections
    sections = _extract_sections(body)

    # ── 1. Abstract word count ────────────────────────────────────────────────
    max_abstract = profile.get("abstract_max_words")
    if max_abstract:
        abstract_words = _word_count(abstract)
        if abstract_words == 0:
            warnings.append({
                "check":    "Abstract",
                "severity": "high",
                "message":  f"No abstract found. {journal_display} requires an abstract of max {max_abstract} words.",
            })
        elif abstract_words <= max_abstract:
            passes.append({
                "check":   "Abstract Length",
                "message": f"Abstract is {abstract_words} words — within the {max_abstract} word limit ✓",
            })
        else:
            excess = abstract_words - max_abstract
            warnings.append({
                "check":    "Abstract Length",
                "severity": "high",
                "message": (
                    f"Abstract is {abstract_words} words — {journal_display} limit is {max_abstract} words. "
                    f"Please shorten by {excess} words."
                ),
            })

    # ── 2. Required sections ──────────────────────────────────────────────────
    required_structure = profile.get("structure", [])
    for section in required_structure:
        clean = re.sub(r"^[IVX]+\.\s*", "", section).strip().lower()
        found = any(
            clean in key or key in clean
            for key in sections.keys()
        ) or clean in body.lower()

        if found:
            passes.append({
                "check":   f"Section: {section}",
                "message": f"'{section}' section is present ✓",
            })
        else:
            warnings.append({
                "check":    f"Section: {section}",
                "severity": "medium",
                "message": (
                    f"Section '{section}' is missing or not named correctly. "
                    f"{journal_display} requires this section."
                ),
            })

    # ── 3. Section-level word count advisories ────────────────────────────────
    for sec_name, sec_content in sections.items():
        advisory = None
        for key in SECTION_WORD_ADVISORIES:
            if key in sec_name:
                advisory = SECTION_WORD_ADVISORIES[key]
                break

        if advisory and sec_content:
            wc = _word_count(sec_content)
            if wc > advisory["hard"]:
                warnings.append({
                    "check":    f"Word Count: {sec_name.title()}",
                    "severity": "medium",
                    "message": (
                        f"'{sec_name.title()}' section is {wc} words — "
                        f"recommended maximum is ~{advisory['hard']} words. "
                        f"Consider condensing by ~{wc - advisory['hard']} words."
                    ),
                })
            elif wc > advisory["soft"]:
                warnings.append({
                    "check":    f"Word Count: {sec_name.title()}",
                    "severity": "low",
                    "message": (
                        f"'{sec_name.title()}' section is {wc} words — "
                        f"getting long (soft limit ~{advisory['soft']} words). "
                        f"Review for conciseness."
                    ),
                })
            else:
                passes.append({
                    "check":   f"Word Count: {sec_name.title()}",
                    "message": f"'{sec_name.title()}' is {wc} words — looks good ✓",
                })

    # ── 4. Keywords ───────────────────────────────────────────────────────────
    requires_keywords = profile.get("keywords", False)
    max_keywords      = profile.get("max_keywords", 0)
    keywords          = metadata.get("keywords", [])

    if requires_keywords:
        if not keywords:
            warnings.append({
                "check":    "Keywords",
                "severity": "high",
                "message":  f"{journal_display} requires keywords — none found in your manuscript.",
            })
        elif max_keywords and len(keywords) > max_keywords:
            warnings.append({
                "check":    "Keywords",
                "severity": "medium",
                "message": (
                    f"You have {len(keywords)} keywords — "
                    f"{journal_display} allows max {max_keywords}. "
                    f"Please remove {len(keywords) - max_keywords}."
                ),
            })
        else:
            passes.append({
                "check":   "Keywords",
                "message": f"{len(keywords)} keywords found — meets requirement ✓",
            })

    # ── 5. Title case ─────────────────────────────────────────────────────────
    title      = metadata.get("title", "")
    title_case = profile.get("title_case", "Title Case")
    if title:
        if title_case == "UPPERCASE":
            if title == title.upper():
                passes.append({
                    "check":   "Title Case",
                    "message": f"Title is UPPERCASE — correct for {journal_display} ✓",
                })
            else:
                warnings.append({
                    "check":    "Title Case",
                    "severity": "medium",
                    "message": (
                        f"{journal_display} requires the title in UPPERCASE. "
                        f"Current title: '{title}'"
                    ),
                })
        else:
            passes.append({
                "check":   "Title Case",
                "message": f"Title format acceptable for {journal_display} ✓",
            })

    # ── 6. References present ─────────────────────────────────────────────────
    refs_text = references if isinstance(references, str) else "\n".join(
        str(r) for r in references
    )
    ref_lines = [l for l in refs_text.splitlines() if l.strip()]

    if ref_lines:
        passes.append({
            "check":   "References",
            "message": f"{len(ref_lines)} references found ✓",
        })
    else:
        warnings.append({
            "check":    "References",
            "severity": "high",
            "message":  "No references found in your manuscript.",
        })

    # ── 7. DOI in references ──────────────────────────────────────────────────
    doi_required = profile.get("doi_required", False)
    if doi_required and ref_lines:
        doi_count   = len(re.findall(r"10\.\d{4,}/\S+", refs_text))
        missing_doi = len(ref_lines) - doi_count
        if missing_doi == 0:
            passes.append({
                "check":   "DOI in References",
                "message": "All references appear to have DOIs ✓",
            })
        else:
            warnings.append({
                "check":    "DOI in References",
                "severity": "medium",
                "message": (
                    f"{missing_doi} reference(s) may be missing a DOI. "
                    f"{journal_display} requires DOIs in references."
                ),
            })

    # ── 8. Page limit estimate ────────────────────────────────────────────────
    page_limit = profile.get("page_limit")
    if page_limit:
        total_words     = _word_count(body) + _word_count(abstract)
        estimated_pages = round(total_words / 500)
        if estimated_pages <= page_limit:
            passes.append({
                "check":   "Page Limit",
                "message": (
                    f"Estimated ~{estimated_pages} pages — "
                    f"within the {page_limit} page limit for {journal_display} ✓"
                ),
            })
        else:
            warnings.append({
                "check":    "Page Limit",
                "severity": "high",
                "message": (
                    f"Estimated ~{estimated_pages} pages based on word count — "
                    f"{journal_display} limit is {page_limit} pages. "
                    f"Consider condensing your content."
                ),
            })

    # ── 9. Formatting reminder ────────────────────────────────────────────────
    font         = profile.get("font", "Times New Roman")
    font_size    = profile.get("font_size", 12)
    line_spacing = profile.get("line_spacing", 1.5)
    margin_val   = _margin_to_inches(profile.get("margins", "1-inch"))
    columns      = profile.get("columns", 1)
    col_text     = "2-column" if columns == 2 else "single column"

    warnings.append({
        "check":    "Formatting (Applied Automatically)",
        "severity": "info",
        "message": (
            f"DOCX styled with: {font} {font_size}pt, "
            f"{line_spacing}x line spacing, {margin_val}\" margins, "
            f"{col_text} layout. Verify against the journal's submission template."
        ),
    })

    # ── 10. Heading style reminder ────────────────────────────────────────────
    heading_styles = profile.get("heading_styles", {})
    if heading_styles:
        h1 = heading_styles.get(1, {})
        h1_desc = []
        if h1.get("caps"):
            h1_desc.append("ALL CAPS")
        if h1.get("bold"):
            h1_desc.append("Bold")
        if h1.get("italic"):
            h1_desc.append("Italic")
        if h1_desc:
            warnings.append({
                "check":    "Heading Style",
                "severity": "info",
                "message": (
                    f"{journal_display} level-1 headings: "
                    f"{', '.join(h1_desc)} at {h1.get('size', font_size)}pt — "
                    f"applied in the downloaded DOCX."
                ),
            })

    # ── Score (exclude info-level reminders) ──────────────────────────────────
    scored_warnings = [w for w in warnings if w.get("severity") not in ("info",)]
    total = len(passes) + len(scored_warnings)
    score = round((len(passes) / total) * 100) if total > 0 else 100

    return {
        "journal":       journal_display,
        "passes":        passes,
        "warnings":      warnings,
        "total_checks":  total,
        "passed_checks": len(passes),
        "score":         score,
    }