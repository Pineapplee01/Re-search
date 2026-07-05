from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from validate_papers_json import validate_file


# Static beast-hunt protocol.
LANE_SPECS = [
    {
        "lane_id": "venue-first",
        "purpose": "Search core queries against top venues and publisher pages.",
        "query_group": "core_queries",
        "required_sources": ["semantic-scholar", "openalex", "publisher-pages"],
    },
    {
        "lane_id": "citation-expansion",
        "purpose": "Start from strong seeds and expand through citations, references, and related-work chains.",
        "query_group": "expansion_queries",
        "required_sources": ["openalex", "semantic-scholar"],
    },
    {
        "lane_id": "boundary-challenger",
        "purpose": "Use exclusion-enforced queries to test scope edges and catch near-miss papers.",
        "query_group": "exclusion_queries",
        "required_sources": ["semantic-scholar", "web-search"],
    },
    {
        "lane_id": "artifact-verifier",
        "purpose": "Verify article links, official code repositories, and public dataset pages for candidate papers.",
        "query_group": "artifact_queries",
        "required_sources": ["publisher-pages", "project-pages", "official-repos", "dataset-pages"],
    },
]
REQUIRED_LANE_PAPER_FIELDS = (
    "title",
    "authors",
    "year",
    "venue",
    "venue_type",
    "article_url",
    "source",
    "why_relevant",
    "is_primary_evidence",
    "artifact_search_notes",
)
JURY_REVIEW_QUESTION = (
    "Is this beast-mode paper set broad, source-grounded, and internally "
    "cross-checked enough to enter difference analysis?"
)
MIN_COMPLETED_LANES = 3
MIN_UNIQUE_PAPERS = 10
MIN_MULTI_LANE_CONFIRMATIONS = 4


def utc_now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def print_json(payload: Any) -> None:
    print(json.dumps(payload, ensure_ascii=False))


def load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def slug_key(value: str) -> str:
    value = value.lower()
    value = re.sub(r"https?://", "", value)
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def resolve_beast_dir(state: dict[str, Any], beast_dir: str | None) -> Path:
    if beast_dir:
        return Path(beast_dir).resolve()
    return Path(state["run_dir"]).resolve() / "beast-hunt"


# Problem-map parsing and lane planning.
def extract_section_lines(text: str, heading: str) -> list[str]:
    lines = text.splitlines()
    target = heading.lower().strip()
    capture = False
    collected: list[str] = []
    for line in lines:
        stripped = line.strip()
        if stripped.startswith("### "):
            current = stripped[4:].strip().lower()
            if capture and current != target:
                break
            capture = current == target
            continue
        if capture and stripped:
            collected.append(stripped)
    return collected


def parse_problem_map(problem_map_path: Path) -> dict[str, list[str]]:
    text = problem_map_path.read_text(encoding="utf-8")
    query_groups = {
        "core_queries": extract_section_lines(text, "Core Queries"),
        "expansion_queries": extract_section_lines(text, "Expansion Queries"),
        "exclusion_queries": extract_section_lines(text, "Exclusion-Enforced Queries"),
    }

    artifact_queries: list[str] = []
    for item in query_groups["core_queries"][:2] + query_groups["expansion_queries"][:2]:
        cleaned = re.sub(r"^(\d+\.\s*|-\s*)", "", item).strip("`")
        if cleaned:
            artifact_queries.append(f"{cleaned} code repository dataset")
    query_groups["artifact_queries"] = artifact_queries or ["official project repository dataset"]
    return query_groups


def build_lane_plan(state: dict[str, Any], problem_map_path: Path) -> dict[str, Any]:
    query_groups = parse_problem_map(problem_map_path)
    lanes = [
        {
            "lane_id": spec["lane_id"],
            "purpose": spec["purpose"],
            "query_group": spec["query_group"],
            "queries": query_groups.get(spec["query_group"], []),
            "required_sources": spec["required_sources"],
            "status": "pending",
            "notes": "",
        }
        for spec in LANE_SPECS
    ]
    return {
        "protocol_version": 1,
        "generated_at": utc_now(),
        "effort": state["effort"],
        "question": state["question"],
        "lanes": lanes,
    }


def default_lane_file(lane: dict[str, Any]) -> dict[str, Any]:
    return {
        "lane_id": lane["lane_id"],
        "purpose": lane["purpose"],
        "query_group": lane["query_group"],
        "queries": lane["queries"],
        "required_sources": lane["required_sources"],
        "status": "pending",
        "completed_at": None,
        "papers": [],
        "summary": "",
    }


def default_jury_verdict() -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "status": "pending",
        "reviewer_type": "independent-reviewer",
        "verdict": None,
        "reasons": [],
        "checked_at": None,
    }


def require_beast_effort(state: dict[str, Any], *, action: str) -> tuple[bool, str | None]:
    if state.get("effort") != "beast":
        return False, f"{action} requires effort=beast"
    return True, None


def resolve_lanes_dir(beast_dir: Path) -> Path:
    return beast_dir / "lanes"


def required_verdict_artifacts(beast_dir: Path) -> list[Path]:
    return [
        beast_dir / "merge-report.json",
        beast_dir / "jury-input.json",
        beast_dir / "jury-verdict.json",
    ]


def missing_paths(paths: list[Path]) -> list[str]:
    return [str(path) for path in paths if not path.exists()]


# Initialization command.
def init_beast(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state_path).resolve())
    ok, error = require_beast_effort(state, action="beast-hunt init")
    if not ok:
        assert error is not None
        print(error, file=sys.stderr)
        return 1

    beast_dir = resolve_beast_dir(state, None)
    lanes_dir = resolve_lanes_dir(beast_dir)
    lanes_dir.mkdir(parents=True, exist_ok=True)

    plan = build_lane_plan(state, Path(args.problem_map).resolve())
    save_json(beast_dir / "lane-plan.json", plan)

    for lane in plan["lanes"]:
        lane_path = lanes_dir / f"{lane['lane_id']}.json"
        if not lane_path.exists():
            save_json(lane_path, default_lane_file(lane))

    save_json(beast_dir / "jury-verdict.json", default_jury_verdict())

    print_json(
        {
            "beast_dir": str(beast_dir),
            "lane_plan_path": str(beast_dir / "lane-plan.json"),
            "lanes_dir": str(lanes_dir),
            "jury_verdict_path": str(beast_dir / "jury-verdict.json"),
        }
    )
    return 0


def paper_identity(entry: dict[str, Any]) -> str:
    if doi := entry.get("doi"):
        return f"doi:{slug_key(str(doi))}"
    article_url = entry.get("article_url")
    if isinstance(article_url, str) and article_url.strip():
        return f"url:{slug_key(article_url)}"
    return f"title:{slug_key(str(entry.get('title', '')))}:{entry.get('year', '')}"


def choose_article_url(candidates: list[str]) -> str:
    def score(url: str) -> tuple[int, str]:
        lowered = url.lower()
        if "doi.org" in lowered:
            return (0, lowered)
        if any(host in lowered for host in ("acm.org", "ieee.org", "springer.com", "nature.com")):
            return (1, lowered)
        if "arxiv.org" in lowered:
            return (2, lowered)
        return (3, lowered)

    return sorted({item for item in candidates if item}, key=score)[0]


# Mechanical merge and lane validation.
def build_merged_record(entry: dict[str, Any]) -> dict[str, Any]:
    return {
        "paper_id": None,
        "title": entry["title"],
        "authors": entry["authors"],
        "year": entry["year"],
        "venue": entry["venue"],
        "venue_type": entry["venue_type"],
        "article_url_candidates": [entry["article_url"]],
        "code_url_candidates": [entry["code_url"]] if entry.get("code_url") else [],
        "dataset_url_candidates": list(entry.get("dataset_urls", [])),
        "source_candidates": [entry["source"]],
        "why_relevant_notes": [entry["why_relevant"]],
        "artifact_notes": [entry["artifact_search_notes"]],
        "supporting_lanes": [entry["lane_id"]],
        "is_primary_evidence": bool(entry["is_primary_evidence"]),
        "crosscheck_status": "single_lane",
    }


def append_merge_conflict(record: dict[str, Any], entry: dict[str, Any], *, identity: str, conflicts: list[dict[str, Any]]) -> None:
    if record["year"] != entry["year"] or normalize_text(record["venue"]) != normalize_text(entry["venue"]):
        conflicts.append(
            {
                "identity": identity,
                "existing_year": record["year"],
                "incoming_year": entry["year"],
                "existing_venue": record["venue"],
                "incoming_venue": entry["venue"],
                "lane_id": entry["lane_id"],
            }
        )


def merge_entry_into_record(record: dict[str, Any], entry: dict[str, Any]) -> None:
    record["article_url_candidates"].append(entry["article_url"])
    if entry.get("code_url"):
        record["code_url_candidates"].append(entry["code_url"])
    record["dataset_url_candidates"].extend(entry.get("dataset_urls", []))
    record["source_candidates"].append(entry["source"])
    record["why_relevant_notes"].append(entry["why_relevant"])
    record["artifact_notes"].append(entry["artifact_search_notes"])
    if entry["lane_id"] not in record["supporting_lanes"]:
        record["supporting_lanes"].append(entry["lane_id"])
    record["is_primary_evidence"] = record["is_primary_evidence"] or bool(entry["is_primary_evidence"])
    if len(record["supporting_lanes"]) >= 2:
        record["crosscheck_status"] = "confirmed_by_multiple_lanes"


def finalize_merged_record(record: dict[str, Any], *, paper_id: str) -> dict[str, Any]:
    return {
        "paper_id": paper_id,
        "title": record["title"],
        "authors": record["authors"],
        "year": record["year"],
        "venue": record["venue"],
        "venue_type": record["venue_type"],
        "article_url": choose_article_url(record["article_url_candidates"]),
        "code_url": sorted(set(record["code_url_candidates"]))[0] if record["code_url_candidates"] else None,
        "dataset_urls": sorted(set(record["dataset_url_candidates"])),
        "source": ", ".join(sorted(set(record["source_candidates"]))),
        "why_relevant": " | ".join(dict.fromkeys(record["why_relevant_notes"])),
        "is_primary_evidence": record["is_primary_evidence"],
        "artifact_search_notes": " | ".join(dict.fromkeys(record["artifact_notes"])),
        "supporting_lanes": sorted(record["supporting_lanes"]),
        "crosscheck_status": record["crosscheck_status"],
    }


def merge_papers(entries: list[dict[str, Any]]) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    merged: dict[str, dict[str, Any]] = {}
    conflicts: list[dict[str, Any]] = []

    for entry in entries:
        identity = paper_identity(entry)
        record = merged.get(identity)
        if record is None:
            merged[identity] = build_merged_record(entry)
            continue

        append_merge_conflict(record, entry, identity=identity, conflicts=conflicts)
        merge_entry_into_record(record, entry)

    final_records = []
    sorted_records = sorted(
        merged.values(),
        key=lambda item: (-(len(item["supporting_lanes"])), item["year"], item["title"].lower()),
    )
    for index, record in enumerate(sorted_records, start=1):
        final_records.append(finalize_merged_record(record, paper_id=f"P{index:02d}"))

    return final_records, conflicts


def lane_payload_errors(payload: dict[str, Any], *, path: Path) -> list[str]:
    errors: list[str] = []
    lane_id = payload.get("lane_id")
    if not isinstance(lane_id, str) or not lane_id.strip():
        errors.append(f"{path.name}: lane_id missing")
    if payload.get("status") != "completed":
        errors.append(f"{path.name}: status must be completed before merge")
    papers = payload.get("papers")
    if not isinstance(papers, list) or not papers:
        errors.append(f"{path.name}: papers must be a non-empty list")
    return errors


def normalize_lane_paper(paper: dict[str, Any], *, lane_id: str | None) -> dict[str, Any]:
    return {
        "lane_id": lane_id,
        "title": paper.get("title", ""),
        "authors": paper.get("authors", []),
        "year": paper.get("year"),
        "venue": paper.get("venue", ""),
        "venue_type": paper.get("venue_type", ""),
        "article_url": paper.get("article_url", ""),
        "code_url": paper.get("code_url"),
        "dataset_urls": paper.get("dataset_urls", []),
        "source": paper.get("source", ""),
        "why_relevant": paper.get("why_relevant", ""),
        "is_primary_evidence": paper.get("is_primary_evidence", False),
        "artifact_search_notes": paper.get("artifact_search_notes", ""),
        "doi": paper.get("doi"),
    }


def validate_lane_file(path: Path) -> tuple[list[dict[str, Any]], list[str]]:
    payload = load_json(path)
    errors = lane_payload_errors(payload, path=path)
    papers = payload.get("papers")
    if errors and (not isinstance(papers, list) or not papers):
        return [], errors

    lane_id = payload.get("lane_id")
    normalized: list[dict[str, Any]] = []
    for index, paper in enumerate(papers or []):
        prefix = f"{path.name}.papers[{index}]"
        if not isinstance(paper, dict):
            errors.append(f"{prefix} must be an object")
            continue

        for field in REQUIRED_LANE_PAPER_FIELDS:
            if field not in paper:
                errors.append(f"{prefix}.{field} is required")
        if not isinstance(paper.get("authors"), list) or not paper.get("authors"):
            errors.append(f"{prefix}.authors must be a non-empty list")
        if not isinstance(paper.get("dataset_urls"), list):
            errors.append(f"{prefix}.dataset_urls must be a list")

        normalized.append(normalize_lane_paper(paper, lane_id=lane_id))
    return normalized, errors


def collect_completed_lane_entries(lanes_dir: Path) -> tuple[list[dict[str, Any]], list[str], list[str]]:
    all_entries: list[dict[str, Any]] = []
    completed_lane_ids: list[str] = []
    errors: list[str] = []

    for lane_path in sorted(lanes_dir.glob("*.json")):
        entries, lane_errors = validate_lane_file(lane_path)
        if lane_errors:
            errors.extend(lane_errors)
            continue
        all_entries.extend(entries)
        completed_lane_ids.append(load_json(lane_path)["lane_id"])

    return all_entries, completed_lane_ids, errors


def print_errors(errors: list[str]) -> int:
    for error in errors:
        print(error, file=sys.stderr)
    return 1


def build_merge_report(
    *,
    completed_lane_ids: list[str],
    all_entries: list[dict[str, Any]],
    merged_papers: list[dict[str, Any]],
    conflicts: list[dict[str, Any]],
    papers_path: Path,
) -> dict[str, Any]:
    return {
        "protocol_version": 1,
        "generated_at": utc_now(),
        "completed_lanes": completed_lane_ids,
        "candidate_count": len(all_entries),
        "unique_paper_count": len(merged_papers),
        "multi_lane_confirmed_count": sum(
            1 for item in merged_papers if item["crosscheck_status"] == "confirmed_by_multiple_lanes"
        ),
        "single_lane_only_count": sum(1 for item in merged_papers if item["crosscheck_status"] == "single_lane"),
        "missing_code_url_count": sum(1 for item in merged_papers if item["code_url"] is None),
        "missing_dataset_count": sum(1 for item in merged_papers if not item["dataset_urls"]),
        "conflicts": conflicts,
        "papers_path": str(papers_path),
    }


def build_jury_input(state: dict[str, Any], papers_path: Path, merge_report_path: Path) -> dict[str, Any]:
    return {
        "question": state["question"],
        "run_id": state["run_id"],
        "papers_path": str(papers_path),
        "merge_report_path": str(merge_report_path.resolve()),
        "review_question": JURY_REVIEW_QUESTION,
    }


def jury_readiness_reasons(report: dict[str, Any]) -> list[str]:
    reasons: list[str] = []
    completed_lanes = report.get("completed_lanes", [])
    if len(completed_lanes) < MIN_COMPLETED_LANES:
        reasons.append("beast mode requires at least 3 completed lanes before jury")
    if "artifact-verifier" not in completed_lanes:
        reasons.append("artifact-verifier lane must complete before jury")
    if report.get("unique_paper_count", 0) < MIN_UNIQUE_PAPERS:
        reasons.append("beast mode expects at least 10 unique papers after merge")
    if report.get("multi_lane_confirmed_count", 0) < MIN_MULTI_LANE_CONFIRMATIONS:
        reasons.append("beast mode expects at least 4 papers confirmed by multiple lanes")
    if report.get("conflicts"):
        reasons.append("metadata conflicts must be reviewed before jury")
    return reasons


# Merge command.
def merge_beast(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state_path).resolve())
    run_dir = Path(state["run_dir"]).resolve()
    beast_dir = resolve_beast_dir(state, args.beast_dir)
    lanes_dir = resolve_lanes_dir(beast_dir)
    if not lanes_dir.exists():
        print(f"lanes directory not found: {lanes_dir}", file=sys.stderr)
        return 1

    all_entries, completed_lane_ids, errors = collect_completed_lane_entries(lanes_dir)
    if errors:
        return print_errors(errors)

    merged_papers, conflicts = merge_papers(all_entries)
    papers_path = Path(args.output).resolve() if args.output else run_dir / "papers.json"
    save_json(papers_path, merged_papers)

    validation_errors = validate_file(papers_path)
    if validation_errors:
        return print_errors(validation_errors)

    merge_report = build_merge_report(
        completed_lane_ids=completed_lane_ids,
        all_entries=all_entries,
        merged_papers=merged_papers,
        conflicts=conflicts,
        papers_path=papers_path,
    )
    merge_report_path = beast_dir / "merge-report.json"
    save_json(merge_report_path, merge_report)
    save_json(beast_dir / "jury-input.json", build_jury_input(state, papers_path, merge_report_path))

    print_json(merge_report)
    return 0


# Verdict recording and assertion commands.
def record_verdict(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state_path).resolve())
    ok, error = require_beast_effort(state, action="record-verdict")
    if not ok:
        assert error is not None
        print(error, file=sys.stderr)
        return 1

    beast_dir = resolve_beast_dir(state, args.beast_dir)
    missing = missing_paths(required_verdict_artifacts(beast_dir))
    if missing:
        print(json.dumps({"missing_artifacts": missing}, ensure_ascii=False), file=sys.stderr)
        return 1

    reasons = [item.strip() for item in args.reason if item.strip()]
    if not reasons:
        print("record-verdict requires at least one --reason", file=sys.stderr)
        return 2

    verdict_path = beast_dir / "jury-verdict.json"
    payload = load_json(verdict_path)
    payload.update(
        {
            "status": "completed",
            "reviewer_type": args.reviewer_type,
            "verdict": args.verdict,
            "reasons": reasons,
            "checked_at": utc_now(),
        }
    )
    save_json(verdict_path, payload)
    print_json(payload)
    return 0


def verdict_errors(verdict_path: Path) -> list[str]:
    errors: list[str] = []
    if not verdict_path.exists():
        errors.append(f"jury verdict not found: {verdict_path}")
        return errors

    verdict = load_json(verdict_path)
    if verdict.get("status") != "completed":
        errors.append("jury verdict status must be completed")
    if verdict.get("verdict") != "accepted":
        errors.append("jury verdict must be accepted")
    reviewer_type = verdict.get("reviewer_type")
    if not isinstance(reviewer_type, str) or not reviewer_type.strip():
        errors.append("jury verdict reviewer_type is required")
    checked_at = verdict.get("checked_at")
    if not isinstance(checked_at, str) or not checked_at.strip():
        errors.append("jury verdict checked_at is required")
    return errors


def assert_verdict(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state_path).resolve())
    verdict_path = resolve_beast_dir(state, args.beast_dir) / "jury-verdict.json"
    errors = verdict_errors(verdict_path)

    payload = {
        "accepted": not errors,
        "jury_verdict_path": str(verdict_path.resolve()),
        "errors": errors,
    }
    if errors:
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 1
    print_json(payload)
    return 0


def jury_ready(args: argparse.Namespace) -> int:
    state = load_json(Path(args.state_path).resolve())
    beast_dir = resolve_beast_dir(state, args.beast_dir)
    merge_report_path = beast_dir / "merge-report.json"
    if not merge_report_path.exists():
        print(f"merge report not found: {merge_report_path}", file=sys.stderr)
        return 1

    report = load_json(merge_report_path)
    reasons = jury_readiness_reasons(report)

    payload = {
        "ready": not reasons,
        "reasons": reasons,
        "merge_report_path": str(merge_report_path.resolve()),
        "jury_input_path": str((beast_dir / "jury-input.json").resolve()),
    }
    if reasons:
        print(json.dumps(payload, ensure_ascii=False), file=sys.stderr)
        return 1
    print_json(payload)
    return 0


# CLI surface.
def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Beast-mode hunt executor and merge gate.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    init_parser = subparsers.add_parser("init")
    init_parser.add_argument("--state-path", required=True)
    init_parser.add_argument("--problem-map", required=True)
    init_parser.set_defaults(func=init_beast)

    merge_parser = subparsers.add_parser("merge")
    merge_parser.add_argument("--state-path", required=True)
    merge_parser.add_argument("--beast-dir")
    merge_parser.add_argument("--output")
    merge_parser.set_defaults(func=merge_beast)

    record_parser = subparsers.add_parser("record-verdict")
    record_parser.add_argument("--state-path", required=True)
    record_parser.add_argument("--beast-dir")
    record_parser.add_argument("--reviewer-type", required=True)
    record_parser.add_argument("--verdict", choices=["accepted", "revise", "rejected"], required=True)
    record_parser.add_argument("--reason", action="append", default=[])
    record_parser.set_defaults(func=record_verdict)

    assert_verdict_parser = subparsers.add_parser("assert-verdict")
    assert_verdict_parser.add_argument("--state-path", required=True)
    assert_verdict_parser.add_argument("--beast-dir")
    assert_verdict_parser.set_defaults(func=assert_verdict)

    ready_parser = subparsers.add_parser("jury-ready")
    ready_parser.add_argument("--state-path", required=True)
    ready_parser.add_argument("--beast-dir")
    ready_parser.set_defaults(func=jury_ready)

    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    raise SystemExit(args.func(args))


if __name__ == "__main__":
    main()
