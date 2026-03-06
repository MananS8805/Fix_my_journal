import os
import json
import re
import requests
from bs4 import BeautifulSoup
from groq import Groq
from typing import Optional, List, Dict
import collections


class StyleAgent:
    """
    Agent responsible for extracting journal formatting rules
    from a webpage using Groq LLM.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.client = Groq(api_key=api_key or os.getenv("GROQ_API_KEY"))

    def _fetch_page_content(self, url: str) -> str:
        """
        Fetch and clean webpage text from a URL.
        """
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()

            soup = BeautifulSoup(response.text, "html.parser")

            # Remove scripts and styles
            for script in soup(["script", "style"]):
                script.extract()

            text = soup.get_text(separator="\n")
            text = "\n".join(line.strip() for line in text.splitlines() if line.strip())

            return text

        except Exception as e:
            raise RuntimeError(f"Failed to fetch page content: {str(e)}")

    def extract_formatting_rules(self, url: str) -> Dict:
        """
        Extract formatting rules from a journal guideline page.
        """
        try:
            page_text = self._fetch_page_content(url)

            prompt = f"""You are an academic formatting expert.

Extract manuscript formatting guidelines from the text below.

Return ONLY valid JSON with this exact structure, no explanation, no markdown, no backticks:

{{
  "citation_style": "",
  "abstract_word_limit": "",
  "heading_structure": "",
  "reference_style": "",
  "figure_caption_style": "",
  "table_format": "",
  "font": "",
  "font_size": "",
  "line_spacing": ""
}}

TEXT:
{page_text[:12000]}"""

            response = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[{"role": "user", "content": prompt}],
                response_format={"type": "json_object"},
                temperature=0.1,
            )

            try:
                rules = json.loads(response.choices[0].message.content)
            except Exception:
                rules = {"raw_output": response.choices[0].message.content}

            return {
                "source": url,
                "rules": rules,
                "status": "success"
            }

        except Exception as e:
            return {
                "source": url,
                "rules": None,
                "status": "error",
                "message": str(e)
            }


class CitationAgent:
    """
    Agent responsible for validating citations against a reference list.
    Uses pure Python regex — no AI needed.
    """

    def __init__(self):
        pass

    def _extract_citekeys(self, body: str) -> List[str]:
        """
        Extract all unique citekeys from the manuscript body.
        A citekey is the identifier used in [@citekey].
        """
        cite_pattern = re.compile(r"\[@([^\]]+)\]")
        matches = cite_pattern.findall(body)

        all_keys = set()
        for match in matches:
            keys = [key.strip().lstrip('@') for key in match.split(';')]
            for key in keys:
                if key:
                    all_keys.add(key)
        return list(all_keys)

    def validate_citations(self, body: str, references: List[Dict]) -> Dict:
        """
        Validate in-text citations against a list of CSL-JSON references.

        Args:
            body: The manuscript body text containing [@citekey] citations.
            references: A list of reference dictionaries in CSL-JSON format.
                        Each dictionary MUST have an "id" key.

        Returns:
            A dictionary containing the validation results.
        """

        cited_keys = self._extract_citekeys(body)
        reference_ids = {ref.get("id") for ref in references if ref.get("id")}

        missing_references = [key for key in cited_keys if key not in reference_ids]
        unused_references = [ref_id for ref_id in reference_ids if ref_id not in cited_keys]

        # Basic duplicate check based on ID
        all_ref_ids = [ref.get("id") for ref in references if ref.get("id")]
        duplicates = [
            item for item, count in collections.Counter(all_ref_ids).items() if count > 1
        ]

        is_valid = not missing_references and not duplicates

        suggestions = []
        for key in missing_references:
            suggestions.append({
                "issue": "Missing Reference",
                "citation": key,
                "suggestion": (
                    f"The citation '[@{key}]' is present in the text, but no corresponding "
                    f"entry was found in the reference list. Please add a reference with the ID '{key}'."
                )
            })

        for ref_id in unused_references:
            suggestions.append({
                "issue": "Unused Reference",
                "citation": ref_id,
                "suggestion": (
                    f"The reference with ID '{ref_id}' is in the reference list but does not "
                    f"appear to be cited in the text. Consider removing it or adding a citation '[@{ref_id}]'."
                )
            })

        for dup_id in duplicates:
            suggestions.append({
                "issue": "Duplicate Reference ID",
                "citation": dup_id,
                "suggestion": (
                    f"The reference ID '{dup_id}' is used for multiple entries in the reference list. "
                    f"Reference IDs must be unique."
                )
            })

        return {
            "total_citations_in_text": len(cited_keys),
            "total_references_in_list": len(reference_ids),
            "missing_references": missing_references,
            "unused_references": unused_references,
            "duplicates": duplicates,
            "valid": is_valid,
            "suggestions": suggestions
        }