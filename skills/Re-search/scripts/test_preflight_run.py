import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


SCRIPT = Path(__file__).with_name("preflight_run.py")


def run_script(*args):
    return subprocess.run(
        [sys.executable, str(SCRIPT), *args],
        capture_output=True,
        text=True,
        check=False,
    )


class PreflightRunTests(unittest.TestCase):
    def test_init_creates_dual_artifacts(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init",
                "--project-root",
                tmp,
                "--task",
                "Map strong skill patterns before refactor",
                "--task-type",
                "skill-implementation",
            )

            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            run_dir = Path(payload["run_dir"])
            self.assertTrue(run_dir.is_dir())
            self.assertTrue((run_dir / "preflight.json").is_file())
            self.assertTrue((run_dir / "preflight.md").is_file())

            artifact = json.loads((run_dir / "preflight.json").read_text(encoding="utf-8"))
            self.assertEqual(artifact["task_type"], "skill-implementation")
            self.assertEqual(artifact["recommended_next_skill"]["skill"], "request-refactor-plan")
            self.assertEqual(artifact["status"], "draft")

    def test_validate_accepts_ready_artifact(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init",
                "--project-root",
                tmp,
                "--task",
                "Compare our KT1 research with strong prior work",
                "--task-type",
                "research-question",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run_dir = Path(payload["run_dir"])
            json_path = run_dir / "preflight.json"

            artifact = json.loads(json_path.read_text(encoding="utf-8"))
            artifact["status"] = "ready"
            artifact["problem_boundary"] = {
                "goal": "Identify the literature boundary for KT1 coordination detection.",
                "non_goals": ["Do not design the final model in preflight."],
                "success_signal": "The downstream workflow can search with explicit venue and scope constraints.",
                "boundary_traps": ["Do not mix generic misinformation work with coordination detection."],
            }
            artifact["existing_solution_space"] = [
                {
                    "ref_id": "R1",
                    "source_category": "paper",
                    "title": "Coordination Detection in Social Networks",
                    "url": "https://doi.org/10.1000/example",
                    "why_it_matters": "Represents a high-level reference for the core task.",
                }
            ]
            artifact["selected_reference_patterns"] = [
                {
                    "ref_id": "R1",
                    "reusable_pattern": "Venue-first screening before detailed comparison.",
                    "transfer_decision": "adapt",
                    "boundary_limit": "Reuse the screening pattern, not the original problem framing.",
                }
            ]
            artifact["migration_path"] = {
                "transfers_directly": ["Carry over venue-first retrieval discipline."],
                "needs_adaptation": ["Shift from generic social analysis to CTI-oriented boundary language."],
                "do_not_copy": ["Do not copy the paper's threat model as our baseline."],
            }
            artifact["boundary_risks"] = ["Query drift toward broad misinformation work."]
            artifact["learning_steps"] = [
                "Read the seed papers.",
                "Inspect linked code and artifact pages.",
                "Translate the retrieval pattern into our workflow.",
            ]
            artifact["recommended_next_skill"] = {
                "skill": "literature-gap-workflow",
                "why": "The task is a research-question and now has a bounded handoff artifact.",
                "context_to_inherit": [
                    "Use the coordination-detection boundary exactly as stated.",
                    "Prefer venue-first search before citation expansion.",
                ],
            }
            artifact["updated_at"] = "2026-07-05T00:00:00Z"
            json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

            validate = run_script("validate", str(run_dir))
            self.assertEqual(validate.returncode, 0, validate.stderr)
            summary = json.loads(validate.stdout)
            self.assertEqual(summary["task_type"], "research-question")
            self.assertEqual(summary["recommended_next_skill"], "literature-gap-workflow")

    def test_validate_rejects_draft_by_default(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init",
                "--project-root",
                tmp,
                "--task",
                "Draft preflight should not pass",
                "--task-type",
                "tool-api",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)

            validate = run_script("validate", payload["run_dir"])
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("status must be ready", validate.stderr)

    def test_validate_rejects_missing_reference_url(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = run_script(
                "init",
                "--project-root",
                tmp,
                "--task",
                "Catch malformed references",
                "--task-type",
                "skill-implementation",
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            payload = json.loads(result.stdout)
            run_dir = Path(payload["run_dir"])
            json_path = run_dir / "preflight.json"

            artifact = json.loads(json_path.read_text(encoding="utf-8"))
            artifact["status"] = "ready"
            artifact["problem_boundary"] = {
                "goal": "Check malformed references.",
                "non_goals": ["Do not start coding yet."],
                "success_signal": "Validator catches missing URL structure.",
                "boundary_traps": ["Do not collapse source layers."],
            }
            artifact["existing_solution_space"] = [
                {
                    "ref_id": "R1",
                    "source_category": "github-skill",
                    "title": "Reference Skill",
                    "url": "not-a-url",
                    "why_it_matters": "Should fail validation.",
                }
            ]
            artifact["selected_reference_patterns"] = [
                {
                    "ref_id": "R1",
                    "reusable_pattern": "Use thin entry plus validators.",
                    "transfer_decision": "keep",
                    "boundary_limit": "Do not build a repo-wide runtime first.",
                }
            ]
            artifact["migration_path"] = {
                "transfers_directly": ["Thin entry plus validator."],
                "needs_adaptation": ["Adjust for project-local research-wiki output."],
                "do_not_copy": ["Do not copy unrelated repo abstractions."],
            }
            artifact["boundary_risks"] = ["URL quality is not enforced."]
            artifact["learning_steps"] = ["Read the skill.", "Map the reusable parts.", "Validate the artifact."]
            artifact["recommended_next_skill"] = {
                "skill": "request-refactor-plan",
                "why": "The artifact frames a skill-implementation task.",
                "context_to_inherit": ["Keep the scope on structure and validators first."],
            }
            json_path.write_text(json.dumps(artifact, ensure_ascii=False, indent=2), encoding="utf-8")

            validate = run_script("validate", str(json_path))
            self.assertNotEqual(validate.returncode, 0)
            self.assertIn("existing_solution_space[0].url", validate.stderr)


if __name__ == "__main__":
    unittest.main()
