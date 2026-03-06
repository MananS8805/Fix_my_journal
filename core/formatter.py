"""
Manuscript formatter engine - applies journal-specific formatting rules.
"""

import re
from typing import Dict, List
from .journal_profiles import get_journal_profile
from .changelog import ChangeLog


class ManuscriptFormatter:
    """Applies journal-specific formatting transformations to manuscripts."""

    def __init__(self, journal_name: str):
        self.journal_profile = get_journal_profile(journal_name)
        self.journal_name = journal_name.upper()
        self.changelog = ChangeLog()

        if not self.journal_profile:
            raise ValueError(f"Unknown journal: {journal_name}")

    def format_manuscript(self, manuscript: Dict) -> Dict:
        formatted = {
            "metadata":   self._format_metadata(manuscript.get("metadata", {})),
            "abstract":   self._format_abstract(manuscript.get("abstract", "")),
            "body":       self._format_body(manuscript.get("body", "")),
            "references": self._format_references(manuscript.get("references", [])),
            "changelog":  self.changelog.to_dict(),
            "journal":    self.journal_name,   
            "tables":     manuscript.get("tables", []),
            "sections": self._reorder_sections(manuscript.get("sections", [])),
            
        }
        return formatted
    
    def _reorder_sections(self, sections: list) -> list:
        """Reorder rich sections list to match journal required structure."""
        required = self.journal_profile.get("structure", [])
        if not required or not sections:
            return sections

        reordered = []
        used = set()

        for req in required:
            for i, sec in enumerate(sections):
                if i not in used and req.lower() in sec.get("heading", "").lower():
                    reordered.append(sec)
                    used.add(i)
                    break

        # Append unmatched sections at the end
        for i, sec in enumerate(sections):
            if i not in used:
                reordered.append(sec)

        return reordered

    # ── METADATA ──────────────────────────────────────────────────────────────

    def _format_metadata(self, metadata: Dict) -> Dict:
        title_case     = self.journal_profile.get("title_case", "Title Case")
        original_title = metadata.get("title", "")
        formatted_title = original_title

        if title_case == "UPPERCASE":
            formatted_title = original_title.upper()
            self.changelog.add_change(
                "metadata_title_case",
                original_title,
                formatted_title,
                f"{self.journal_name} requires uppercase titles",
            )
        elif title_case == "Title Case":
            formatted_title = self._to_title_case(original_title)
            if formatted_title != original_title:
                self.changelog.add_change(
                    "metadata_title_case",
                    original_title,
                    formatted_title,
                    f"{self.journal_name} requires title case",
                )

        return {**metadata, "title": formatted_title, "journal": self.journal_name}

    # ── ABSTRACT ──────────────────────────────────────────────────────────────

    def _format_abstract(self, abstract: str) -> str:
        max_words = self.journal_profile.get("abstract_max_words", 150)
        words = abstract.split()

        if len(words) > max_words:
            original_len = len(words)
            abstract = " ".join(words[:max_words])
            self.changelog.add_change(
                "abstract_length",
                f"{original_len} words",
                f"{max_words} words",
                f"{self.journal_name} abstract limit exceeded",
            )
        return abstract

    # ── BODY ──────────────────────────────────────────────────────────────────

    def _format_body(self, body: str) -> str:
        required_structure = self.journal_profile.get("structure", [])
        sections           = self._extract_sections(body)
        formatted_body     = ""
        used_sections      = set()

        for required_section in required_structure:
            for section_name, content in sections.items():
                if section_name.lower() in required_section.lower():
                    formatted_body += f"\n## {required_section}\n{content}\n"
                    used_sections.add(section_name)
                    if section_name != required_section:
                        self.changelog.add_change(
                            "section_order",
                            section_name,
                            required_section,
                            f"Reordered to match {self.journal_name} structure",
                        )
                    break

        # Append unmatched sections
        for section_name, content in sections.items():
            if section_name not in used_sections:
                formatted_body += f"\n## {section_name}\n{content}\n"

        return formatted_body.strip()

    # ── REFERENCES ────────────────────────────────────────────────────────────

    def _format_references(self, references) -> str:
        reference_style = self.journal_profile.get("reference_style", "alphabetical")

        if isinstance(references, list):
            references_text = "\n".join(references)
        else:
            references_text = references

        original_style = self._detect_reference_style(references_text)

        if original_style != reference_style:
            self.changelog.add_change(
                "reference_style",
                original_style,
                reference_style,
                f"{self.journal_name} requires {reference_style} references",
            )

        return self._reformat_references(references_text, reference_style)

    # ── HELPERS ───────────────────────────────────────────────────────────────

    def _extract_sections(self, text: str) -> Dict[str, str]:
        section_pattern = r"#+\s*([^#\n]+)\n(.*?)(?=\n#+|$)"
        matches = re.finditer(section_pattern, text, re.IGNORECASE | re.DOTALL)
        sections = {}
        for match in matches:
            sections[match.group(1).strip()] = match.group(2).strip()
        return sections

    def _to_title_case(self, text: str) -> str:
        # Strip any leading ## markdown prefix from title
        text = re.sub(r'^#+\s*', '', text)
        SMALL_WORDS = {
            "a", "an", "the", "and", "but", "or", "for", "nor",
            "on", "at", "to", "by", "in", "of", "up", "as", "is", "vs"
        }
        words = text.split()
        result = []
        for i, word in enumerate(words):
            if i == 0 or word.lower() not in SMALL_WORDS:
                result.append(word.capitalize())
            else:
                result.append(word.lower())
        return " ".join(result)

    def _detect_reference_style(self, references: str) -> str:
        if re.search(r"\[\d+\]", references):
            return "numbered"
        if re.search(r"\([A-Za-z]+,\s*\d{4}\)", references):
            return "alphabetical"
        if re.search(r"^\d+\.", references, re.MULTILINE):
            return "numbered"
        return "unknown"

    def _reformat_references(self, references: str, target_style: str) -> str:
        lines = [l.strip() for l in references.split("\n") if l.strip()]
        formatted = ""

        if target_style == "numbered":
            for i, line in enumerate(lines, 1):
                clean = re.sub(r"^\[\d+\]|\d+\.", "", line).strip()
                formatted += f"{i}. {clean}\n"
        elif target_style == "alphabetical":
            for line in lines:
                formatted += f"• {line}\n"
        elif target_style == "superscript":
            for i, line in enumerate(lines, 1):
                formatted += f"[{i}] {line}\n"
        else:
            formatted = "\n".join(lines)

        return formatted

    def get_formatting_summary(self) -> str:
        summary  = f"Formatted for: {self.journal_name}\n\n"
        summary += "Journal Guidelines:\n"
        summary += f"- Font: {self.journal_profile.get('font')}\n"
        summary += f"- Font Size: {self.journal_profile.get('font_size')}pt\n"
        summary += f"- Line Spacing: {self.journal_profile.get('line_spacing')}\n"
        summary += f"- Abstract Max: {self.journal_profile.get('abstract_max_words')} words\n"
        summary += f"- Citation Style: {self.journal_profile.get('reference_style')}\n"
        summary += f"- Required Structure: {', '.join(self.journal_profile.get('structure', []))}\n\n"
        summary += "Changes Made:\n"
        summary += self.changelog.to_markdown()
        return summary


# ─────────────────────────────────────────────────────────────────────────────
# CSL citation rendering (used by backend/main.py)
# ─────────────────────────────────────────────────────────────────────────────

def render_citations_with_csl(body: str, references, csl_style: str):
    """
    Render in-text citations and bibliography using citeproc-py.

    Expected citation syntax in body:  [@ref1]  or  [@ref1; @ref2]

    References can be:
    - CSL-JSON list of dicts (recommended, must include "id")
    - list of strings
    - plain string with newline-separated references
    """

    correction_log = []

    try:
        from citeproc import CitationStylesBibliography, CitationStylesStyle
        from citeproc import formatter
        from citeproc import Citation, CitationItem
        from citeproc.source.json import CiteProcJSON
        import citeproc_styles
    except ImportError as e:
        import sys
        print(f"Failed to import citeproc: {e}")
        print(f"Python sys.path: {sys.path}")
        raise e

    # ── Normalise references to CSL-JSON list ─────────────────────────────
    refs = []
    if isinstance(references, list) and references and isinstance(references[0], dict):
        refs = references
        refs = [{**r, "type": r.get("type", "article-journal")}for r in refs]
        correction_log.append("Using CSL-JSON references for citeproc rendering.")
    else:
        if isinstance(references, str):
            lines = [l.strip() for l in references.split("\n") if l.strip()]
        elif isinstance(references, list):
            lines = [l.strip() for l in references if isinstance(l, str) and l.strip()]
        else:
            lines = []
        refs = [
                    {
                        "id": f"ref{i+1}",
                        "type": "article-journal",
                        "title": line,
                        "author": [{"family": "Unknown", "given": ""}],
                    }
                    for i, line in enumerate(lines)
            ]
        if refs:
            correction_log.append("Converted plain references into minimal CSL-JSON items.")

    # ── Build bibliography ────────────────────────────────────────────────
    style_path   = citeproc_styles.get_style_filepath(csl_style)
    style        = CitationStylesStyle(style_path, validate=False)
    bibliography = CitationStylesBibliography(
        style, CiteProcJSON(refs), formatter.plain
    )

    def _format_citation(citekeys):
        items    = [CitationItem(key) for key in citekeys]
        citation = Citation(items)
        bibliography.register(citation)
        rendered = bibliography.cite(
            citation, lambda x: bibliography.citation(x, lambda y: y)
        )
        if isinstance(rendered, (list, tuple)):
            return "".join(str(p) for p in rendered)
        return str(rendered)

    # ── Replace [@key] patterns in body ──────────────────────────────────
    cite_pattern = re.compile(r"\[@([^\]]+)\]")
    replaced_any = False

    def _replace(match):
        nonlocal replaced_any
        raw  = match.group(1)
        keys = []
        for part in raw.split(";"):
            part = part.strip().lstrip("@")
            if part:
                keys.append(part)
        if not keys:
            return match.group(0)
        replaced_any = True
        return _format_citation(keys)

    new_body = cite_pattern.sub(_replace, body)

    if replaced_any:
        correction_log.append("Re-rendered in-text citations using citeproc-py.")
    else:
        correction_log.append("No citekeys found in body; in-text citations unchanged.")

    # ── Render bibliography ───────────────────────────────────────────────
    bib_entries      = [str(entry) for entry in bibliography.bibliography()]
    bibliography_text = "\n".join(bib_entries).strip()
    if bibliography_text:
        correction_log.append("Rendered bibliography using citeproc-py.")

    return new_body, bibliography_text, correction_log