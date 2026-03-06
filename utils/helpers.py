import re
from typing import List, Dict, Tuple


def identify_section_headers(text: str) -> List[str]:
    """
    Identify section headers (Introduction, Methods, Results, etc.) using regex.
    
    Args:
        text: Document text to search
        
    Returns:
        List of detected section headers
    """
    # Pattern to match common section headers
    section_patterns = [
        r'(?i)^#+\s*(Introduction|Background)',
        r'(?i)^#+\s*(Methods|Methodology)',
        r'(?i)^#+\s*(Results)',
        r'(?i)^#+\s*(Discussion)',
        r'(?i)^#+\s*(Conclusion|Conclusions)',
        r'(?i)^#+\s*(References|Bibliography)',
        r'(?i)^#+\s*(Abstract)',
        r'(?i)^#+\s*(Keywords)',
    ]
    
    found_headers = []
    for pattern in section_patterns:
        matches = re.finditer(pattern, text, re.MULTILINE)
        for match in matches:
            found_headers.append(match.group(0).strip())
    
    return found_headers


def calculate_compliance_score(
    metadata: Dict,
    abstract: str,
    body: str,
    references: str,
    required_sections: List[str] = None
) -> Dict:
    """
    Calculate a compliance score based on missing structural elements.
    
    Args:
        metadata: Document metadata dict
        abstract: Abstract section text
        body: Body section text
        references: References section text
        required_sections: List of required section headers (default: standard sections)
        
    Returns:
        Dictionary containing compliance score and missing elements
    """
    if required_sections is None:
        required_sections = [
            "Introduction",
            "Methods",
            "Results",
            "Discussion",
            "References"
        ]
    
    checks = {
        "has_metadata": bool(metadata and metadata.get("title")),
        "has_abstract": len(abstract.strip()) > 50,
        "has_body": len(body.strip()) > 200,
        "has_references": len(references.strip()) > 50,
    }
    
    # Check for required sections
    body_lower = body.lower()
    sections_found = []
    missing_sections = []
    
    for section in required_sections:
        if re.search(rf"(?i)#+\s*{section}", body):
            sections_found.append(section)
        else:
            missing_sections.append(section)
    
    # Calculate compliance score (0-100)
    total_checks = len(checks) + len(required_sections)
    passed_checks = sum(checks.values()) + len(sections_found)
    compliance_score = (passed_checks / total_checks) * 100 if total_checks > 0 else 0
    
    return {
        "compliance_score": round(compliance_score, 2),
        "total_checks": total_checks,
        "passed_checks": passed_checks,
        "element_checks": checks,
        "sections_found": sections_found,
        "missing_sections": missing_sections,
    }


def extract_in_text_citations(text: str) -> List[Tuple[str, int]]:
    """
    Extract in-text citations from document body using the [@key] format.
    
    Args:
        text: Document text
        
    Returns:
        List of tuples (citation_key, count)
    """
    # Pattern to match citations like [@key1] or [@key1; @key2]
    cite_pattern = re.compile(r"\[@([^\]]+)\]")
    matches = cite_pattern.findall(text)
    
    from collections import Counter
    
    all_keys = []
    for match in matches:
        keys = [key.strip() for key in match.split(';')]
        all_keys.extend(keys)
        
    citation_counts = Counter(all_keys)
    
    return sorted(citation_counts.items(), key=lambda x: x[1], reverse=True)
