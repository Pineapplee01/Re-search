import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("validate_papers_json.py")


def run_validator(path: Path):
    return subprocess.run(
        [sys.executable, str(SCRIPT), str(path)],
        capture_output=True,
        text=True,
        check=False,
    )


class ValidatePapersJsonTests(unittest.TestCase):
    def test_accepts_required_article_code_and_dataset_fields(self):
        payload = [
            {
                "paper_id": "P01",
                "title": "Phase-Aware Detection of Coordinated Content",
                "authors": ["A", "B"],
                "year": 2025,
                "venue": "ICLR",
                "venue_type": "conference",
                "article_url": "https://doi.org/10.1000/example",
                "code_url": "https://github.com/example/project",
                "dataset_urls": ["https://example.org/dataset"],
                "source": "semantic-scholar",
                "why_relevant": "Matches the mapped task and evidence style.",
                "is_primary_evidence": True,
                "artifact_search_notes": "Checked DOI page and project repo.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "papers.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result = run_validator(path)

            self.assertEqual(result.returncode, 0, result.stderr)
            self.assertIn("papers.json is valid", result.stdout)

    def test_requires_article_url(self):
        payload = [
            {
                "paper_id": "P01",
                "title": "Missing article URL",
                "authors": ["A"],
                "year": 2025,
                "venue": "NeurIPS",
                "venue_type": "conference",
                "article_url": "",
                "code_url": None,
                "dataset_urls": [],
                "source": "openalex",
                "why_relevant": "Relevant.",
                "is_primary_evidence": False,
                "artifact_search_notes": "Checked venue and author pages.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "papers.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result = run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("article_url", result.stderr)

    def test_requires_code_and_dataset_fields_even_when_missing(self):
        payload = [
            {
                "paper_id": "P01",
                "title": "Missing artifact fields",
                "authors": ["A"],
                "year": 2025,
                "venue": "WWW",
                "venue_type": "conference",
                "article_url": "https://arxiv.org/abs/2501.00001",
                "source": "semantic-scholar",
                "why_relevant": "Relevant.",
                "is_primary_evidence": True,
                "artifact_search_notes": "Checked paper page only.",
            }
        ]

        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "papers.json"
            path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
            result = run_validator(path)

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("code_url", result.stderr)
            self.assertIn("dataset_urls", result.stderr)


if __name__ == "__main__":
    unittest.main()
