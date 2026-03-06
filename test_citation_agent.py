import unittest
import os
import sys

# Ensure repo root is on sys.path
REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if REPO_ROOT not in sys.path:
    sys.path.insert(0, REPO_ROOT)

from core.agents import CitationAgent
from core.formatter import render_citations_with_csl

class TestCitationProcessing(unittest.TestCase):

    def setUp(self):
        self.agent = CitationAgent()
        self.sample_body = """
        This is a sentence with a citation [@smith2020].
        This sentence has multiple citations [@jones2021; @brown2022].
        This is another sentence with a citation that is not in the reference list [@davis2023].
        """
        self.sample_references = [
            {
                "id": "smith2020",
                "type": "article-journal",
                "title": "A paper by Smith",
                "author": [{"family": "Smith", "given": "J."}],
                "issued": {"date-parts": [[2020]]}
            },
            {
                "id": "jones2021",
                "type": "article-journal",
                "title": "A paper by Jones",
                "author": [{"family": "Jones", "given": "K."}],
                "issued": {"date-parts": [[2021]]}
            },
            {
                "id": "brown2022",
                "type": "article-journal",
                "title": "A paper by Brown",
                "author": [{"family": "Brown", "given": "L."}],
                "issued": {"date-parts": [[2022]]}
            },
            {
                "id": "unused2024",
                "type": "article-journal",
                "title": "An unused paper",
                "author": [{"family": "Nobody", "given": "A."}],
                "issued": {"date-parts": [[2024]]}
            }
        ]

    def test_citation_validation(self):
        """Test the validation of citations against a reference list."""
        validation = self.agent.validate_citations(self.sample_body, self.sample_references)

        self.assertFalse(validation["valid"])
        self.assertEqual(validation["total_citations_in_text"], 4)
        self.assertEqual(validation["total_references_in_list"], 4)
        self.assertEqual(validation["missing_references"], ["davis2023"])
        self.assertEqual(validation["unused_references"], ["unused2024"])
        self.assertEqual(len(validation["suggestions"]), 2)

    def test_csl_rendering(self):
        """Test the rendering of citations and bibliography."""
        new_body, bibliography, log = render_citations_with_csl(
            self.sample_body,
            self.sample_references,
            "apa"
        )

        self.assertIn("(Smith, 2020)", new_body)
        self.assertIn("(Jones, 2021; Brown, 2022)", new_body)
        self.assertIn("This is another sentence with a citation that is not in the reference list", new_body) # Should not be replaced

        self.assertIn("Brown, L. (2022).", bibliography)
        self.assertIn("Jones, K. (2021).", bibliography)
        self.assertIn("Smith, J. (2020).", bibliography)
        self.assertIn("Nobody, A. (2024).", bibliography) # The unused reference should still be in the bibliography if rendered

if __name__ == "__main__":
    unittest.main()
