"""
Discovery Agent: fetch journal rules using Crossref + Groq.
"""

import asyncio
import json
import os
from typing import Dict, Optional

import requests
from bs4 import BeautifulSoup
from groq import Groq


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
    """
    Look up a journal via the Crossref API and return the first result.
    """
    url = f"{CROSSREF_BASE}/works"
    params = {"query.container-title": journal_name, "rows": 1}
    try:
        resp = requests.get(url, params=params, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("message", {}).get("items", [])
        if not items:
            return {}
        return items[0]
    except Exception:
        return {}


def _fetch_page_text(url: str) -> str:
    """
    Fetch and clean text content from a journal guidelines page.
    """
    if not url:
        return ""
    try:
        resp = requests.get(url, timeout=20)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.text, "html.parser")
        for tag in soup(["script", "style", "noscript"]):
            tag.extract()
        return _clean_text(soup.get_text(separator="\n"))
    except Exception:
        return ""


def _groq_extract_rules(
    journal_name: str,
    source_url: str,
    page_text: str,
    api_key: Optional[str] = None,
) -> Dict:
    """
    Use Groq (Llama 3.3 70B) to extract formatting rules from journal page text.
    Falls back to DEFAULT_RULES if API key is missing or call fails.
    """
    key = api_key or os.getenv("GROQ_API_KEY", "")

    if not key:
        return {
            **DEFAULT_RULES,
            "journal": journal_name,
            "source_url": source_url,
            "status": "missing_api_key",
        }

    client = Groq(api_key=key)

    prompt = f"""You are a journal formatting analyst.

Extract the author instructions and return ONLY valid JSON with this exact schema.
No explanation, no markdown, no backticks — just the JSON object:

{{
  "csl_style": "apa",
  "font": "Times New Roman",
  "spacing": "double",
  "margins": "1-inch"
}}

Rules:
- If the page is not clearly an author instruction page, infer the likely style from the journal name.
- Do not add extra keys.
- csl_style must be one of: apa, vancouver, harvard, ieee, chicago, mla, nature, science

Journal: {journal_name}
Source URL: {source_url}

Page Text:
{page_text[:12000]}"""

    try:
        response = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[{"role": "user", "content": prompt}],
            response_format={"type": "json_object"},
            temperature=0.1,
        )

        text = response.choices[0].message.content.strip()

        try:
            rules = json.loads(text)
        except Exception:
            # If JSON parsing fails, fall back to defaults
            rules = DEFAULT_RULES.copy()
            rules["raw_output"] = text[:1000]

    except Exception as e:
        rules = DEFAULT_RULES.copy()
        rules["error"] = str(e)

    # Merge with defaults so all keys are always present
    rules = {**DEFAULT_RULES, **rules}
    rules["journal"] = journal_name
    rules["source_url"] = source_url
    rules["status"] = "success"

    return rules


async def get_journal_rules(journal_name: str, style_url: Optional[str] = None) -> Dict:
    """
    Async discovery of journal formatting rules using Crossref + Groq.

    Steps:
    1. If style_url is provided, use it directly.
    2. Otherwise, look up the journal on Crossref to find its URL.
    3. Fetch the page text from that URL.
    4. Send page text to Groq to extract structured formatting rules.

    Args:
        journal_name: Name of the journal (e.g. "nature", "ieee")
        style_url: Optional direct URL to the journal's author guidelines page.

    Returns:
        Dictionary with keys: csl_style, font, spacing, margins, journal, source_url, status
    """

    def _sync() -> Dict:
        # Step 1: Determine the journal URL
        journal_url = ""
        if style_url:
            journal_url = style_url
        else:
            journal_data = _crossref_journal_lookup(journal_name)
            journal_url = journal_data.get("URL") or ""

        # Step 2: Fetch page content
        page_text = ""
        if journal_url:
            page_text = _fetch_page_text(journal_url)

        # Step 3: Extract rules with Groq
        return _groq_extract_rules(journal_name, journal_url, page_text)

    return await asyncio.to_thread(_sync)