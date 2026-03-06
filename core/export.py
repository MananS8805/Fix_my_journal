"""
Export manuscript to various formats (LaTeX, DOCX, PDF).
"""

import os
import re
from typing import Dict, Optional
from pathlib import Path


class ManuscriptExporter:
    """Export formatted manuscript to various output formats."""
    
    def __init__(self, output_dir: Optional[str] = None):
        repo_root = Path(__file__).resolve().parents[1]
        default_dir = repo_root / "exports"
        resolved_dir = Path(output_dir) if output_dir else default_dir
        self.output_dir = str(resolved_dir)
        os.makedirs(self.output_dir, exist_ok=True)
    
    def export_to_latex(self, manuscript: Dict, journal_name: str, changelog) -> str:
        """
        Export manuscript to LaTeX format.
        
        Args:
            manuscript: Structured manuscript data
            journal_name: Target journal name
            changelog: Change tracking object
            
        Returns:
            Path to generated LaTeX file
        """
        latex_content = self._generate_latex(manuscript, journal_name, changelog)
        
        output_file = os.path.join(self.output_dir, f"{journal_name}_manuscript.tex")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        
        return output_file
    
    def export_to_docx(self, manuscript: Dict, journal_name: str, changelog) -> str:

        try:
            from docx import Document
            from docx.shared import Pt, Inches
            from docx.enum.text import WD_PARAGRAPH_ALIGNMENT
        except ImportError:
            raise ImportError("DOCX export requires python-docx")

        from core.journal_profiles import get_journal_profile

        profile = get_journal_profile(journal_name)

        doc = Document()

        # -------------------------------------------------
        # Apply Page Margins
        # -------------------------------------------------

        section = doc.sections[0]

        margins = profile.get("margins", {})

        section.top_margin = Inches(margins.get("top", 1))
        section.bottom_margin = Inches(margins.get("bottom", 1))
        section.left_margin = Inches(margins.get("left", 1))
        section.right_margin = Inches(margins.get("right", 1))

        # -------------------------------------------------
        # Apply Default Font Style
        # -------------------------------------------------

        style = doc.styles["Normal"]

        font = style.font
        font.name = profile.get("font", "Times New Roman")
        font.size = Pt(profile.get("font_size", 12))

        # -------------------------------------------------
        # Title
        # -------------------------------------------------

        title_text = manuscript["metadata"].get("title", "Untitled Manuscript")

        title = doc.add_heading(title_text, level=0)
        title.alignment = WD_PARAGRAPH_ALIGNMENT.CENTER

        # -------------------------------------------------
        # Abstract
        # -------------------------------------------------

        doc.add_heading("Abstract", level=1)

        abstract_para = doc.add_paragraph(manuscript.get("abstract", ""))

        abstract_format = abstract_para.paragraph_format

        abstract_format.line_spacing = profile.get("line_spacing", 1.5)
        abstract_format.space_after = Pt(12)

        # -------------------------------------------------
        # Body
        # -------------------------------------------------

        doc.add_heading("Body", level=1)

        body_text = manuscript.get("body", "")

        paragraphs = body_text.split("\n")

        for para in paragraphs:

            if not para.strip():
                continue

            p = doc.add_paragraph(para)

            p_format = p.paragraph_format

            # Line spacing
            p_format.line_spacing = profile.get("line_spacing", 1.5)

            # Paragraph spacing
            p_format.space_before = Pt(6)
            p_format.space_after = Pt(6)

            # First-line indentation
            p_format.first_line_indent = Inches(0.25)

        # -------------------------------------------------
        # References
        # -------------------------------------------------

        doc.add_heading("References", level=1)

        references = manuscript.get("references", "")

        if isinstance(references, list):
            references = "\n".join(references)

        for ref in references.split("\n"):

            if ref.strip():

                r = doc.add_paragraph(ref)

                r_format = r.paragraph_format

                r_format.line_spacing = profile.get("line_spacing", 1.5)
                r_format.space_after = Pt(6)

        # -------------------------------------------------
        # Formatting Change Log
        # -------------------------------------------------

        doc.add_heading("Formatting Changes", level=1)

        doc.add_paragraph(changelog.to_markdown())

        # -------------------------------------------------
        # Save File
        # -------------------------------------------------

        output_file = os.path.join(self.output_dir, f"{journal_name}_manuscript.docx")

        doc.save(output_file)

        return output_file    
    def export_to_pdf(self, latex_file: str, journal_name: str) -> str:
        """
        Convert LaTeX to PDF using pdflatex.
        (Stub - would require pdflatex installation)
        """
        try:
            import subprocess
            output_file = os.path.join(self.output_dir, f"{journal_name}_manuscript.pdf")
            subprocess.run(
                ["pdflatex", "-interaction=nonstopmode", "-output-directory", 
                 self.output_dir, latex_file],
                capture_output=True,
                timeout=60
            )
            return output_file
        except Exception as e:
            raise Exception(f"PDF export requires pdflatex: {str(e)}")
    
    def _generate_latex(self, manuscript: Dict, journal_name: str, changelog) -> str:
        """Generate LaTeX document structure."""
        
        latex = r"""
\documentclass[11pt]{article}
\usepackage[utf8]{inputenc}
\usepackage{geometry}
\usepackage{graphicx}
\usepackage{hyperref}
\usepackage{amsmath}
\usepackage[numbers]{natbib}

\geometry{margin=1in}

\title{""" + manuscript["metadata"].get("title", "Manuscript") + r"""}
\author{}
\date{\today}

\begin{document}

\maketitle

\begin{abstract}
""" + (manuscript["abstract"][:500] if manuscript["abstract"] else "No abstract provided.") + r"""
\end{abstract}

\section*{Introduction}
""" + self._extract_first_section(manuscript["body"], "Introduction") + r"""

\section*{Methods}
""" + self._extract_first_section(manuscript["body"], "Methods") + r"""

\section*{Results}
""" + self._extract_first_section(manuscript["body"], "Results") + r"""

\section*{Discussion}
""" + self._extract_first_section(manuscript["body"], "Discussion") + r"""

\section*{References}
\begin{thebibliography}{99}
""" + self._format_references(manuscript["references"]) + r"""
\end{thebibliography}

\section*{Formatting Changes Log}
""" + self._changelog_to_latex(changelog) + r"""

\end{document}
"""
        return latex
    
    def _extract_first_section(self, text: str, section_name: str) -> str:
        """Extract first part of a section."""
        pattern = rf"(?i)#+\s*{section_name}\s*\n(.*?)(?=\n#+|$)"
        match = re.search(pattern, text, re.DOTALL)
        if match:
            section_text = match.group(1).strip()
            return section_text[:300] + "..." if len(section_text) > 300 else section_text
        return f"No {section_name} section found."
    
    def _format_references(self, references_text: str) -> str:
        """Format references for LaTeX."""
        lines = references_text.split('\n')
        latex_refs = ""
        for i, line in enumerate(lines[:10], 1):
            if line.strip():
                latex_refs += rf"\bibitem{{{i}}} {line}" + "\n"
        return latex_refs
    
    def _changelog_to_latex(self, changelog) -> str:
        """Convert changelog to LaTeX format."""
        changes = changelog.changes
        latex = ""
        for change in changes[:10]:  # Limit to 10 changes for display
            latex += f"\\textbf{{{change['category']}:}} {change['old_value']} $\\rightarrow$ {change['new_value']} ({change['reason']}) \\\\\n"
        return latex
