__all__ = [
    "ManuscriptParser",
    "StyleAgent",
    "CitationAgent",
    "ManuscriptFormatter",
    "ChangeLog",
    "ManuscriptExporter",
    "get_journal_list",
    "get_journal_profile",
    "JOURNAL_PROFILES",
    "get_journal_rules",
    "markdown_to_docx",
]


def __getattr__(name):
    if name == "ManuscriptParser":
        from .parser import ManuscriptParser
        return ManuscriptParser
    if name == "StyleAgent":
        from .agents import StyleAgent
        return StyleAgent
    if name == "CitationAgent":
        from .agents import CitationAgent
        return CitationAgent
    if name == "ManuscriptFormatter":
        from .formatter import ManuscriptFormatter
        return ManuscriptFormatter
    if name == "ChangeLog":
        from .changelog import ChangeLog
        return ChangeLog
    if name == "ManuscriptExporter":
        from .export import ManuscriptExporter
        return ManuscriptExporter
    if name == "get_journal_list":
        from .journal_profiles import get_journal_list
        return get_journal_list
    if name == "get_journal_profile":
        from .journal_profiles import get_journal_profile
        return get_journal_profile
    if name == "JOURNAL_PROFILES":
        from .journal_profiles import JOURNAL_PROFILES
        return JOURNAL_PROFILES
    if name == "get_journal_rules":
        from .discovery import get_journal_rules
        return get_journal_rules
    if name == "markdown_to_docx":
        from .transformer import markdown_to_docx
        return markdown_to_docx
    raise AttributeError(f"module 'core' has no attribute {name}")


def __dir__():
    return sorted(__all__)
