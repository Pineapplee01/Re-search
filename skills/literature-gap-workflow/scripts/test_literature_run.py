import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("literature_run.py")
PREFLIGHT_SCRIPT = Path(__file__).parents[2] / "Re-search" / "scripts" / "preflight_run.py"


def run_script(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


def run_preflight(*args):
    return subprocess.run(
        [sys.executable, str(PREFLIGHT_SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class LiteratureRunTests(unittest.TestCase):
    def _ready_preflight(self, tmp: str, task: str = "Bounded research task") -> Path:
        init = run_preflight(
            "init",
            "--project-root",
            tmp,
            "--task",
            task,
            "--task-type",
            "research-question",
        )
        self.assertEqual(init.returncode, 0, init.stderr)
        payload = json.loads(init.stdout)
        run_dir = Path(payload["run_dir"])
        json_path = run_dir / "preflight.json"

        artifact = json.loads(json_path.read_text(encoding="utf-8"))
        artifact["status"] = "ready"
        artifact["problem_boundary"] = {
            "goal": "Define the search boundary before running the literature workflow.",
            "non_goals": ["Do not perform the full paper hunt in preflight."],
            "success_signal": "The workflow can inherit an explicit boundary and next skill.",
            "boundary_traps": ["Do not widen to unrelated misinformation problems."],
        }
        artifact["existing_solution_space"] = [
            {
                "ref_id": "R1",
                "source_category": "paper",
                "title": "Seed Research Paper",
                "url": "https://doi.org/10.1000/seed",
                "why_it_matters": "Provides a seed search pattern.",
                "quality_signals": ["top-tier venue"],
            },
            {
                "ref_id": "R2",
                "source_category": "paper-code",
                "title": "Seed Research Code",
                "url": "https://github.com/example/seed-code",
                "why_it_matters": "Provides artifact grounding for the search pattern.",
                "quality_signals": ["linked project code", "active repository"],
            }
        ]
        artifact["selected_reference_patterns"] = [
            {
                "ref_id": "R1",
                "reusable_pattern": "Use venue-first screening before deeper comparison.",
                "transfer_decision": "adapt",
                "boundary_limit": "Do not inherit the source paper's exact scope.",
            }
        ]
        artifact["comparison_axes"] = [
            "problem-boundary",
            "search-scope",
            "evidence-standard",
        ]
        artifact["migration_path"] = {
            "transfers_directly": ["Venue-first screening."],
            "needs_adaptation": ["Translate the seed pattern to the target topic."],
            "do_not_copy": ["Do not copy claims that were never validated in this project."],
        }
        artifact["boundary_risks"] = ["Scope drift during later search stages."]
        artifact["learning_steps"] = ["Read the seed artifact.", "Map its retrieval logic.", "Run the downstream workflow."]
        artifact["recommended_next_skill"] = {
            "skill": "literature-gap-workflow",
            "why": "The task is now bounded and ready for staged literature analysis.",
            "context_to_inherit": ["Keep the search bounded.", "Preserve venue-first logic."],
        }
        json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")
        return run_dir

    def test_init_defaults_to_balanced_and_standard(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "What is our default effort behavior?",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state = json.loads(Path(payload["state_path"]).read_text(encoding="utf-8"))

            self.assertEqual(state["effort"], "balanced")
            self.assertEqual(state["mode"], "standard")
            self.assertEqual(state["execution_profile"]["agent_strategy"], "single-agent")
            self.assertEqual(state["preflight"]["status"], "missing")

    def test_init_creates_research_wiki_when_missing(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "How does our risk method differ from recent work?",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run_dir = Path(payload["run_dir"])

            self.assertTrue((Path(tmp) / "research-wiki").is_dir())
            self.assertTrue(run_dir.is_dir())
            self.assertTrue((run_dir / "state.json").is_file())
            self.assertTrue((run_dir / "problem-map.md").is_file())
            self.assertTrue((run_dir / "baseline-snapshot.md").is_file())
            self.assertTrue((run_dir / "papers.json").is_file())
            self.assertTrue((run_dir / "difference-matrix.md").is_file())
            self.assertTrue((run_dir / "report.md").is_file())

    def test_init_reuses_existing_research_wiki(self):
        with tempfile.TemporaryDirectory() as tmp:
            wiki_dir = Path(tmp) / "research-wiki"
            wiki_dir.mkdir()

            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Map coordination detection papers",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            self.assertTrue(str(wiki_dir) in payload["run_dir"])

    def test_effort_lite_maps_to_quick(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Quick literature triage",
                "--effort",
                "lite",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state = json.loads(Path(payload["state_path"]).read_text(encoding="utf-8"))

            self.assertEqual(state["effort"], "lite")
            self.assertEqual(state["mode"], "quick")
            self.assertEqual(state["execution_profile"]["verification_strategy"], "single-pass")

    def test_effort_beast_maps_to_deep_with_multi_agent_cross_check(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Maximum-audit literature review",
                "--effort",
                "beast",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state = json.loads(Path(payload["state_path"]).read_text(encoding="utf-8"))

            self.assertEqual(state["effort"], "beast")
            self.assertEqual(state["mode"], "deep")
            self.assertEqual(state["execution_profile"]["agent_strategy"], "multi-agent-cross-check")
            self.assertEqual(state["execution_profile"]["verification_strategy"], "cross-check")

    def test_init_accepts_registered_preflight(self):
        with tempfile.TemporaryDirectory() as tmp:
            preflight_dir = self._ready_preflight(tmp, task="Use preflight during init")
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Use preflight during init",
                "--preflight",
                str(preflight_dir),
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state = json.loads(Path(payload["state_path"]).read_text(encoding="utf-8"))
            self.assertEqual(state["preflight"]["status"], "registered")
            self.assertEqual(state["preflight"]["task_type"], "research-question")
            self.assertEqual(state["preflight"]["recommended_next_skill"], "literature-gap-workflow")
            self.assertEqual(state["preflight"]["reference_count"], 2)
            self.assertIn("problem-boundary", state["preflight"]["comparison_axes"])
            self.assertTrue(state["preflight"]["preflight_json"].endswith("preflight.json"))

    def test_set_preflight_registers_ready_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Attach preflight later",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state_path = Path(payload["state_path"])

            preflight_dir = self._ready_preflight(tmp, task="Attach preflight later")
            set_result = run_script(
                "set-preflight",
                "--state-path",
                str(state_path),
                "--preflight",
                str(preflight_dir),
            )
            self.assertEqual(set_result.returncode, 0, set_result.stderr)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["preflight"]["status"], "registered")
            self.assertEqual(state["preflight"]["recommended_next_skill"], "literature-gap-workflow")

    def test_set_preflight_rejects_draft_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Reject draft preflight",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            state_path = Path(payload["state_path"])

            draft = run_preflight(
                "init",
                "--project-root",
                tmp,
                "--task",
                "Reject draft preflight",
                "--task-type",
                "research-question",
            )
            self.assertEqual(draft.returncode, 0, draft.stderr)
            preflight_payload = json.loads(draft.stdout)

            set_result = run_script(
                "set-preflight",
                "--state-path",
                str(state_path),
                "--preflight",
                preflight_payload["run_dir"],
            )
            self.assertNotEqual(set_result.returncode, 0)
            self.assertIn("status must be ready", set_result.stderr)

    def test_legacy_mode_argument_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Legacy mode input",
                "--mode",
                "deep",
            )

            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unrecognized arguments: --mode deep", result.stderr)

    def test_gate_blocks_hunt_before_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Compare our KT1 idea with prior work",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])

            blocked = run_script("assert-stage", "--state-path", str(state_path), "--stage", "hunt")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("requires completed stage: map", blocked.stderr)

    def test_gate_blocks_hunt_without_baseline_even_after_map(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Compare our coordination method with recent venue work",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])

            complete = run_script("complete-stage", "--state-path", str(state_path), "--stage", "map")
            self.assertEqual(complete.returncode, 0, complete.stderr)

            blocked = run_script("assert-stage", "--state-path", str(state_path), "--stage", "hunt")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("requires a provided baseline source", blocked.stderr)

    def test_completing_stage_unlocks_next_stage(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Compare our KT3 method with recent DISARM-style work",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])

            baseline = run_script(
                "set-baseline",
                "--state-path",
                str(state_path),
                "--source-type",
                "text",
                "--source-value",
                "KT3 focuses on phase-aware risk judgment with DISARM mapping.",
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)

            complete = run_script("complete-stage", "--state-path", str(state_path), "--stage", "map")
            self.assertEqual(complete.returncode, 0, complete.stderr)

            unlocked = run_script("assert-stage", "--state-path", str(state_path), "--stage", "hunt")
            self.assertEqual(unlocked.returncode, 0, unlocked.stderr)

    def test_complete_stage_blocks_hunt_without_baseline(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Do not bypass baseline gating",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])

            complete = run_script("complete-stage", "--state-path", str(state_path), "--stage", "map")
            self.assertEqual(complete.returncode, 0, complete.stderr)

            blocked = run_script("complete-stage", "--state-path", str(state_path), "--stage", "hunt")
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("requires a provided baseline source", blocked.stderr)

    def test_complete_stage_records_internal_mode_and_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Find venue papers about coordinated misinformation detection",
                "--effort",
                "beast",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])
            artifact_path = Path(payload["run_dir"]) / "problem-map.md"

            baseline = run_script(
                "set-baseline",
                "--state-path",
                str(state_path),
                "--source-type",
                "text",
                "--source-value",
                "We study coordinated misinformation detection with a phase-aware risk model.",
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)

            complete = run_script(
                "complete-stage",
                "--state-path",
                str(state_path),
                "--stage",
                "map",
                "--artifact",
                str(artifact_path),
            )
            self.assertEqual(complete.returncode, 0, complete.stderr)

            state = json.loads(state_path.read_text(encoding="utf-8"))
            self.assertEqual(state["mode"], "deep")
            self.assertEqual(state["effort"], "beast")
            self.assertEqual(state["stages"]["map"]["artifact"], str(artifact_path))
            self.assertEqual(state["stages"]["map"]["status"], "completed")

    def test_beast_hunt_completion_requires_accepted_jury_verdict(self):
        with tempfile.TemporaryDirectory() as tmp:
            init = run_script(
                "init-run",
                "--project-root",
                tmp,
                "--question",
                "Require accepted verdict before beast hunt completion",
                "--effort",
                "beast",
            )
            payload = json.loads(init.stdout)
            state_path = Path(payload["state_path"])
            run_dir = Path(payload["run_dir"])
            beast_dir = run_dir / "beast-hunt"
            beast_dir.mkdir()
            (beast_dir / "merge-report.json").write_text(
                json.dumps({"protocol_version": 1, "unique_paper_count": 10}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (beast_dir / "jury-input.json").write_text(
                json.dumps({"review_question": "ready?"}, ensure_ascii=False, indent=2),
                encoding="utf-8",
            )
            (beast_dir / "jury-verdict.json").write_text(
                json.dumps(
                    {
                        "protocol_version": 1,
                        "status": "pending",
                        "reviewer_type": "independent-reviewer",
                        "verdict": None,
                        "reasons": [],
                        "checked_at": None,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            baseline = run_script(
                "set-baseline",
                "--state-path",
                str(state_path),
                "--source-type",
                "text",
                "--source-value",
                "We study coordinated misinformation detection with phase-aware risk modeling.",
            )
            self.assertEqual(baseline.returncode, 0, baseline.stderr)

            complete_map = run_script("complete-stage", "--state-path", str(state_path), "--stage", "map")
            self.assertEqual(complete_map.returncode, 0, complete_map.stderr)

            blocked = run_script(
                "complete-stage",
                "--state-path",
                str(state_path),
                "--stage",
                "hunt",
                "--artifact",
                str(run_dir / "papers.json"),
            )
            self.assertNotEqual(blocked.returncode, 0)
            self.assertIn("accepted jury verdict", blocked.stderr)

            (beast_dir / "jury-verdict.json").write_text(
                json.dumps(
                    {
                        "protocol_version": 1,
                        "status": "completed",
                        "reviewer_type": "fresh-thread",
                        "verdict": "accepted",
                        "reasons": ["Cross-check passed"],
                        "checked_at": "2026-07-05T00:00:00Z",
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )

            completed = run_script(
                "complete-stage",
                "--state-path",
                str(state_path),
                "--stage",
                "hunt",
                "--artifact",
                str(run_dir / "papers.json"),
            )
            self.assertEqual(completed.returncode, 0, completed.stderr)


if __name__ == "__main__":
    unittest.main()
