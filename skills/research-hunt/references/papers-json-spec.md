# papers.json Spec

Use this schema for `papers.json`.

## Required Shape

`papers.json` must be a JSON array.

Each entry must include:

```json
{
  "paper_id": "P01",
  "title": "Paper title",
  "authors": ["Author A", "Author B"],
  "year": 2025,
  "venue": "ICLR",
  "venue_type": "conference",
  "article_url": "https://doi.org/... or https://arxiv.org/abs/...",
  "code_url": "https://github.com/org/repo",
  "dataset_urls": [
    "https://dataset.example.org"
  ],
  "source": "semantic-scholar",
  "why_relevant": "One or two sentences tied to the mapped problem.",
  "is_primary_evidence": true,
  "artifact_search_notes": "Checked paper page, author page, and Papers with Code; official repo found, no public dataset link found."
}
```

## Link Rules

- `article_url` is mandatory and must point to the paper page, DOI, publisher page, or arXiv page.
- `code_url` is mandatory as a field:
  - use a URL string when a public official repo exists
  - use `null` when no public repo was found
- `dataset_urls` is mandatory as a field:
  - use a list of URLs when public datasets exist
  - use `[]` when no public dataset was found
- Never use search results as artifact links.

## Search Order For Artifact Links

1. paper landing page
2. DOI / publisher page
3. authors' official project pages
4. official GitHub / GitLab / project repositories
5. benchmark or dataset homepages
6. secondary aggregators only as fallback confirmation

## Optional Helpful Fields

- `doi`
- `abstract`
- `task_tags`
- `method_tags`
- `publication_status`
- `citation_count`
