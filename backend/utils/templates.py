from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[2]
TEMPLATES_DIR = REPO_ROOT / "templates"

def get_template_path(journal_name: str) -> Path:
    """
    Get the path to the .docx template for a given journal.

    Args:
        journal_name: The name of the journal.

    Returns:
        The path to the .docx template.
    """
    journal_template_path = TEMPLATES_DIR / f"{journal_name.lower()}.docx"
    if journal_template_path.exists():
        return journal_template_path
    
    return TEMPLATES_DIR / "default.docx"
