import google.generativeai as genai
from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional
import os

# Define the structured output using Pydantic models
class Section(BaseModel):
    heading: str = Field(description="The heading of the section.")
    content: str = Field(description="The full text content of the section.")
    font_size: Optional[int] = Field(None, description="Average font size of the section content.")
    font_style: Optional[str] = Field(None, description="Dominant font style (e.g., 'bold', 'italic').")

class Table(BaseModel):
    caption: str = Field(description="The caption of the table.")
    content: List[List[str]] = Field(description="The table content as a 2D JSON array.")
    page: int = Field(description="The page number where the table is found.")

class Manuscript(BaseModel):
    title: str = Field(description="The primary title of the manuscript.")
    abstract: str = Field(description="The complete abstract of the manuscript.")
    sections: List[Section] = Field(description="A list of all sections in the document.")
    tables: List[Table] = Field(description="A list of all tables extracted from the document.")
    citations: List[str] = Field(description="A list of all bibliographic citations or references.")
    keywords: List[str] = Field(description="A list of keywords associated with the manuscript.")

class ManuscriptParser:
    """
    A parser that uses Gemini for multimodal document understanding to extract
    structured information from scientific manuscripts.
    """
    def __init__(self, api_key: Optional[str] = None):
        """
        Initializes the Gemini client.
        Requires GOOGLE_API_KEY to be set as an environment variable if api_key is not provided.
        """
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY")
        if not self.api_key:
            raise ValueError("GOOGLE_API_KEY environment variable not set.")
        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel(model_name="gemini-2.0-flash")

    def parse(self, source: str) -> Dict[str, Any]:
        """
        Parses a document (PDF or Word file) using the Gemini API.

        Args:
            source: The local file path to the manuscript.

        Returns:
            A dictionary with the structured content of the manuscript,
            formatted to be compatible with downstream agents.
        """
        print(f"Starting parsing for: {source}")

        # 1. Upload the file to Gemini
        uploaded_file = genai.upload_file(path=source)
        print(f"Successfully uploaded file: {uploaded_file.uri}")

        # 2. Prompt Gemini for structured extraction
        prompt = f"""
Analyze the layout and semantic structure of the document provided and return a JSON object that strictly follows the provided `Manuscript` schema.

- For the `sections` field, identify each distinct section by its heading and include the full content.
- For the `tables` field, extract the caption and represent the table as a JSON array.
- For the `citations` field, list all entries from the bibliography or references section.
- Also, try to infer 'hidden' metadata like font size or style where possible.
"""
        
        # 3. Generate content using the model
        try:
            response = self.model.generate_content(
                [uploaded_file, prompt],
                generation_config=genai.types.GenerationConfig(
                    response_mime_type="application/json",
                )
            )
            
            # 4. Parse the JSON output into our Pydantic model
            structured_data = Manuscript.model_validate_json(response.text)
            
            # 5. Convert to the format expected by downstream agents
            return self._to_legacy_format(structured_data)

        except Exception as e:
            print(f"An error occurred during Gemini processing: {e}")
            return {"error": str(e)}
        finally:
            # Clean up the uploaded file
            genai.delete_file(uploaded_file.name)
            print(f"Cleaned up file: {uploaded_file.name}")

    def _to_legacy_format(self, manuscript: Manuscript) -> Dict[str, Any]:
        """
        Converts the structured `Manuscript` object into the dictionary format
        expected by `CitationAgent` and `ManuscriptExporter`.
        """
        # Combine sections into a single 'body' string
        body_content = "\n\n".join([f"## {s.heading}\n{s.content}" for s in manuscript.sections])
        
        # Format references as a simple string
        references_text = "\n".join(manuscript.citations)
        
        # Tables and figures are not explicitly handled in the old format,
        # but we can pass them along if needed. For now, we'll omit them.

        return {
            "metadata": {
                "title": manuscript.title,
                "authors": [],  # Author extraction is not part of the new schema yet
                "keywords": manuscript.keywords,
            },
            "abstract": manuscript.abstract,
            "body": body_content,
            "references": references_text,
            "figures": [], # Placeholder
            "tables": [table.model_dump_json() for table in manuscript.tables], # Pass as JSON strings
        }