from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


REQUIRED_STRING_FIELDS = [
    "paper_id",
    "title",
    "venue",
    "venue_type",
    "article_url",
    "source",
    "why_relevant",
    "artifact_search_notes",
]


def is_http_url(value: object) -> bool:
    return isinstance(value, str) and value.startswith(("http://", "https://"))


def validate_entry(entry: object, index: int) -> list[str]:
    prefix = f"paper[{index}]"
    errors: list[str] = []

    if not isinstance(entry, dict):
        return [f"{prefix} must be an object"]

    for field in REQUIRED_STRING_FIELDS:
        value = entry.get(field)
        if not isinstance(value, str) or not value.strip():
            errors.append(f"{prefix}.{field} must be a non-empty string")

    authors = entry.get("authors")
    if not isinstance(authors, list) or not authors or not all(isinstance(item, str) and item.strip() for item in authors):
        errors.append(f"{prefix}.authors must be a non-empty list of strings")

    year = entry.get("year")
    if not isinstance(year, int):
        errors.append(f"{prefix}.year must be an integer")

    is_primary_evidence = entry.get("is_primary_evidence")
    if not isinstance(is_primary_evidence, bool):
        errors.append(f"{prefix}.is_primary_evidence must be a boolean")

    article_url = entry.get("article_url")
    if not is_http_url(article_url):
        errors.append(f"{prefix}.article_url must be an http(s) URL")

    if "code_url" not in entry:
        errors.append(f"{prefix}.code_url field is required")
    else:
        code_url = entry.get("code_url")
        if code_url is not None and not is_http_url(code_url):
            errors.append(f"{prefix}.code_url must be null or an http(s) URL")

    if "dataset_urls" not in entry:
        errors.append(f"{prefix}.dataset_urls field is required")
    else:
        dataset_urls = entry.get("dataset_urls")
        if not isinstance(dataset_urls, list):
            errors.append(f"{prefix}.dataset_urls must be a list")
        elif not all(is_http_url(item) for item in dataset_urls):
            errors.append(f"{prefix}.dataset_urls must contain only http(s) URLs")

    return errors


def validate_file(path: Path) -> list[str]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return [f"file not found: {path}"]
    except json.JSONDecodeError as exc:
        return [f"invalid JSON: {exc}"]

    if not isinstance(payload, list):
        return ["papers.json must be a JSON array"]
    if not payload:
        return ["papers.json must contain at least one paper entry"]

    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, entry in enumerate(payload):
        errors.extend(validate_entry(entry, index))
        if isinstance(entry, dict):
            paper_id = entry.get("paper_id")
            if isinstance(paper_id, str):
                if paper_id in seen_ids:
                    errors.append(f"paper[{index}].paper_id duplicates an earlier entry: {paper_id}")
                seen_ids.add(paper_id)
    return errors


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Validate research-hunt papers.json output.")
    parser.add_argument("path", help="Path to papers.json")
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()
    errors = validate_file(Path(args.path).resolve())
    if errors:
        for error in errors:
            print(error, file=sys.stderr)
        raise SystemExit(1)
    print("papers.json is valid")


if __name__ == "__main__":
    main()
