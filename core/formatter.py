"""
Manuscript formatter engine - applies journal-specific formatting rules.
"""

import re
from typing import Dict
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
        """
        Apply all formatting transformations.
        
        Args:
            manuscript: Parsed manuscript with keys: metadata, abstract, body, references
            
        Returns:
            Formatted manuscript with all changes applied
        """
        formatted = {
            "metadata": self._format_metadata(manuscript["metadata"]),
            "abstract": self._format_abstract(manuscript["abstract"]),
            "body": self._format_body(manuscript["body"]),
            "references": self._format_references(manuscript["references"]),
            "changelog": self.changelog.to_dict(),
            "journal": self.journal_name,
        }
        
        return formatted
    
    def _format_metadata(self, metadata: Dict) -> Dict:
        """Format title and metadata according to journal guidelines."""
        title_case = self.journal_profile.get("title_case", "Title Case")
        original_title = metadata.get("title", "")
        formatted_title = original_title
        
        if title_case == "UPPERCASE":
            formatted_title = original_title.upper()
            self.changelog.add_change(
                "metadata_title_case",
                f"'{original_title}'",
                f"'{formatted_title}'",
                f"{self.journal_name} requires UPPERCASE titles"
            )
        elif title_case == "Title Case":
            formatted_title = self._to_title_case(original_title)
            self.changelog.add_change(
                "metadata_title_case",
                f"'{original_title}'",
                f"'{formatted_title}'",
                f"{self.journal_name} requires Title Case"
            )
        
        return {
            "title": formatted_title,
            "journal": self.journal_name,
            **metadata
        }
    
    def _format_abstract(self, abstract: str) -> str:
        """Trim and format abstract to journal requirements."""
        max_words = self.journal_profile.get("abstract_max_words", 150)
        words = abstract.split()
        
        if len(words) > max_words:
            original_length = len(words)
            abstract = " ".join(words[:max_words])
            self.changelog.add_change(
                "abstract_length",
                f"{original_length} words",
                f"{max_words} words",
                f"{self.journal_name} limits abstracts to {max_words} words"
            )
        
        return abstract
    
    def _format_body(self, body: str) -> str:
        """Reorder and format body sections according to journal structure."""
        required_structure = self.journal_profile.get("structure", [])
        
        # Extract existing sections
        sections = self._extract_sections(body)
        
        # Reorder sections
        formatted_body = ""
        for required_section in required_structure:
            for section_name, content in sections.items():
                if section_name.lower() in required_section.lower():
                    formatted_body += f"\n## {required_section}\n{content}\n"
                    self.changelog.add_change(
                        "section_order",
                        section_name,
                        required_section,
                        f"{self.journal_name} requires section structure: {', '.join(required_structure)}"
                    )
                    break
        
        return formatted_body
    
    def _format_references(self, references: str) -> str:
        """Reformat references according to journal citation style."""
        reference_style = self.journal_profile.get("reference_style", "alphabetical")
        original_style = self._detect_reference_style(references)
        
        if original_style != reference_style:
            self.changelog.add_change(
                "reference_style",
                original_style,
                reference_style,
                f"{self.journal_name} requires {reference_style} citation style"
            )
        
        # Parse and reformat references
        formatted_refs = self._reformat_references(references, reference_style)
        
        return formatted_refs
    
    def _extract_sections(self, text: str) -> Dict[str, str]:
        """Extract sections from body text."""
        section_pattern = r"#+\s*([^#\n]+)\n(.*?)(?=\n#+|$)"
        matches = re.finditer(section_pattern, text, re.IGNORECASE | re.DOTALL)
        
        sections = {}
        for match in matches:
            section_title = match.group(1).strip()
            section_content = match.group(2).strip()
            sections[section_title] = section_content
        
        return sections
    
    def _to_title_case(self, text: str) -> str:
        """Convert text to title case."""
        return " ".join(word.capitalize() for word in text.split())
    
    def _detect_reference_style(self, references: str) -> str:
        """Detect current reference style."""
        if re.search(r'\[\d+\]', references):
            return "numbered"
        elif re.search(r'\([A-Z][a-z]+,\s*\d{4}\)', references):
            return "alphabetical"
        elif re.search(r'^\d+\.', references, re.MULTILINE):
            return "numbered"
        else:
            return "unknown"
    
    def _reformat_references(self, references: str, target_style: str) -> str:
        """Reformat references to target citation style."""
        formatted = ""
        
        if target_style == "superscript":
            # Convert to superscript format
            lines = references.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    formatted += f"[{i}] {line}\n"
        
        elif target_style == "numbered":
            # Convert to numbered format
            lines = references.split('\n')
            for i, line in enumerate(lines, 1):
                if line.strip():
                    # Remove existing numbering
                    clean_line = re.sub(r'^\[\d+\]|\^\d+', '', line).strip()
                    formatted += f"{i}. {clean_line}\n"
        
        elif target_style == "alphabetical":
            # Convert to alphabetical format with author-year
            lines = references.split('\n')
            for line in lines:
                if line.strip():
                    formatted += f"- {line}\n"
        
        else:
            formatted = references
        
        return formatted
    
    def get_formatting_summary(self) -> str:
        """Get human-readable summary of formatting applied."""
        summary = f"Formatted for: {self.journal_name}\n\n"
        summary += f"Journal Guidelines:\n"
        summary += f"- Font: {self.journal_profile.get('font')}\n"
        summary += f"- Font Size: {self.journal_profile.get('font_size')}pt\n"
        summary += f"- Line Spacing: {self.journal_profile.get('line_spacing')}\n"
        summary += f"- Abstract Max: {self.journal_profile.get('abstract_max_words')} words\n"
        summary += f"- Citation Style: {self.journal_profile.get('reference_style')}\n"
        summary += f"- Required Structure: {', '.join(self.journal_profile.get('structure', []))}\n\n"
        summary += f"Changes Made:\n{self.changelog.to_markdown()}"
        
        return summary


def render_citations_with_csl(body: str, references, csl_style: str):
    """
    Render in-text citations and bibliography using citeproc-py.

    Expected citation syntax in body:
    - [@ref1]
    - [@ref1; @ref2]

    References can be:
    - CSL-JSON list of dicts (recommended, must include "id")
    - list of strings
    - string with newline-separated references
    """

    correction_log = []

    # Lazy imports to avoid heavy startup costs
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

    refs = []

    if isinstance(references, list) and references and isinstance(references[0], dict):
        refs = references
        correction_log.append("Using CSL-JSON references for citeproc rendering.")
    else:
        if isinstance(references, str):
            lines = [line.strip() for line in references.split("\n") if line.strip()]
        elif isinstance(references, list):
            lines = [line.strip() for line in references if isinstance(line, str) and line.strip()]
        else:
            lines = []

        refs = [{"id": f"ref{i+1}", "title": line} for i, line in enumerate(lines)]
        if refs:
            correction_log.append("Converted plain references into minimal CSL-JSON items.")

    style_path = citeproc_styles.get_style_filepath(csl_style)
    style = CitationStylesStyle(style_path, validate=False)
    bibliography = CitationStylesBibliography(style, CiteProcJSON(refs), formatter.plain)

    def _format_citation(citekeys):
        items = [CitationItem(key) for key in citekeys]
        citation = Citation(items)
        bibliography.register(citation)
        rendered = bibliography.cite(citation, lambda x: bibliography.citation(x, lambda y: y))
        if isinstance(rendered, (list, tuple)):
            return "".join(str(part) for part in rendered)
        return str(rendered)

    # Replace citekey patterns in body
    cite_pattern = re.compile(r"\[@([^\]]+)\]")
    replaced_any = False

    def _replace(match):
        nonlocal replaced_any
        raw = match.group(1)
        keys = []
        for part in raw.split(";"):
            part = part.strip()
            if part.startswith("@"):
                part = part[1:]
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

    # Render bibliography
    bib_entries = [str(entry) for entry in bibliography.bibliography()]
    bibliography_text = "\n".join(bib_entries).strip()
    if bibliography_text:
        correction_log.append("Rendered bibliography using citeproc-py.")

    return new_body, bibliography_text, correction_log
