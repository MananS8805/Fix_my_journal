# Manuscript Formatting Agent

A modular FastAPI-based system for parsing, formatting, and exporting scientific manuscripts according to journal-specific guidelines.

## Features

✅ **Multi-format Parsing** - Extract structured content from PDF and DOCX files
✅ **Journal-Specific Formatting** - Support for 5+ major journals (Nature, Science, IEEE, ACM, arXiv)
✅ **AI-Powered Style Extraction** - Use Google Generative AI to extract custom formatting rules
✅ **Citation Validation** - Validate in-text citations against reference lists
✅ **Compliance Scoring** - Assess document structure completeness
✅ **Multi-format Export** - Export as LaTeX, DOCX, or PDF
✅ **Change Tracking** - Detailed changelog of all transformations applied
✅ **Real-time Dashboard** - Structured JSON responses for frontend integration

## Project Structure

```
New folder/
├── requirements.txt              # Python dependencies
├── backend/
│   └── main.py                  # FastAPI application & endpoints
├── core/
│   ├── __init__.py
│   ├── parser.py                # Manuscript parsing (Docling integration)
│   ├── agents.py                # AI agents (StyleAgent, CitationAgent)
│   ├── formatter.py             # Journal-specific formatting engine
│   ├── export.py                # LaTeX/DOCX/PDF export
│   ├── changelog.py             # Change tracking system
│   └── journal_profiles.py      # Journal formatting profiles
├── utils/
│   ├── __init__.py
│   └── helpers.py               # Utility functions
└── exports/                     # Generated output files
```

## Installation

1. **Install Dependencies**
```bash
pip install -r requirements.txt
```

2. **Configure Google Generative AI** (Optional - for StyleAgent)
```bash
export GOOGLE_API_KEY="your-api-key"
```

3. **Start the Server**
```bash
cd backend
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

## API Endpoints

### 1. Parse Manuscript
**Endpoint:** `POST /parse`

Extract structured content from uploaded manuscript.

**Request:**
```bash
curl -X POST "http://localhost:8000/parse" \
  -F "file=@paper.pdf"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "metadata": {
      "title": "Novel Deep Learning Approach"
    },
    "abstract": "This paper presents...",
    "body": "## Introduction\n...",
    "references": "[1] Author et al...",
    "section_headers": ["Introduction", "Methods", "Results", "Discussion"],
    "in_text_citations": [["[1]", 5], ["[2]", 3]],
    "compliance_score": {
      "compliance_score": 85.5,
      "sections_found": ["Introduction", "Methods"],
      "missing_sections": ["References"]
    }
  }
}
```

### 2. Get Available Journals
**Endpoint:** `GET /journals`

Retrieve list of supported journals and their basic requirements.

**Response:**
```json
{
  "success": true,
  "data": {
    "available_journals": [
      {
        "name": "Nature",
        "id": "nature",
        "abstract_max_words": 150,
        "citation_style": "superscript",
        "page_limit": 5
      },
      {
        "name": "IEEE",
        "id": "ieee",
        "abstract_max_words": 100,
        "citation_style": "numbered",
        "page_limit": 8
      },
      ...
    ],
    "total_journals": 5
  }
}
```

### 3. Get Journal Details
**Endpoint:** `GET /journals/{journal_name}`

Get detailed formatting profile for a specific journal.

**Example:**
```bash
curl "http://localhost:8000/journals/nature"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "name": "Nature",
    "abstract_max_words": 150,
    "font": "Times New Roman",
    "font_size": 12,
    "line_spacing": 1.5,
    "margins": {"top": 1, "bottom": 1, "left": 1.25, "right": 1.25},
    "reference_style": "superscript",
    "keywords": true,
    "structure": ["Title", "Abstract", "Keywords", "Introduction", "Methods", "Results", "Discussion", "References"],
    "doi_required": true,
    ...
  }
}
```

### 4. Format Manuscript
**Endpoint:** `POST /format-manuscript`

Format a manuscript according to journal guidelines without exporting.

**Request:**
```bash
curl -X POST "http://localhost:8000/format-manuscript?journal=nature" \
  -F "file=@paper.pdf"
```

**Response:**
```json
{
  "success": true,
  "data": {
    "original": { ... original parsed content ... },
    "formatted": {
      "metadata": {
        "title": "NOVEL DEEP LEARNING APPROACH",
        "journal": "NATURE"
      },
      "abstract": "This study presents a novel approach...",
      "body": "...",
      "references": "...",
      "changelog": { ... detailed changelog ... },
      "journal": "NATURE"
    },
    "summary": "Formatted for: NATURE\n\nJournal Guidelines:\n- Font: Times New Roman\n..."
  }
}
```

### 5. Format and Export
**Endpoint:** `POST /format-and-export`

Format manuscript and export to specified format (LaTeX, DOCX, PDF).

**Request:**
```bash
curl -X POST "http://localhost:8000/format-and-export?journal=ieee&format=latex" \
  -F "file=@paper.pdf" \
  --output formatted_paper.tex
```

**Query Parameters:**
- `journal` (required): Target journal (nature, science, ieee, acm, arxiv)
- `format` (optional, default: latex): Export format (latex, docx, pdf)

**Response:**
```json
{
  "success": true,
  "data": {
    "journal": "IEEE",
    "export_format": "latex",
    "file_path": "./exports/ieee_manuscript.tex",
    "total_changes": 7,
    "changelog": "# Manuscript Formatting Changes\n\n**Timestamp:** 2026-03-05T...\n\n## ABSTRACT_LENGTH\n\n- **Change:** 250 words → 100 words\n  **Reason:** IEEE limits abstracts to 100 words\n\n## SECTION_ORDER\n\n- **Change:** Introduction → I. INTRODUCTION\n  **Reason:** IEEE requires section structure: ...",
    "metadata": {
      "title": "Novel Deep Learning Approach",
      "journal": "IEEE",
      "abstract_length": 98,
      "page_limit": 8
    }
  }
}
```

### 6. Download Formatted File
**Endpoint:** `GET /export-file/{journal_name}/{filename}`

Download formatted manuscript file.

**Example:**
```bash
curl "http://localhost:8000/export-file/nature/manuscript.tex" \
  --output my_formatted_paper.tex
```

### 7. Health Check
**Endpoint:** `GET /health`

Check if the service is running.

## Supported Journals

| Journal | ID | Abstract Max | Citation Style | Page Limit |
|---------|----|----|---|---|
| Nature | `nature` | 150 words | Superscript | 5 |
| Science | `science` | 200 words | Numbered | 6 |
| IEEE | `ieee` | 100 words | Numbered | 8 |
| ACM | `acm` | 150 words | Alphabetical | 10 |
| arXiv | `arxiv` | 250 words | Alphabetical | Unlimited |

## Core Modules

### 1. **parser.py** - `ManuscriptParser`
```python
from core.parser import ManuscriptParser

parser = ManuscriptParser()
result = parser.parse("paper.pdf")
# Returns: {"metadata": {...}, "abstract": "...", "body": "...", "references": "..."}
```

### 2. **formatter.py** - `ManuscriptFormatter`
```python
from core.formatter import ManuscriptFormatter

formatter = ManuscriptFormatter("nature")
formatted = formatter.format_manuscript(parsed_data)
changelog = formatter.changelog
```

### 3. **export.py** - `ManuscriptExporter`
```python
from core.export import ManuscriptExporter

exporter = ManuscriptExporter()
latex_file = exporter.export_to_latex(formatted_manuscript, "nature", changelog)
docx_file = exporter.export_to_docx(formatted_manuscript, "nature", changelog)
```

### 4. **agents.py** - AI-Powered Agents

#### StyleAgent
```python
from core.agents import StyleAgent

agent = StyleAgent(api_key="YOUR_API_KEY")
rules = agent.extract_formatting_rules("https://example.com/style-guide")
```

#### CitationAgent
```python
from core.agents import CitationAgent

agent = CitationAgent()
validation = agent.validate_citations(body_text, references_list)
```

### 5. **helpers.py** - Utility Functions
```python
from utils.helpers import (
    identify_section_headers,
    calculate_compliance_score,
    extract_in_text_citations
)

headers = identify_section_headers(text)
score = calculate_compliance_score(metadata, abstract, body, references)
citations = extract_in_text_citations(text)
```

## Example Workflow

```python
import requests

# Step 1: Upload and parse manuscript
with open("my_paper.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post("http://localhost:8000/parse", files=files)
    parsed = response.json()["data"]

# Step 2: Check available journals
journals_response = requests.get("http://localhost:8000/journals")
journals = journals_response.json()["data"]["available_journals"]

# Step 3: Format for specific journal and export
with open("my_paper.pdf", "rb") as f:
    files = {"file": f}
    response = requests.post(
        "http://localhost:8000/format-and-export",
        params={"journal": "nature", "format": "latex"},
        files=files
    )
    export_data = response.json()["data"]

# Step 4: Get updated file
download_response = requests.get(f"http://localhost:8000/export-file/{export_data['journal']}/manuscript.tex")
with open("formatted_paper.tex", "wb") as f:
    f.write(download_response.content)
```

## Change Tracking

Every transformation generates a detailed changelog showing:
- **Category**: What was changed (title case, abstract length, reference style, etc.)
- **Old Value**: Original value
- **New Value**: Formatted value
- **Reason**: Why the change was necessary
- **Timestamp**: When the change was made

Example changelog output:
```markdown
# Manuscript Formatting Changes

**Timestamp:** 2026-03-05T10:30:45

## ABSTRACT_LENGTH

- **Change:** 250 words → 150 words
  **Reason:** Nature limits abstracts to 150 words

## REFERENCE_STYLE

- **Change:** alphabetical → superscript
  **Reason:** Nature requires superscript citation style

## SECTION_ORDER

- **Change:** Introduction → kept as-is
  **Reason:** Nature requires structure: Title, Abstract, Keywords, Introduction,...
```

## Output Formats

### LaTeX
- Complete `.tex` file with preamble
- Includes changelog as appendix
- Ready for `pdflatex` compilation
- Customizable for journal-specific packages

### DOCX
- Microsoft Word format
- Formatted with journal requirements
- Includes changelog document
- Editable for final adjustments

### PDF
- Requires `pdflatex` installation
- Generated from LaTeX
- Professional formatting
- Includes all journal requirements

## Configuration

Create a `.env` file for configuration:
```bash
GOOGLE_API_KEY=your_api_key_here
EXPORT_DIRECTORY=./exports
MAX_UPLOAD_SIZE=50MB
```

## Error Handling

All endpoints return standardized error responses:

```json
{
  "success": false,
  "error": "Journal 'unknown' not found"
}
```

Common error codes:
- `400`: Bad request (invalid journal, unsupported format)
- `404`: File or journal not found
- `500`: Server error

## Performance Notes

- **Parsing**: 5-30 seconds per document (depends on file size)
- **Formatting**: < 1 second
- **Export**: 1-5 seconds (LaTeX/DOCX), 10-30 seconds (PDF)
- **API Response**: < 100ms for metadata operations

## Future Enhancements

- [ ] Support for more journals (50+ major publishers)
- [ ] Custom journal profile upload
- [ ] Batch processing for multiple files
- [ ] Integration with research databases (CrossRef, PubMed)
- [ ] Real-time collaboration endpoints
- [ ] Advanced citation formatting (CrossRef integration)
- [ ] Plagiarism detection integration
- [ ] Table of Contents auto-generation

## Troubleshooting

### "ModuleNotFoundError: No module named 'docling'"
```bash
pip install docling
```

### "GOOGLE_API_KEY not configured"
Set environment variable:
```bash
export GOOGLE_API_KEY="your_key_here"
```

### PDF export fails
Ensure `pdflatex` is installed:
```bash
# macOS
brew install mactex

# Ubuntu/Debian
sudo apt-get install texlive-latex-base

# Windows
# Download from https://miktex.org/
```

## License

MIT License

## Support

For issues or questions, please open an issue or contact the development team.
