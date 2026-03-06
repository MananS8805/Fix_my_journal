from fastapi import FastAPI, File, UploadFile, HTTPException, Query, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
import tempfile
import os
import sys
from pathlib import Path
import json
from datetime import datetime
from typing import Optional, Dict, Any
from pydantic import BaseModel
from dotenv import load_dotenv

load_dotenv()

# Ensure repo root is on sys.path when running from backend/
REPO_ROOT = Path(__file__).resolve().parents[1]
BACKEND_DIR = Path(__file__).resolve().parent

for p in [str(REPO_ROOT), str(BACKEND_DIR)]:
    if p not in sys.path:
        sys.path.insert(0, p)

EXPORTS_DIR = REPO_ROOT / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)



# ── Imports ───────────────────────────────────────────────────────────────────
from core.parser import ManuscriptParser
from core.discovery import get_journal_rules
from core.export import ManuscriptExporter
from core.transformer import markdown_to_docx
from core.validator import validate_transformation
from core.formatter import render_citations_with_csl
import importlib.util as _ilu2
_jp_spec = _ilu2.spec_from_file_location(
    "journal_profiles",
    Path(__file__).parents[1] / "core" / "journal_profiles.py"
)
_jp_mod = _ilu2.module_from_spec(_jp_spec)
_jp_spec.loader.exec_module(_jp_mod)
get_journal_list = _jp_mod.get_journal_list
get_journal_profile = _jp_mod.get_journal_profile   
import importlib.util as _ilu

_helpers_spec = _ilu.spec_from_file_location(
    "helpers",
    Path(__file__).parents[1] / "utils" / "helpers.py"
)
_helpers_mod = _ilu.module_from_spec(_helpers_spec)
_helpers_spec.loader.exec_module(_helpers_mod)
identify_section_headers = _helpers_mod.identify_section_headers
calculate_compliance_score = _helpers_mod.calculate_compliance_score
extract_in_text_citations = _helpers_mod.extract_in_text_citations

import importlib.util
_spec = importlib.util.spec_from_file_location(
    "templates",
    Path(__file__).parent / "utils" / "templates.py"
)
_mod = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_mod)
get_template_path = _mod.get_template_path


# ─────────────────────────────────────────────────────────────────────────────
# Pydantic models
# ─────────────────────────────────────────────────────────────────────────────

class TransformPayload(BaseModel):
    manuscript: Dict[str, Any]
    journal:    Optional[str] = None
    template:   Optional[str] = None
    style_url:  Optional[str] = None


# ─────────────────────────────────────────────────────────────────────────────
# App
# ─────────────────────────────────────────────────────────────────────────────

app = FastAPI(
    title="Manuscript Formatting Agent",
    description="Parse, format, and export scientific manuscripts per journal guidelines.",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── DEBUG (temporary) ─────────────────────────────────────────────────────────
@app.get("/debug")
async def debug():
    import sys
    try:
        from core.journal_profiles import get_journal_list, get_journal_profile
        jlist = get_journal_list()
        return {"sys_path": sys.path, "journals": jlist}
    except Exception as e:
        return {"sys_path": sys.path, "error": str(e)}

exporter      = ManuscriptExporter()
_style_agent  = None
_citation_agent = None


def get_style_agent():
    global _style_agent
    if _style_agent is None:
        from core.agents import StyleAgent
        _style_agent = StyleAgent()
    return _style_agent


def get_citation_agent():
    global _citation_agent
    if _citation_agent is None:
        from core.agents import CitationAgent
        _citation_agent = CitationAgent()
    return _citation_agent


# ─────────────────────────────────────────────────────────────────────────────
# Helper
# ─────────────────────────────────────────────────────────────────────────────

def _build_markdown(manuscript: Dict[str, Any], references_text: str) -> str:
    title    = manuscript.get("metadata", {}).get("title", "Manuscript")
    abstract = manuscript.get("abstract", "")
    body     = manuscript.get("body", "")

    md = f"# {title}\n\n"
    if abstract:
        md += "## Abstract\n\n" + abstract.strip() + "\n\n"
    md += body.strip() + "\n\n"
    if references_text:
        md += "## References\n\n" + references_text.strip() + "\n"
    return md


# ─────────────────────────────────────────────────────────────────────────────
# /parse
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/parse")
async def parse_manuscript(file: UploadFile = File(...)):
    """
    Parse an uploaded PDF or DOCX manuscript and extract structured content.

    Returns:
        JSON with keys: metadata, abstract, body, references,
        section_headers, in_text_citations, compliance_score
    """
    try:
        print(f"GOOGLE_API_KEY set: {bool(os.getenv('GOOGLE_API_KEY'))}")

        with tempfile.NamedTemporaryFile(
            delete=False, suffix=Path(file.filename).suffix
        ) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name

        parser      = ManuscriptParser()
        parsed_data = parser.parse(tmp_path)
        os.unlink(tmp_path)

        # Guard: Gemini parse can return {"error": "..."} on failure
        if "error" in parsed_data:
            return JSONResponse(
                status_code=400,
                content={"success": False, "error": parsed_data["error"]},
            )

        section_headers = identify_section_headers(parsed_data.get("body", ""))
        compliance = calculate_compliance_score(
            metadata   = parsed_data.get("metadata", {}),
            abstract   = parsed_data.get("abstract", ""),
            body       = parsed_data.get("body", ""),
            references = parsed_data.get("references", ""),
        )
        citations = extract_in_text_citations(parsed_data.get("body", ""))

        return JSONResponse({
            "success": True,
            "data": {
                "metadata":         parsed_data.get("metadata", {}),
                "abstract":         parsed_data.get("abstract", ""),
                "body":             parsed_data.get("body", ""),
                "references":       parsed_data.get("references", ""),
                "section_headers":  section_headers,
                "in_text_citations": citations,
                "compliance_score": compliance,
            },
        })

    except Exception as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


# ─────────────────────────────────────────────────────────────────────────────
# /transform-manuscript
# ─────────────────────────────────────────────────────────────────────────────

@app.post("/transform-manuscript")
async def transform_manuscript(
    request:   Request,
    journal:   str           = Query(..., description="Journal name, e.g. 'nature'"),
    file:      UploadFile    = File(None),
    template:  Optional[str] = Query(None, description="Path to reference .docx template"),
    style_url: Optional[str] = Query(None, description="Optional journal style URL override"),
):
    """
    Full pipeline: upload → parse → discover rules → validate citations
    → render CSL → transform to DOCX → sanity-check → return download URL.

    Accepts either:
    - multipart file upload (PDF / DOCX), or
    - JSON body with a 'manuscript' key.
    """
    correction_log      = []
    citation_validation = {}

    try:
        # ── Step 1: acquire manuscript ────────────────────────────────────
        if file is not None:
            with tempfile.NamedTemporaryFile(
                delete=False, suffix=Path(file.filename).suffix
            ) as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name

            parser     = ManuscriptParser()
            manuscript = parser.parse(tmp_path)
            os.unlink(tmp_path)

            # Guard: parser returns {"error": "..."} on Gemini failure
            if "error" in manuscript:
                return JSONResponse(
                    status_code=400,
                    content={"success": False, "error": manuscript["error"]},
                )
            correction_log.append("Parsed manuscript file into structured JSON via Gemini.")
        else:
            body_json = await request.json()
            if isinstance(body_json, dict) and "manuscript" in body_json:
                payload    = TransformPayload(**body_json)
                manuscript = payload.manuscript
                if payload.journal:
                    journal = payload.journal
                if payload.template:
                    template = payload.template
                if payload.style_url:
                    style_url = payload.style_url
            else:
                manuscript = body_json
            correction_log.append("Loaded structured manuscript JSON from request body.")

        # ── Step 2: journal profile + rule discovery ───────────────────────
        profile   = get_journal_profile(journal) or {}
        rules     = await get_journal_rules(journal, style_url=style_url)
        csl_style = rules.get("csl_style", "apa")

        correction_log.append(f"Journal profile loaded: {profile.get('name', journal)}.")
        correction_log.append(f"CSL style: {csl_style}.")
        if rules.get("font"):
            correction_log.append(f"Target font: {rules['font']}.")
        if rules.get("spacing"):
            correction_log.append(f"Target spacing: {rules['spacing']}.")
        if rules.get("margins"):
            correction_log.append(f"Target margins: {rules['margins']}.")

        # ── Step 3: citation validation ────────────────────────────────────
        body       = manuscript.get("body", "")
        references = manuscript.get("references", [])
        if isinstance(references, str):
            references = [
                {"id": f"ref{i+1}", "title": line}
                for i, line in enumerate(references.splitlines())
                if line.strip()
            ]

        try:
            citation_agent      = get_citation_agent()
            citation_validation = citation_agent.validate_citations(body, references)
            correction_log.append("Citation validation completed.")
            if not citation_validation.get("valid"):
                correction_log.append("Citation issues found. See 'citation_validation' for details.")
        except Exception as exc:
            correction_log.append(f"Citation validation failed: {exc}")

        # ── Step 4: CSL rendering ──────────────────────────────────────────
        bibliography_text = ""
        new_body          = body
        try:
            new_body, bibliography_text, csl_log = render_citations_with_csl(
                body=body,
                references=references,
                csl_style=csl_style,
            )
            correction_log.extend(csl_log)
        except Exception as csl_err:
            correction_log.append(
                f"CSL engine failed: {csl_err}. Original citations preserved."
            )

        # Fallback bibliography text if citeproc produced nothing
        if not bibliography_text:
            raw_refs = manuscript.get("references", "")
            if isinstance(raw_refs, str) and raw_refs.strip():
                bibliography_text = raw_refs.strip()
            elif isinstance(raw_refs, list):
                bibliography_text = "\n".join(
                    str(r) for r in raw_refs if str(r).strip()
                ).strip()

        # ── Step 5: build Markdown + convert to DOCX ──────────────────────
        body_for_md    = new_body if (new_body and new_body != body) else body
        final_markdown = _build_markdown(
            {**manuscript, "body": body_for_md},
            bibliography_text,
        )

        template_path = Path(template) if template else get_template_path(journal)

        filename    = (
            f"{journal.lower()}_transformed_"
            f"{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        )
        output_path = EXPORTS_DIR / filename

        # KEY FIX: pass the journal profile so the fallback renderer uses
        # the correct font, size, spacing and margins for this journal.
        markdown_to_docx(
            markdown_text  = final_markdown,
            output_path    = output_path,
            reference_doc  = template_path,
            use_citeproc   = True,
            journal_profile = profile,
        )
        correction_log.append("Generated DOCX (Pandoc or python-docx fallback).")

        # ── Step 6: sanity-check ───────────────────────────────────────────
        transformation_validation = validate_transformation(
            original_markdown = final_markdown,
            docx_path         = str(output_path),
        )
        correction_log.append("Sanity check on generated DOCX completed.")

        return JSONResponse({
            "success": True,
            "data": {
                "journal":                   journal.upper(),
                "file_path":                 str(output_path),
                "download_url":              f"/export-file/{journal.lower()}/{filename}",
                "correction_log":            correction_log,
                "discovered_rules":          rules,
                "citation_validation":       citation_validation,
                "transformation_validation": transformation_validation,
            },
        })

    except Exception as exc:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(exc)},
        )


# ─────────────────────────────────────────────────────────────────────────────
# /export-file
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/export-file/{journal_name}/{filename}")
async def export_file(journal_name: str, filename: str):
    """Download a formatted DOCX from the exports directory."""
    safe_name = Path(filename).name
    expected_prefix = f"{journal_name.lower()}_"

    if not safe_name.lower().startswith(expected_prefix):
        raise HTTPException(status_code=400, detail="Filename does not match journal.")

    file_path = (EXPORTS_DIR / safe_name).resolve()
    if EXPORTS_DIR not in file_path.parents and file_path != EXPORTS_DIR:
        raise HTTPException(status_code=400, detail="Invalid file path.")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found.")

    return FileResponse(path=file_path, filename=safe_name)


# ─────────────────────────────────────────────────────────────────────────────
# /journals
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/journals")
async def get_journals():
    try:
        import sys
        print("SYS PATH:", sys.path)
        print("PYTHONPATH ENV:", os.environ.get("PYTHONPATH"))
        from core.journal_profiles import get_journal_list, get_journal_profile
        print("IMPORT OK")
        journal_ids = get_journal_list()
        print("JOURNALS:", journal_ids)
        journals = []
        for jid in journal_ids:
            p = get_journal_profile(jid)
            if p:
                journals.append({
                    "id":                jid,
                    "name":              p.get("name", jid.title()),
                    "abstract_max_words": p.get("abstract_max_words", 150),
                    "citation_style":    p.get("reference_style", "alphabetical"),
                    "font":              p.get("font", "Times New Roman"),
                    "font_size":         p.get("font_size", 12),
                    "line_spacing":      p.get("line_spacing", 1.5),
                })
        return JSONResponse({
            "success": True,
            "data": {"available_journals": journals, "total": len(journals)},
        })
    except Exception as exc:
        import traceback
        print("EXCEPTION:", traceback.format_exc())
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})

@app.get("/journals/{journal_name}")
async def get_journal_details(journal_name: str):
    """Full formatting profile for a specific journal."""
    try:
        from core.journal_profiles import get_journal_list, get_journal_profile
        profile = get_journal_profile(journal_name)
        if not profile:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Journal '{journal_name}' not found."},
            )
        return JSONResponse({"success": True, "data": profile})
    except Exception as exc:
        return JSONResponse(status_code=400, content={"success": False, "error": str(exc)})


# ─────────────────────────────────────────────────────────────────────────────
# /health
# ─────────────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health_check():
    return JSONResponse({"status": "ok", "version": "1.0.0"})