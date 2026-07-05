import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


BEAST_SCRIPT = Path(__file__).with_name("beast_hunt.py")
RUNNER_SCRIPT = Path(__file__).parents[2] / "literature-gap-workflow" / "scripts" / "literature_run.py"


def run_beast(*args):
    return subprocess.run(
        [sys.executable, str(BEAST_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def run_runner(*args):
    return subprocess.run(
        [sys.executable, str(RUNNER_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


PROBLEM_MAP = """# Problem Mapping

### Core Queries
1. `coordinated misinformation detection`
2. `campaign detection social media`
3. `disinformation network analysis`

### Expansion Queries
1. `coordination detection threat intelligence`
2. `misinformation campaign lifecycle analysis`

### Exclusion-Enforced Queries
1. `coordinated misinformation detection NOT marketing`
2. `campaign detection social media NOT advertising`
"""


def write_lane_file(path: Path, lane_id: str, papers: list[dict]):
    payload = {
        "lane_id": lane_id,
        "purpose": "test",
        "query_group": "core_queries",
        "queries": [],
        "required_sources": [],
        "status": "completed",
        "completed_at": "2026-07-05T00:00:00Z",
        "papers": papers,
        "summary": "ok",
    }
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


class BeastHuntTests(unittest.TestCase):
    def _init_beast_run(self, tmp: str) -> tuple[Path, Path]:
        init = run_runner(
            "init-run",
            "--project-root",
            tmp,
            "--question",
            "Beast mode literature retrieval",
            "--effort",
            "beast",
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        payload = json.loads(init.stdout)
        state_path = Path(payload["state_path"])
        problem_map_path = Path(payload["run_dir"]) / "problem-map.md"
        problem_map_path.write_text(PROBLEM_MAP, encoding="utf-8")
        baseline = run_runner(
            "set-baseline",
            "--state-path",
            str(state_path),
            "--source-type",
            "text",
            "--source-value",
            "We study coordinated misinformation detection.",
        )
        self.assertEqual(baseline.returncode, 0, baseline.stderr)
        complete = run_runner("complete-stage", "--state-path", str(state_path), "--stage", "map")
        self.assertEqual(complete.returncode, 0, complete.stderr)
        return state_path, problem_map_path

    def test_init_creates_beast_lane_plan(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path, problem_map_path = self._init_beast_run(tmp)
            result = run_beast("init", "--state-path", str(state_path), "--problem-map", str(problem_map_path))
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            lane_plan = json.loads(Path(payload["lane_plan_path"]).read_text(encoding="utf-8"))
            lane_ids = [lane["lane_id"] for lane in lane_plan["lanes"]]
            self.assertEqual(
                lane_ids,
                ["venue-first", "citation-expansion", "boundary-challenger", "artifact-verifier"],
            )

    def test_merge_combines_duplicate_papers_across_lanes(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path, problem_map_path = self._init_beast_run(tmp)
            init = run_beast("init", "--state-path", str(state_path), "--problem-map", str(problem_map_path))
            payload = json.loads(init.stdout)
            lanes_dir = Path(payload["lanes_dir"])

            shared_paper = {
                "title": "Unified Campaign Detection",
                "authors": ["A", "B"],
                "year": 2025,
                "venue": "ICWSM",
                "venue_type": "conference",
                "article_url": "https://doi.org/10.1000/unified",
                "code_url": None,
                "dataset_urls": [],
                "source": "semantic-scholar",
                "why_relevant": "core match",
                "is_primary_evidence": True,
                "artifact_search_notes": "checked DOI page",
                "doi": "10.1000/unified",
            }
            shared_paper_with_artifacts = dict(shared_paper)
            shared_paper_with_artifacts["code_url"] = "https://github.com/example/unified"
            shared_paper_with_artifacts["dataset_urls"] = ["https://example.org/unified-dataset"]
            shared_paper_with_artifacts["source"] = "openalex"
            shared_paper_with_artifacts["artifact_search_notes"] = "checked repo and dataset page"

            write_lane_file(lanes_dir / "venue-first.json", "venue-first", [shared_paper])
            write_lane_file(lanes_dir / "citation-expansion.json", "citation-expansion", [shared_paper_with_artifacts])
            write_lane_file(
                lanes_dir / "boundary-challenger.json",
                "boundary-challenger",
                [
                    {
                        "title": "Adjacent Campaign Typology",
                        "authors": ["C"],
                        "year": 2024,
                        "venue": "WWW",
                        "venue_type": "conference",
                        "article_url": "https://arxiv.org/abs/2401.00001",
                        "code_url": None,
                        "dataset_urls": [],
                        "source": "web-search",
                        "why_relevant": "boundary paper",
                        "is_primary_evidence": False,
                        "artifact_search_notes": "checked arXiv page",
                    }
                ],
            )
            write_lane_file(lanes_dir / "artifact-verifier.json", "artifact-verifier", [shared_paper_with_artifacts])

            merge = run_beast("merge", "--state-path", str(state_path))
            self.assertEqual(merge.returncode, 0, merge.stderr)
            report = json.loads(merge.stdout)
            self.assertEqual(report["unique_paper_count"], 2)
            papers = json.loads((Path(json.loads(Path(state_path).read_text(encoding="utf-8"))["run_dir"]) / "papers.json").read_text(encoding="utf-8"))
            merged = next(paper for paper in papers if paper["title"] == "Unified Campaign Detection")
            self.assertEqual(merged["code_url"], "https://github.com/example/unified")
            self.assertEqual(merged["dataset_urls"], ["https://example.org/unified-dataset"])
            self.assertEqual(merged["crosscheck_status"], "confirmed_by_multiple_lanes")

    def test_jury_ready_requires_artifact_lane_and_multilane_confirmation(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path, problem_map_path = self._init_beast_run(tmp)
            init = run_beast("init", "--state-path", str(state_path), "--problem-map", str(problem_map_path))
            payload = json.loads(init.stdout)
            lanes_dir = Path(payload["lanes_dir"])

            paper = {
                "title": "Only One Lane",
                "authors": ["A"],
                "year": 2025,
                "venue": "ICLR",
                "venue_type": "conference",
                "article_url": "https://doi.org/10.1000/one",
                "code_url": None,
                "dataset_urls": [],
                "source": "semantic-scholar",
                "why_relevant": "one lane only",
                "is_primary_evidence": True,
                "artifact_search_notes": "checked DOI page",
                "doi": "10.1000/one",
            }
            write_lane_file(lanes_dir / "venue-first.json", "venue-first", [paper])
            write_lane_file(lanes_dir / "citation-expansion.json", "citation-expansion", [dict(paper, doi="10.1000/two", article_url="https://doi.org/10.1000/two", title="Second Paper")])
            write_lane_file(lanes_dir / "boundary-challenger.json", "boundary-challenger", [dict(paper, doi="10.1000/three", article_url="https://doi.org/10.1000/three", title="Third Paper")])
            write_lane_file(lanes_dir / "artifact-verifier.json", "artifact-verifier", [dict(paper, doi="10.1000/four", article_url="https://doi.org/10.1000/four", title="Fourth Paper")])

            merge = run_beast("merge", "--state-path", str(state_path))
            self.assertEqual(merge.returncode, 0, merge.stderr)

            ready = run_beast("jury-ready", "--state-path", str(state_path))
            self.assertNotEqual(ready.returncode, 0)
            self.assertIn("confirmed by multiple lanes", ready.stderr)

    def test_record_verdict_writes_completed_jury_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            state_path, problem_map_path = self._init_beast_run(tmp)
            init = run_beast("init", "--state-path", str(state_path), "--problem-map", str(problem_map_path))
            payload = json.loads(init.stdout)
            beast_dir = Path(payload["beast_dir"])
            verdict_path = Path(payload["jury_verdict_path"])
            (beast_dir / "merge-report.json").write_text(
                json.dumps({"protocol_version": 1, "unique_paper_count": 10}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (beast_dir / "jury-input.json").write_text(
                json.dumps({"review_question": "ready?"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )

            record = run_beast(
                "record-verdict",
                "--state-path",
                str(state_path),
                "--reviewer-type",
                "fresh-thread",
                "--verdict",
                "accepted",
                "--reason",
                "Broad venue coverage",
                "--reason",
                "Artifact metadata checked",
            )
            self.assertEqual(record.returncode, 0, record.stderr)

            verdict = json.loads(verdict_path.read_text(encoding="utf-8"))
            self.assertEqual(verdict["status"], "completed")
            self.assertEqual(verdict["reviewer_type"], "fresh-thread")
            self.assertEqual(verdict["verdict"], "accepted")
            self.assertEqual(verdict["reasons"], ["Broad venue coverage", "Artifact metadata checked"])

            asserted = run_beast("assert-verdict", "--state-path", str(state_path))
            self.assertEqual(asserted.returncode, 0, asserted.stderr)


if __name__ == "__main__":
    unittest.main()
