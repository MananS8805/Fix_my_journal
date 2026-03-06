Place your reference DOCX templates here.

Example:
- templates/apa.docx
- templates/apa7.docx
- templates/journal_template.docx

The /transform endpoint uses:
1) the template passed in the request (if any),
2) templates/{csl_style}.docx (if it exists),
3) templates/journal_template.docx as fallback.
