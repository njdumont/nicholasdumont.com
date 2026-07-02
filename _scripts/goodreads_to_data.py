#!/usr/bin/env python3
"""
Generate _data/books.json for the site from a Goodreads CSV export.

Goodreads retired its public API, so the reliable way to sync is the CSV export:
  Goodreads -> My Books -> (left sidebar, bottom) Import and Export -> Export Library
That downloads a file like `goodreads_library_export.csv`.

Usage:
  python3 _scripts/goodreads_to_data.py path/to/goodreads_library_export.csv
  python3 _scripts/goodreads_to_data.py export.csv --shelf to-read   # default shelf
  python3 _scripts/goodreads_to_data.py export.csv --all             # ignore shelf filter

Output: writes _data/books.json (a flat list of {title, author}, sorted by title),
which books.html renders via {{ site.data.books }}. Then commit + push to publish.

Unlike some generators, this one is path-safe (it writes relative to this script,
not your current directory) and prints exactly what it wrote.
"""
import argparse
import csv
import json
import os
import sys

# Repo root = parent of the _scripts/ directory this file lives in.
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = os.path.dirname(SCRIPT_DIR)
OUT_PATH = os.path.join(REPO_ROOT, "_data", "books.json")


def title_sort_key(title: str) -> str:
    """Sort ignoring a leading article (The / A / An)."""
    t = title.lower()
    for article in ("the ", "a ", "an "):
        if t.startswith(article):
            return t[len(article):]
    return t


def main() -> int:
    parser = argparse.ArgumentParser(description="Build _data/books.json from a Goodreads CSV export.")
    parser.add_argument("csv_path", help="Path to the Goodreads library export CSV")
    parser.add_argument("--shelf", default="to-read",
                        help="Exclusive Shelf to include (default: to-read)")
    parser.add_argument("--all", action="store_true",
                        help="Include every book, ignoring the shelf filter")
    args = parser.parse_args()

    if not os.path.isfile(args.csv_path):
        print(f"Error: file not found: {args.csv_path}", file=sys.stderr)
        return 1

    books = []
    with open(args.csv_path, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        if "Title" not in (reader.fieldnames or []):
            print("Error: this doesn't look like a Goodreads export "
                  "(no 'Title' column found).", file=sys.stderr)
            return 1
        for row in reader:
            shelf = (row.get("Exclusive Shelf") or "").strip()
            if not args.all and shelf != args.shelf:
                continue
            title = (row.get("Title") or "").strip()
            author = (row.get("Author") or "").strip()
            if not title:
                continue
            books.append({"title": title, "author": author})

    books.sort(key=lambda b: title_sort_key(b["title"]))

    os.makedirs(os.path.dirname(OUT_PATH), exist_ok=True)
    with open(OUT_PATH, "w", encoding="utf-8") as f:
        json.dump(books, f, ensure_ascii=False, indent=2)
        f.write("\n")

    scope = "all shelves" if args.all else f"shelf '{args.shelf}'"
    print(f"Wrote {len(books)} books ({scope}) -> {os.path.relpath(OUT_PATH, os.getcwd())}")
    if not books:
        print("Warning: 0 books matched. Check the --shelf name, or pass --all.",
              file=sys.stderr)
    return 0


if __name__ == "__main__":
    sys.exit(main())
