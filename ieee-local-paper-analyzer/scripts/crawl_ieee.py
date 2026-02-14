#!/usr/bin/env python3
import argparse
import csv
import json
import time
from pathlib import Path

import requests

SEARCH_API = "https://ieeexplore.ieee.org/rest/search"
DEFAULT_HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json, text/plain, */*",
    "Origin": "https://ieeexplore.ieee.org",
    "Referer": "https://ieeexplore.ieee.org/",
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0 Safari/537.36",
}


def normalize_record(item: dict, query: str) -> dict:
    authors = []
    authors_data = item.get("authors") or {}
    for a in authors_data.get("authors", []):
        name = (a.get("full_name") or "").strip()
        if name:
            authors.append(name)

    keywords = []
    for key in ("index_terms", "author_terms"):
        terms = item.get(key) or {}
        for bucket in terms.values() if isinstance(terms, dict) else []:
            if isinstance(bucket, list):
                keywords.extend([str(x).strip() for x in bucket if str(x).strip()])

    pdf_path = item.get("pdf_url") or ""
    if pdf_path and pdf_path.startswith("/"):
        pdf_url = f"https://ieeexplore.ieee.org{pdf_path}"
    else:
        pdf_url = pdf_path

    doc_path = item.get("html_url") or item.get("documentLink") or ""
    if doc_path and doc_path.startswith("/"):
        document_url = f"https://ieeexplore.ieee.org{doc_path}"
    else:
        document_url = doc_path

    return {
        "query": query,
        "title": (item.get("title") or "").strip(),
        "authors": authors,
        "publication_title": (item.get("publicationTitle") or "").strip(),
        "year": item.get("publicationYear"),
        "doi": (item.get("doi") or "").strip(),
        "abstract": (item.get("abstract") or "").strip(),
        "keywords": sorted(set(keywords)),
        "document_url": document_url,
        "pdf_url": pdf_url,
        "publisher": (item.get("publisher") or "IEEE").strip(),
        "content_type": (item.get("contentType") or "").strip(),
        "source": "ieee_xplore_rest_search",
    }


def search_ieee(query: str, max_records: int, start_year: int | None, end_year: int | None, sleep_sec: float) -> list[dict]:
    session = requests.Session()
    session.headers.update(DEFAULT_HEADERS)

    page_size = 25
    records: list[dict] = []
    start_record = 1

    while len(records) < max_records:
        payload = {
            "queryText": query,
            "highlight": True,
            "returnType": "SEARCH",
            "rowsPerPage": page_size,
            "pageNumber": ((start_record - 1) // page_size) + 1,
        }
        if start_year:
            payload["start_year"] = str(start_year)
        if end_year:
            payload["end_year"] = str(end_year)

        response = session.post(SEARCH_API, data=json.dumps(payload), timeout=30)
        response.raise_for_status()
        data = response.json()

        results = data.get("records") or []
        if not results:
            break

        for item in results:
            records.append(normalize_record(item, query))
            if len(records) >= max_records:
                break

        start_record += len(results)
        time.sleep(sleep_sec)

    return records


def write_jsonl(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        for row in records:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_csv(records: list[dict], out_path: Path) -> None:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fields = [
        "query",
        "title",
        "authors",
        "publication_title",
        "year",
        "doi",
        "abstract",
        "keywords",
        "document_url",
        "pdf_url",
        "publisher",
        "content_type",
        "source",
    ]
    with out_path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        for row in records:
            out = dict(row)
            out["authors"] = "; ".join(row.get("authors", []))
            out["keywords"] = "; ".join(row.get("keywords", []))
            writer.writerow(out)


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Crawl IEEE papers metadata from local-host network environment.")
    p.add_argument("--query", required=True, help="Keyword query for IEEE search.")
    p.add_argument("--max-records", type=int, default=100, help="Maximum number of papers to fetch.")
    p.add_argument("--start-year", type=int, default=None, help="Filter start publication year.")
    p.add_argument("--end-year", type=int, default=None, help="Filter end publication year.")
    p.add_argument("--sleep-sec", type=float, default=0.8, help="Sleep seconds between page requests.")
    p.add_argument("--out", required=True, help="Output path (.jsonl or .csv).")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    records = search_ieee(
        query=args.query,
        max_records=args.max_records,
        start_year=args.start_year,
        end_year=args.end_year,
        sleep_sec=args.sleep_sec,
    )

    out_path = Path(args.out)
    suffix = out_path.suffix.lower()
    if suffix == ".jsonl":
        write_jsonl(records, out_path)
    elif suffix == ".csv":
        write_csv(records, out_path)
    else:
        raise ValueError("--out must end with .jsonl or .csv")

    print(f"Fetched {len(records)} records -> {out_path}")


if __name__ == "__main__":
    main()
