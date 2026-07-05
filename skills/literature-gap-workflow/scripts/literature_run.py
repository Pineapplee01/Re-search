from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


# Static workflow protocol.
STAGE_ORDER = ("map", "hunt", "compare", "report")
EFFORT_TO_MODE = {
    "lite": "quick",
    "balanced": "standard",
    "max": "deep",
    "beast": "deep",
}
EFFORT_PROFILES = {
    "lite": {
        "agent_strategy": "single-agent",
        "verification_strategy": "single-pass",
        "search_depth": "light",
    },
    "balanced": {
        "agent_strategy": "single-agent",
        "verification_strategy": "single-pass",
        "search_depth": "standard",
    },
    "max": {
        "agent_strategy": "single-agent",
        "verification_strategy": "double-check",
        "search_depth": "deep",
    },
    "beast": {
        "agent_strategy": "multi-agent-cross-check",
        "verification_strategy": "cross-check",
        "search_depth": "deep",
    },
}
RUN_TEXT_DEFAULTS = {
    "problem-map.md": "# Problem Mapping\n\nPending `research-map`.\n",
    "baseline-snapshot.md": "# Baseline Snapshot\n\nPending `research-map`.\n",
    "difference-matrix.md": "# Difference Analysis\n\nPending `research-compare`.\n",
    "report.md": (
        "# Research Report\n\n"
        "## Problem Mapping\n\nPending.\n\n"
        "## Literature Search\n\nPending.\n\n"
        "## Difference Analysis\n\nPending.\n\n"
        "## Motivation\n\nPending.\n\n"
        "## Method\n\nPending.\n\n"
        "## Result\n\nPending.\n"
    ),
}
RUN_JSON_DEFAULTS = {
    "papers.json": "[]\n",
}
PREFLIGHT_SCRIPT = Path(__file__).resolve().parents[2] / "Re-search" / "scripts" / "preflight_run.py"


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def slugify(text: str) -> str:
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "-", text.strip().lower()).strip("-")
    return cleaned[:48] or "literature-run"


def ensure_file(path: Path, content: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    if not path.exists():
        path.write_text(content, encoding="utf-8")


def load_state(state_path: Path) -> dict[str, Any]:
    if not state_path.exists():
        raise FileNotFoundError(f"state file not found: {state_path}")
    return json.loads(state_path.read_text(encoding="utf-8"))


def save_state(state_path: Path, state: dict[str, Any]) -> None:
    state["updated_at"] = utc_now()
    state_path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")


def run_preflight_validator(preflight_path: Path) -> tuple[bool, str | None, dict[str, Any] | None]:
    if not PREFLIGHT_SCRIPT.exists():
        return False, f"preflight validator not found: {PREFLIGHT_SCRIPT}", None

    result = subprocess.run(
        [sys.executable, str(PREFLIGHT_SCRIPT), "validate", str(preflight_path)],
        capture_output=True,
        text=True,
        check=False,
    )
    if result.returncode != 0:
        message = result.stderr.strip() or result.stdout.strip() or "preflight validation failed"
        return False, message, None

    try:
        payload = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False, "preflight validator returned invalid JSON", None
    return True, None, payload


def registered_preflight_state(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "status": "registered",
        "preflight_json": payload["preflight_json"],
        "preflight_md": payload["preflight_md"],
        "task_type": payload["task_type"],
        "recommended_next_skill": payload["recommended_next_skill"],
        "comparison_axes": payload.get("comparison_axes", []),
        "reference_count": payload.get("reference_count"),
        "attached_at": utc_now(),
    }


def derive_execution_controls(effort: str | None) -> tuple[str, str, dict[str, str]]:
    resolved_effort = effort or "balanced"
    mode = EFFORT_TO_MODE[resolved_effort]
    return mode, resolved_effort, dict(EFFORT_PROFILES[resolved_effort])


def seed_run_artifacts(run_dir: Path) -> None:
    for name, content in RUN_TEXT_DEFAULTS.items():
        ensure_file(run_dir / name, content)
    for name, content in RUN_JSON_DEFAULTS.items():
        ensure_file(run_dir / name, content)


def build_initial_stage_state() -> dict[str, dict[str, str | None]]:
    return {
        stage: {
            "status": "pending",
            "artifact": None,
            "completed_at": None,
        }
        for stage in STAGE_ORDER
    }


def build_initial_state(
    *,
    question: str,
    project_root: Path,
    wiki_root: Path,
    run_id: str,
    run_dir: Path,
    effort: str,
    mode: str,
    profile: dict[str, str],
) -> dict[str, Any]:
    return {
        "version": 1,
        "question": question,
        "mode": mode,
        "effort": effort,
        "execution_profile": profile,
        "project_root": str(project_root),
        "wiki_root": str(wiki_root),
        "run_id": run_id,
        "run_dir": str(run_dir),
        "created_at": utc_now(),
        "updated_at": utc_now(),
        "preflight": {
            "status": "missing",
            "preflight_json": None,
            "preflight_md": None,
            "task_type": None,
            "recommended_next_skill": None,
            "attached_at": None,
        },
        "baseline": {
            "source_type": None,
            "source_value": None,
            "status": "missing",
        },
        "stages": build_initial_stage_state(),
    }


# Gate checks stay in this orchestrator; stage-specific executors should not replicate them.
def check_stage_gate(state: dict[str, Any], stage: str) -> tuple[bool, str | None]:
    if stage not in STAGE_ORDER:
        return False, f"unknown stage: {stage}"

    stage_index = STAGE_ORDER.index(stage)
    if stage_index > 0:
        required_stage = STAGE_ORDER[stage_index - 1]
        if state["stages"][required_stage]["status"] != "completed":
            return False, f"stage `{stage}` requires completed stage: {required_stage}"

    if stage == "hunt" and state["baseline"]["status"] != "provided":
        return False, "stage `hunt` requires a provided baseline source"

    return True, None


def check_beast_hunt_completion(state: dict[str, Any]) -> tuple[bool, str | None]:
    # This gate verifies artifact presence and accepted verdict state only.
    run_dir = Path(state["run_dir"]).resolve()
    beast_dir = run_dir / "beast-hunt"
    merge_report_path = beast_dir / "merge-report.json"
    jury_input_path = beast_dir / "jury-input.json"
    jury_verdict_path = beast_dir / "jury-verdict.json"

    if not merge_report_path.exists():
        return False, "beast hunt requires merge-report.json before completion"
    if not jury_input_path.exists():
        return False, "beast hunt requires jury-input.json before completion"
    if not jury_verdict_path.exists():
        return False, "beast hunt requires jury-verdict.json before completion"

    verdict = json.loads(jury_verdict_path.read_text(encoding="utf-8"))
    if verdict.get("status") != "completed" or verdict.get("verdict") != "accepted":
        return False, "beast hunt requires an accepted jury verdict before completion"
    reviewer_type = verdict.get("reviewer_type")
    if not isinstance(reviewer_type, str) or not reviewer_type.strip():
        return False, "beast hunt requires reviewer_type in jury verdict"
    checked_at = verdict.get("checked_at")
    if not isinstance(checked_at, str) or not checked_at.strip():
        return False, "beast hunt requires checked_at in jury verdict"

    return True, None


def gate_error_exit_code(error: str | None) -> int:
    if error and error.startswith("unknown stage:"):
        return 2
    return 1


# Command handlers.
def init_run(args: argparse.Namespace) -> int:
    mode, effort, profile = derive_execution_controls(args.effort)

    project_root = Path(args.project_root).resolve()
    wiki_root = project_root / "research-wiki"
    wiki_root.mkdir(parents=True, exist_ok=True)

    runs_root = wiki_root / "literature_runs"
    run_id = f"{datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%SZ')}-{slugify(args.question)}"
    run_dir = runs_root / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    seed_run_artifacts(run_dir)

    state = build_initial_state(
        question=args.question,
        project_root=project_root,
        wiki_root=wiki_root,
        run_id=run_id,
        run_dir=run_dir,
        effort=effort,
        mode=mode,
        profile=profile,
    )

    if args.preflight:
        ok, error, payload = run_preflight_validator(Path(args.preflight).resolve())
        if not ok:
            print(error, file=sys.stderr)
            return 1
        assert payload is not None
        state["preflight"] = registered_preflight_state(payload)

    state_path = run_dir / "state.json"
    save_state(state_path, state)

    print_json(
        {
            "run_id": run_id,
            "run_dir": str(run_dir),
            "state_path": str(state_path),
            "wiki_root": str(wiki_root),
        }
    )
    return 0


def assert_stage(args: argparse.Namespace) -> int:
    state = load_state(Path(args.state_path).resolve())
    ok, error = check_stage_gate(state, args.stage)
    if not ok:
        print(error, file=sys.stderr)
        return gate_error_exit_code(error)
    return 0


def complete_stage(args: argparse.Namespace) -> int:
    state_path = Path(args.state_path).resolve()
    state = load_state(state_path)
    ok, error = check_stage_gate(state, args.stage)
    if not ok:
        print(error, file=sys.stderr)
        return gate_error_exit_code(error)

    if args.stage == "hunt" and state.get("effort") == "beast":
        ok, error = check_beast_hunt_completion(state)
        if not ok:
            print(error, file=sys.stderr)
            return 1

    artifact = str(Path(args.artifact).resolve()) if args.artifact else None
    state["stages"][args.stage] = {
        "status": "completed",
        "artifact": artifact,
        "completed_at": utc_now(),
    }
    save_state(state_path, state)
    print_json({"stage": args.stage, "status": "completed", "artifact": artifact})
    return 0


def set_baseline(args: argparse.Namespace) -> int:
    state_path = Path(args.state_path).resolve()
    state = load_state(state_path)
    state["baseline"] = {
        "source_type": args.source_type,
        "source_value": args.source_value,
        "status": "provided",
    }
    save_state(state_path, state)
    print_json({"baseline": state["baseline"]})
    return 0


def set_preflight(args: argparse.Namespace) -> int:
    state_path = Path(args.state_path).resolve()
    state = load_state(state_path)
    ok, error, payload = run_preflight_validator(Path(args.preflight).resolve())
    if not ok:
        print(error, file=sys.stderr)
        return 1

    assert payload is not None
    state["preflight"] = registered_preflight_state(payload)
    save_state(state_path, state)
    print_json({"preflight": state["preflight"]})
    return 0


# CLI surface.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Manage literature workflow runs.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init-run")
    init_parser.add_argument("--project-root", required=True)
    init_parser.add_argument("--question", required=True)
    init_parser.add_argument("--effort", choices=["lite", "balanced", "max", "beast"])
    init_parser.add_argument("--preflight")
    init_parser.set_defaults(func=init_run)

    assert_parser = subparsers.add_parser("assert-stage")
    assert_parser.add_argument("--state-path", required=True)
    assert_parser.add_argument("--stage", required=True)
    assert_parser.set_defaults(func=assert_stage)

    complete_parser = subparsers.add_parser("complete-stage")
    complete_parser.add_argument("--state-path", required=True)
    complete_parser.add_argument("--stage", required=True)
    complete_parser.add_argument("--artifact")
    complete_parser.set_defaults(func=complete_stage)

    baseline_parser = subparsers.add_parser("set-baseline")
    baseline_parser.add_argument("--state-path", required=True)
    baseline_parser.add_argument("--source-type", choices=["path", "text"], required=True)
    baseline_parser.add_argument("--source-value", required=True)
    baseline_parser.set_defaults(func=set_baseline)

    preflight_parser = subparsers.add_parser("set-preflight")
    preflight_parser.add_argument("--state-path", required=True)
    preflight_parser.add_argument("--preflight", required=True)
    preflight_parser.set_defaults(func=set_preflight)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
