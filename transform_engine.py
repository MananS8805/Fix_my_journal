"""
Transform engine: JSON (or DOCX/PDF) -> Gemini markdown -> Pandoc DOCX.

Usage examples:
  python transform_engine.py --input exports/sample_manuscript.pdf --style-url "https://example.com/guide" --output exports/formatted.docx
  python transform_engine.py --input manuscript.json --style-url "https://example.com/guide" --template templates/journal_template.docx

Notes:
  - Requires pandoc on PATH.
  - Requires a reference DOCX template: templates/journal_template.docx
"""

import argparse
import json
import os
import re
import subprocess
import tempfile
from pathlib import Path

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai


# Required variables (override via env or CLI)
GEMINI_API_KEY = "AIzaSyA-G7pm1m_CJkOL9PwoJKOgm1xnA6XKOwU"
INPUT_JSON = ""
STYLE_GUIDE_URL = ""

MODEL_NAME = os.getenv("GEMINI_MODEL", "gemini-1.5-pro")


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def fetch_style_guide(url: str) -> str:
    if not url:
        return ""
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    return _clean_text(soup.get_text(separator="\n"))


def load_structured_json(path: Path) -> dict:
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict):
        raise ValueError("Input JSON must be an object with metadata, abstract, body, references.")
    return data


def parse_manuscript(path: Path) -> dict:
    # Use existing parser for PDF/DOCX inputs
    from core.parser import ManuscriptParser

    parser = ManuscriptParser()
    return parser.parse(str(path))


def build_prompt(style_guide: str, manuscript: dict) -> str:
    # Keep prompt plain and strict to avoid summarization.
    return f"""
You are an academic formatting assistant.

Task:
- Return ONLY Markdown (no backticks, no commentary).
- Preserve the scientific content verbatim. Do NOT summarize, paraphrase, or add new text.
- Reorganize and reformat only.
- Title should be properly cased and appear as a top-level Markdown heading (# Title).
- Headings must be properly leveled (#, ##, ###).
- Update citations to match the target journal style in the style guide.
- Keep references intact; only reformat their order/labeling if the style guide requires.

Style Guidelines:
{style_guide[:12000]}

Manuscript Content (JSON):
{json.dumps(manuscript, indent=2)[:12000]}

Output format:
# Title

## Abstract
...

## Introduction
...

## References
...
""".strip()


def generate_markdown(api_key: str, prompt: str) -> str:
    key = api_key if api_key and api_key != "YOUR_PASTE_HERE" else os.getenv("GEMINI_API_KEY", "")
    if not key:
        raise ValueError("GEMINI_API_KEY is missing. Set it in the script or environment.")

    genai.configure(api_key=key)
    model = genai.GenerativeModel(MODEL_NAME)
    response = model.generate_content(prompt)
    text = response.text or ""

    # Minimal sanity cleanup
    text = text.strip()
    if not text.startswith("# "):
        # Ensure title heading exists
        text = "# Manuscript\n\n" + text
    return text


def run_pandoc(input_md: Path, output_docx: Path, reference_doc: Path) -> None:
    if not reference_doc.exists():
        raise FileNotFoundError(
            f"Missing reference docx template: {reference_doc}. "
            "Create it (e.g., templates/journal_template.docx) with required styles."
        )

    cmd = [
        "pandoc",
        str(input_md),
        "-o",
        str(output_docx),
        f"--reference-doc={reference_doc}",
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise RuntimeError(
            f"pandoc failed (code {result.returncode}).\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )


def main():
    parser = argparse.ArgumentParser(description="Transform manuscript into formatted DOCX using Gemini + Pandoc.")
    parser.add_argument("--input", required=False, default=INPUT_JSON, help="Input JSON or DOCX/PDF file.")
    parser.add_argument("--style-url", required=False, default=STYLE_GUIDE_URL, help="Journal style guide URL.")
    parser.add_argument("--template", required=False, default="templates/journal_template.docx", help="Reference DOCX template.")
    parser.add_argument("--output", required=False, default="exports/formatted_manuscript.docx", help="Output DOCX path.")
    parser.add_argument("--api-key", required=False, default=GEMINI_API_KEY, help="Gemini API key.")
    args = parser.parse_args()

    if not args.input:
        raise ValueError("Input is required. Provide --input with a JSON or DOCX/PDF path.")

    input_path = Path(args.input).resolve()
    if not input_path.exists():
        raise FileNotFoundError(f"Input file not found: {input_path}")

    # Step 1: Parse -> structured JSON
    if input_path.suffix.lower() == ".json":
        structured = load_structured_json(input_path)
    elif input_path.suffix.lower() in {".pdf", ".docx", ".doc"}:
        structured = parse_manuscript(input_path)
    else:
        raise ValueError("Unsupported input type. Use .json, .pdf, .docx, or .doc")

    # Step 2: Fetch style guide and run Gemini
    style_text = fetch_style_guide(args.style_url) if args.style_url else ""
    prompt = build_prompt(style_text, structured)
    markdown = generate_markdown(args.api_key, prompt)

    # Step 3: Pandoc wrap -> DOCX
    output_docx = Path(args.output).resolve()
    output_docx.parent.mkdir(parents=True, exist_ok=True)
    template_path = Path(args.template).resolve()

    with tempfile.TemporaryDirectory() as tmpdir:
        md_path = Path(tmpdir) / "manuscript.md"
        md_path.write_text(markdown, encoding="utf-8")
        run_pandoc(md_path, output_docx, template_path)

    print(f"Formatted DOCX created: {output_docx}")


if __name__ == "__main__":
    main()
