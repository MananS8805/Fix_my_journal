"""
Pandoc transformer: Markdown -> DOCX using a reference doc template.
"""

import subprocess
import tempfile
from pathlib import Path


def markdown_to_docx(
    markdown_text: str,
    output_path: Path,
    reference_doc: Path,
    use_citeproc: bool = True,
) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if not reference_doc.exists():
        raise FileNotFoundError(
            f"Missing reference template: {reference_doc}. "
            "Create it (e.g., templates/apa7.docx) with journal styles."
        )

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "manuscript.md"
        md_path.write_text(markdown_text, encoding="utf-8")

        cmd = [
            "pandoc",
            str(md_path),
            "-o",
            str(output_path),
            f"--reference-doc={reference_doc}",
        ]
        if use_citeproc:
            cmd.append("--citeproc")

        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            raise RuntimeError(
                f"pandoc failed (code {result.returncode}).\n"
                f"STDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
            )

    return output_path
