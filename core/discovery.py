"""
Discovery Agent: fetch journal rules using Crossref + Gemini.
"""

import asyncio
import json
import os
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
import google.generativeai as genai


CROSSREF_BASE = "https://api.crossref.org"
DEFAULT_RULES = {
    "csl_style": "apa",
    "font": "Times New Roman",
    "spacing": "double",
    "margins": "1-inch",
}


def _clean_text(text: str) -> str:
    return "\n".join(line.strip() for line in text.splitlines() if line.strip())


def _crossref_journal_lookup(journal_name: str) -> Dict:
    url = f"{CROSSREF_BASE}/works"
    params = {"query.container-title": journal_name, "rows": 1}
    resp = requests.get(url, params=params, timeout=15)
    resp.raise_for_status()
    data = resp.json()
    items = data.get("message", {}).get("items", [])
    if not items:
        return {}
    return items[0]


def _fetch_page_text(url: str) -> str:
    if not url:
        return ""
    resp = requests.get(url, timeout=20)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.extract()
    return _clean_text(soup.get_text(separator="\n"))


def _gemini_extract_rules(
    journal_name: str,
    source_url: str,
    page_text: str,
    api_key: Optional[str],
) -> Dict:
    key = api_key or os.getenv("GEMINI_API_KEY", "")
    if not key:
        return {
            **DEFAULT_RULES,
            "journal": journal_name,
            "source_url": source_url,
            "status": "missing_api_key",
        }

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    prompt = f"""
You are a journal formatting analyst.

Extract the author instructions and return ONLY valid JSON with this schema:
{{
  "csl_style": "apa",
  "font": "Times New Roman",
  "spacing": "double",
  "margins": "1-inch"
}}

Rules:
- If the page is not clearly an author instruction page, infer the likely style from the journal name.
- Do not add extra keys.

Journal: {journal_name}
Source URL: {source_url}

Page Text:
{page_text[:12000]}
""".strip()

    response = model.generate_content(prompt)
    text = (response.text or "").strip()

    try:
        rules = json.loads(text)
    except Exception:
        rules = DEFAULT_RULES.copy()
        rules["raw_output"] = text[:1000]

    rules = {**DEFAULT_RULES, **rules}
    rules["journal"] = journal_name
    rules["source_url"] = source_url
    rules["status"] = "success"
    return rules


async def get_journal_rules(journal_name: str, style_url: Optional[str] = None) -> Dict:
    """
    Async discovery of journal rules using Crossref + Gemini.
    """

    def _sync() -> Dict:
        journal_url = ""
        if style_url:
            journal_url = style_url
        else:
            journal_data = _crossref_journal_lookup(journal_name)
            journal_url = journal_data.get("URL") or ""

        page_text = ""
        if journal_url:
            page_text = _fetch_page_text(journal_url)
        return _gemini_extract_rules(journal_name, journal_url, page_text, None)

    return await asyncio.to_thread(_sync)
