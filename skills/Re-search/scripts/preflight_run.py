from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


TASK_TYPES = ("research-question", "skill-implementation", "tool-api")
READY_STATUSES = ("draft", "ready")
SOURCE_CATEGORIES = {
    "github-skill",
    "implementation-repo",
    "paper",
    "paper-code",
    "project-page",
    "dataset-page",
    "official-doc",
    "official-example",
    "release-note",
    "issue-discussion",
    "community-repo",
}
TRANSFER_DECISIONS = {"keep", "adapt", "reject"}
REQUIRED_MARKDOWN_SECTIONS = (
    "## task_type",
    "## problem_boundary",
    "## existing_solution_space",
    "## selected_reference_patterns",
    "## migration_path",
    "## boundary_risks",
    "## learning_steps",
    "## recommended_next_skill",
)
DEFAULT_SOURCE_LAYERS = {
    "research-question": ["paper", "paper-code", "project-page", "dataset-page", "implementation-repo"],
    "skill-implementation": ["github-skill", "implementation-repo", "official-doc", "paper"],
    "tool-api": ["official-doc", "official-example", "release-note", "issue-discussion", "community-repo"],
}


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned[:48] or "preflight"


def is_http_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def load_json(path: Path) -> Any:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def non_empty_string_list(value: object) -> bool:
    return isinstance(value, list) and bool(value) and all(isinstance(item, str) and item.strip() for item in value)


def template_dir() -> Path:
    return Path(__file__).resolve().parents[1] / "references"


def render_markdown_template(*, run_id: str, task: str, task_type: str, next_skill: str) -> str:
    template = (template_dir() / "preflight-template.md").read_text(encoding="utf-8")
    header = (
        "# Preflight Artifact\n\n"
        f"- run_id: `{run_id}`\n"
        f"- task: `{task}`\n"
        f"- task_type: `{task_type}`\n"
        f"- suggested_next_skill: `{next_skill}`\n\n"
    )
    template_body = template.replace("# Preflight Artifact\n\n", "", 1)
    return header + template_body


def default_next_skill(task_type: str) -> str:
    if task_type == "research-question":
        return "literature-gap-workflow"
    if task_type == "skill-implementation":
        return "request-refactor-plan"
    return "openai-docs"


def build_initial_payload(*, run_id: str, task: str, task_type: str, project_root: Path, markdown_path: Path) -> dict[str, Any]:
    next_skill = default_next_skill(task_type)
    return {
        "protocol_version": 1,
        "status": "draft",
        "run_id": run_id,
        "task": task,
        "task_slug": slugify(task),
        "task_type": task_type,
        "project_root": str(project_root),
        "artifact_markdown": str(markdown_path),
        "source_layer": {
            "task_type": task_type,
            "preferred_categories": DEFAULT_SOURCE_LAYERS[task_type],
        },
        "problem_boundary": {
            "goal": "",
            "non_goals": [],
            "success_signal": "",
            "boundary_traps": [],
        },
        "existing_solution_space": [],
        "selected_reference_patterns": [],
        "migration_path": {
            "transfers_directly": [],
            "needs_adaptation": [],
            "do_not_copy": [],
        },
        "boundary_risks": [],
        "learning_steps": [],
        "recommended_next_skill": {
            "skill": next_skill,
            "why": "",
            "context_to_inherit": [],
        },
        "created_at": utc_now(),
        "updated_at": utc_now(),
    }


def resolve_artifact_paths(target: Path) -> tuple[Path, Path]:
    resolved = target.resolve()
    if resolved.is_dir():
        return resolved / "preflight.json", resolved / "preflight.md"
    if resolved.name == "preflight.json":
        return resolved, resolved.with_name("preflight.md")
    if resolved.name == "preflight.md":
        return resolved.with_name("preflight.json"), resolved
    raise ValueError(f"target must be a preflight run dir or preflight artifact path: {resolved}")


def validate_markdown(path: Path) -> list[str]:
    if not path.exists():
        return [f"preflight markdown not found: {path}"]

    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for section in REQUIRED_MARKDOWN_SECTIONS:
        if section not in text:
            errors.append(f"preflight.md missing section: {section}")
    return errors


def validate_reference_entry(entry: object, index: int, seen_ids: set[str]) -> list[str]:
    prefix = f"existing_solution_space[{index}]"
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]

    ref_id = entry.get("ref_id")
    if not isinstance(ref_id, str) or not ref_id.strip():
        errors.append(f"{prefix}.ref_id must be a non-empty string")
    elif ref_id in seen_ids:
        errors.append(f"{prefix}.ref_id duplicates an earlier reference: {ref_id}")
    else:
        seen_ids.add(ref_id)

    source_category = entry.get("source_category")
    if source_category not in SOURCE_CATEGORIES:
        errors.append(f"{prefix}.source_category must be one of: {', '.join(sorted(SOURCE_CATEGORIES))}")

    for field in ("title", "why_it_matters"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")

    if not is_http_url(entry.get("url")):
        errors.append(f"{prefix}.url must be an http(s) URL")
    return errors


def validate_pattern_entry(entry: object, index: int, known_refs: set[str]) -> list[str]:
    prefix = f"selected_reference_patterns[{index}]"
    errors: list[str] = []
    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]

    ref_id = entry.get("ref_id")
    if not isinstance(ref_id, str) or not ref_id.strip():
        errors.append(f"{prefix}.ref_id must be a non-empty string")
    elif ref_id not in known_refs:
        errors.append(f"{prefix}.ref_id must refer to existing_solution_space")

    for field in ("reusable_pattern", "boundary_limit"):
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")

    decision = entry.get("transfer_decision")
    if decision not in TRANSFER_DECISIONS:
        errors.append(f"{prefix}.transfer_decision must be one of: {', '.join(sorted(TRANSFER_DECISIONS))}")
    return errors


def validate_required_metadata(payload: dict[str, Any], *, markdown_path: Path, require_ready: bool) -> list[str]:
    errors: list[str] = []
    if payload.get("protocol_version") != 1:
        errors.append("protocol_version must be 1")

    status = payload.get("status")
    if status not in READY_STATUSES:
        errors.append("status must be one of: draft, ready")
    elif require_ready and status != "ready":
        errors.append("status must be ready for downstream handoff")

    for field in ("run_id", "task", "task_slug", "project_root", "artifact_markdown", "created_at", "updated_at"):
        value = payload.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{field} must be a non-empty string")

    task_type = payload.get("task_type")
    if task_type not in TASK_TYPES:
        errors.append("task_type must be one of: research-question, skill-implementation, tool-api")

    artifact_markdown = payload.get("artifact_markdown")
    if isinstance(artifact_markdown, str) and artifact_markdown.strip():
        expected_markdown = str(markdown_path.resolve())
        if str(Path(artifact_markdown).resolve()) != expected_markdown:
            errors.append("artifact_markdown must point to the sibling preflight.md")
    return errors


def validate_source_layer(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    task_type = payload.get("task_type")
    source_layer = payload.get("source_layer")
    if not isinstance(source_layer, dict):
        errors.append("source_layer must be an object")
        return errors

    if source_layer.get("task_type") != task_type:
        errors.append("source_layer.task_type must match task_type")
    preferred_categories = source_layer.get("preferred_categories")
    if not non_empty_string_list(preferred_categories):
        errors.append("source_layer.preferred_categories must be a non-empty list of strings")
    return errors


def validate_problem_boundary(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    problem_boundary = payload.get("problem_boundary")
    if not isinstance(problem_boundary, dict):
        errors.append("problem_boundary must be an object")
        return errors

    goal = problem_boundary.get("goal")
    if not isinstance(goal, str) or not goal.strip():
        errors.append("problem_boundary.goal must be a non-empty string")
    success_signal = problem_boundary.get("success_signal")
    if not isinstance(success_signal, str) or not success_signal.strip():
        errors.append("problem_boundary.success_signal must be a non-empty string")
    if not non_empty_string_list(problem_boundary.get("non_goals")):
        errors.append("problem_boundary.non_goals must be a non-empty list of strings")
    if not non_empty_string_list(problem_boundary.get("boundary_traps")):
        errors.append("problem_boundary.boundary_traps must be a non-empty list of strings")
    return errors


def validate_solution_space(payload: dict[str, Any]) -> tuple[list[str], set[str]]:
    errors: list[str] = []
    seen_refs: set[str] = set()
    existing_solution_space = payload.get("existing_solution_space")
    if not isinstance(existing_solution_space, list) or not existing_solution_space:
        errors.append("existing_solution_space must be a non-empty list")
    else:
        for index, entry in enumerate(existing_solution_space):
            errors.extend(validate_reference_entry(entry, index, seen_refs))
    return errors, seen_refs


def validate_selected_patterns(payload: dict[str, Any], *, known_refs: set[str]) -> list[str]:
    errors: list[str] = []
    selected_reference_patterns = payload.get("selected_reference_patterns")
    if not isinstance(selected_reference_patterns, list) or not selected_reference_patterns:
        errors.append("selected_reference_patterns must be a non-empty list")
    else:
        for index, entry in enumerate(selected_reference_patterns):
            errors.extend(validate_pattern_entry(entry, index, known_refs))
    return errors


def validate_migration_path(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    migration_path = payload.get("migration_path")
    if not isinstance(migration_path, dict):
        errors.append("migration_path must be an object")
    else:
        for field in ("transfers_directly", "needs_adaptation", "do_not_copy"):
            if not non_empty_string_list(migration_path.get(field)):
                errors.append(f"migration_path.{field} must be a non-empty list of strings")
    return errors


def validate_boundary_risks_and_learning_steps(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not non_empty_string_list(payload.get("boundary_risks")):
        errors.append("boundary_risks must be a non-empty list of strings")
    if not non_empty_string_list(payload.get("learning_steps")):
        errors.append("learning_steps must be a non-empty list of strings")
    return errors


def validate_recommended_next_skill(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    recommended_next_skill = payload.get("recommended_next_skill")
    if not isinstance(recommended_next_skill, dict):
        errors.append("recommended_next_skill must be an object")
        return errors

    skill_name = recommended_next_skill.get("skill")
    if not isinstance(skill_name, str) or not skill_name.strip():
        errors.append("recommended_next_skill.skill must be a non-empty string")
    why = recommended_next_skill.get("why")
    if not isinstance(why, str) or not why.strip():
        errors.append("recommended_next_skill.why must be a non-empty string")
    if not non_empty_string_list(recommended_next_skill.get("context_to_inherit")):
        errors.append("recommended_next_skill.context_to_inherit must be a non-empty list of strings")
    return errors


def validate_payload(payload: object, *, markdown_path: Path, require_ready: bool) -> list[str]:
    errors = validate_markdown(markdown_path)
    if not isinstance(payload, dict):
        return errors + ["preflight.json must be a JSON object"]

    errors.extend(validate_required_metadata(payload, markdown_path=markdown_path, require_ready=require_ready))
    errors.extend(validate_source_layer(payload))
    errors.extend(validate_problem_boundary(payload))
    solution_space_errors, seen_refs = validate_solution_space(payload)
    errors.extend(solution_space_errors)
    errors.extend(validate_selected_patterns(payload, known_refs=set(seen_refs)))
    errors.extend(validate_migration_path(payload))
    errors.extend(validate_boundary_risks_and_learning_steps(payload))
    errors.extend(validate_recommended_next_skill(payload))
    return errors


def init_preflight(args: argparse.Namespace) -> int:
    project_root = Path(args.project_root).resolve()
    runs_root = project_root / "research-wiki" / "preflight_runs"
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(args.task)}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=False)

    markdown_path = run_dir / "preflight.md"
    json_path = run_dir / "preflight.json"

    next_skill = default_next_skill(args.task_type)
    markdown_path.write_text(
        render_markdown_template(run_id=run_id, task=args.task, task_type=args.task_type, next_skill=next_skill),
        encoding="utf-8",
    )
    write_json(
        json_path,
        build_initial_payload(
            run_id=run_id,
            task=args.task,
            task_type=args.task_type,
            project_root=project_root,
            markdown_path=markdown_path.resolve(),
        ),
    )

    print_json(
        {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "preflight_json": str(json_path),
            "preflight_md": str(markdown_path),
        }
    )
    return 0


def validate_preflight(args: argparse.Namespace) -> int:
    json_path, markdown_path = resolve_artifact_paths(Path(args.target))
    try:
        payload = load_json(json_path)
    except FileNotFoundError:
        print(f"preflight json not found: {json_path}", file=sys.stderr)
        return 1
    except json.JSONDecodeError as exc:
        print(f"invalid JSON: {exc}", file=sys.stderr)
        return 1

    errors = validate_payload(payload, markdown_path=markdown_path, require_ready=not args.allow_draft)
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        return 1

    print_json(
        {
            "valid": True,
            "run_id": payload["run_id"],
            "task_type": payload["task_type"],
            "recommended_next_skill": payload["recommended_next_skill"]["skill"],
            "preflight_json": str(json_path.resolve()),
            "preflight_md": str(markdown_path.resolve()),
        }
    )
    return 0


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage Re-search preflight artifacts.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--project-root", required=True)
    init_parser.add_argument("--task", required=True)
    init_parser.add_argument("--task-type", choices=TASK_TYPES, required=True)
    init_parser.set_defaults(func=init_preflight)

    validate_parser = subparsers.add_parser("validate")
    validate_parser.add_argument("target", help="Preflight run directory, preflight.json, or preflight.md")
    validate_parser.add_argument("--allow-draft", action="store_true")
    validate_parser.set_defaults(func=validate_preflight)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
