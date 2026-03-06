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
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))

EXPORTS_DIR = REPO_ROOT / "exports"
EXPORTS_DIR.mkdir(parents=True, exist_ok=True)


class TransformPayload(BaseModel):
    manuscript: Dict[str, Any]
    journal: Optional[str] = None
    template: Optional[str] = None
    style_url: Optional[str] = None


def _build_markdown(manuscript: Dict[str, Any], references_text: str) -> str:
    title = manuscript.get("metadata", {}).get("title", "Manuscript")
    abstract = manuscript.get("abstract", "")
    body = manuscript.get("body", "")

    md = f"# {title}\n\n"
    if abstract:
        md += "## Abstract\n\n" + abstract.strip() + "\n\n"
    md += body.strip() + "\n\n"
    if references_text:
        md += "## References\n\n" + references_text.strip() + "\n"
    return md

from core.parser import ManuscriptParser
from core.discovery import get_journal_rules
from core.export import ManuscriptExporter
from core.transformer import markdown_to_docx
from core.validator import validate_transformation
from utils.helpers import (
    identify_section_headers,
    calculate_compliance_score,
    extract_in_text_citations
)
from backend.utils.templates import get_template_path

# Initialize FastAPI app
app = FastAPI(
    title="Manuscript Formatting Agent",
    description="A modular API for parsing and formatting manuscripts with AI-powered agents",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize exporters (agents and parser are lazy to avoid heavy startup)
exporter = ManuscriptExporter()
_style_agent = None
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


@app.post("/parse")
async def parse_manuscript(file: UploadFile = File(...)):
    """
    Parse an uploaded PDF or DOCX manuscript and extract structured content.
    
    Returns:
        JSON with keys: metadata, abstract, body, references, section_headers, compliance_score
    """
    try:
        print(f"GOOGLE_API_KEY: {os.getenv('GOOGLE_API_KEY')}")
        # Save uploaded file to temporary location
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
            contents = await file.read()
            tmp.write(contents)
            tmp_path = tmp.name
        
        # Parse the manuscript
        parser = ManuscriptParser()
        parsed_data = parser.parse(tmp_path)
        
        # Extract section headers
        section_headers = identify_section_headers(parsed_data.get("body", ""))
        
        # Calculate compliance score
        compliance = calculate_compliance_score(
            metadata=parsed_data.get("metadata", {}),
            abstract=parsed_data.get("abstract", ""),
            body=parsed_data.get("body", ""),
            references=parsed_data.get("references", "")
        )
        
        # Extract in-text citations
        citations = extract_in_text_citations(parsed_data.get("body", ""))
        
        # Clean up temporary file
        os.unlink(tmp_path)
        
        return JSONResponse({
            "success": True,
            "data": {
                "metadata": parsed_data.get("metadata", {}),
                "abstract": parsed_data.get("abstract", ""),
                "body": parsed_data.get("body", ""),
                "references": parsed_data.get("references", ""),
                "section_headers": section_headers,
                "in_text_citations": citations,
                "compliance_score": compliance,
            }
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={
                "success": False,
                "error": str(e)
            }
        )


@app.post("/transform-manuscript")
async def transform_manuscript(
    request: Request,
    journal: str = Query(..., description="Journal name"),
    file: UploadFile = File(None),
    template: Optional[str] = Query(None, description="Reference DOCX template path"),
    style_url: Optional[str] = Query(None, description="Optional journal style URL override"),
):
    """
    Transform a manuscript using discovery rules, CSL citeproc, and Pandoc.

    Accepts either:
    - Multipart file upload (PDF/DOCX), or
    - JSON body with a 'manuscript' object.
    """
    correction_log = []
    citation_validation = {}

    try:
        # Step 1: Acquire structured manuscript
        if file is not None:
            with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as tmp:
                contents = await file.read()
                tmp.write(contents)
                tmp_path = tmp.name
            parser = ManuscriptParser()
            manuscript = parser.parse(tmp_path)
            os.unlink(tmp_path)
            correction_log.append("Parsed manuscript file into structured JSON.")
        else:
            body_json = await request.json()
            if isinstance(body_json, dict) and "manuscript" in body_json:
                payload = TransformPayload(**body_json)
                manuscript = payload.manuscript
                if payload.journal:
                    journal = payload.journal
                if payload.template:
                    template = payload.template
                if payload.style_url:
                    style_url = payload.style_url
            else:
                manuscript = body_json
            correction_log.append("Loaded structured manuscript JSON from request.")

        # Step 2: Discover journal rules (Crossref + Gemini)
        rules = await get_journal_rules(journal, style_url=style_url)
        csl_style = rules.get("csl_style", "apa")
        correction_log.append(f"Applied discovered CSL style: {csl_style}.")
        if rules.get("font"):
            correction_log.append(f"Target font: {rules.get('font')}.")
        if rules.get("spacing"):
            correction_log.append(f"Target spacing: {rules.get('spacing')}.")
        if rules.get("margins"):
            correction_log.append(f"Target margins: {rules.get('margins')}.")
        
        # Step 3: Validate Citations
        body = manuscript.get("body", "")
        references = manuscript.get("references", [])
        if isinstance(references, str):
            references = [{"id": f"ref{i+1}", "title": line} for i, line in enumerate(references.splitlines()) if line.strip()]

        try:
            citation_agent = get_citation_agent()
            citation_validation = citation_agent.validate_citations(body, references)
            correction_log.append("Citation validation completed.")
            if not citation_validation.get("valid"):
                correction_log.append("Citation issues found. See 'citation_validation' for details.")
        except Exception as e:
            correction_log.append(f"Citation validation failed: {str(e)}")


        # Step 4: CSL engine (citeproc-py)
        bibliography_text = ""
        new_body = body
        try:
            new_body, bibliography_text, csl_log = render_citations_with_csl(
                body=body,
                references=references,
                csl_style=csl_style,
            )
            correction_log.extend(csl_log)
        except Exception as csl_error:
            correction_log.append(f"CSL engine failed: {str(csl_error)}. Preserved original citations.")

        if not bibliography_text:
            if isinstance(references, str) and references.strip():
                bibliography_text = references.strip()
            elif isinstance(references, list):
                bibliography_text = "\n".join(str(r) for r in references if str(r).strip()).strip()

        # Step 5: Pandoc transform
        final_markdown = _build_markdown(manuscript, bibliography_text)
        if new_body and new_body != body:
            final_markdown = _build_markdown(
                {**manuscript, "body": new_body},
                bibliography_text,
            )

        template_path = Path(template) if template else get_template_path(journal)

        filename = f"{journal.lower()}_transformed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.docx"
        output_path = EXPORTS_DIR / filename

        markdown_to_docx(
            markdown_text=final_markdown,
            output_path=output_path,
            reference_doc=template_path,
            use_citeproc=True,
        )
        correction_log.append("Generated DOCX via Pandoc using reference template.")

        # Step 6: Sanity Check Transformation
        transformation_validation = validate_transformation(
            original_markdown=final_markdown,
            docx_path=output_path
        )
        correction_log.append("Performed sanity check on the generated document.")

        return JSONResponse({
            "success": True,
            "data": {
                "journal": journal.upper(),
                "file_path": str(output_path),
                "download_url": f"/export-file/{journal.lower()}/{filename}",
                "correction_log": correction_log,
                "discovered_rules": rules,
                "citation_validation": citation_validation,
                "transformation_validation": transformation_validation,
            }
        })

    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/export-file/{journal_name}/{filename}")
async def export_file(journal_name: str, filename: str):
    """
    Download a formatted manuscript file from the exports directory.
    """
    safe_name = Path(filename).name
    expected_prefix = f"{journal_name.lower()}_"

    if not safe_name.lower().startswith(expected_prefix):
        raise HTTPException(
            status_code=400,
            detail="Filename does not match journal"
        )

    file_path = (EXPORTS_DIR / safe_name).resolve()

    if EXPORTS_DIR not in file_path.parents and file_path != EXPORTS_DIR:
        raise HTTPException(
            status_code=400,
            detail="Invalid file path"
        )

    if not file_path.exists():
        raise HTTPException(
            status_code=404,
            detail="File not found"
        )

    return FileResponse(path=file_path, filename=safe_name)


@app.get("/journals")
async def get_journals():
    """
    Get list of all available journals.
    
    Returns:
        JSON with available_journals list containing full journal objects
    """
    try:
        journal_ids = get_journal_list()
        journals = []
        
        for journal_id in journal_ids:
            profile = get_journal_profile(journal_id)
            if profile:
                journals.append({
                    "id": journal_id,
                    "name": profile.get("name", journal_id.title()),
                    "abstract_max_words": profile.get("abstract_max_words", 150),
                    "citation_style": profile.get("reference_style", "alphabetical"),
                    "font": profile.get("font", "Arial"),
                    "font_size": profile.get("font_size", 11),
                    "line_spacing": profile.get("line_spacing", 1.0),
                })
        
        return JSONResponse({
            "success": True,
            "data": {
                "available_journals": journals,
                "total": len(journals)
            }
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/journals/{journal_name}")
async def get_journal_details(journal_name: str):
    """
    Get detailed formatting profile for a specific journal.
    
    Parameters:
        journal_name: Name of the journal (e.g., 'nature', 'ieee', 'acm')
    
    Returns:
        Complete journal formatting requirements
    """
    try:
        profile = get_journal_profile(journal_name)
        
        if not profile:
            return JSONResponse(
                status_code=404,
                content={"success": False, "error": f"Journal '{journal_name}' not found"}
            )
        
        return JSONResponse({
            "success": True,
            "data": profile
        })
    
    except Exception as e:
        return JSONResponse(
            status_code=400,
            content={"success": False, "error": str(e)}
        )


@app.get("/health")
async def health_check():
    """
    Health check endpoint.
    """
    return {"status": "healthy", "service": "Manuscript Formatting Agent"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)
