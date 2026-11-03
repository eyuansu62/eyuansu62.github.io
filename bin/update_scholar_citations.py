#!/usr/bin/env python

import argparse
import os
from pathlib import Path
import sys
import tempfile
import yaml
from datetime import datetime

import sync_scholar_publications as publications


def load_scholar_user_id() -> str:
    """Load the Google Scholar user ID from the configuration file."""
    config_file = "_data/socials.yml"
    if not os.path.exists(config_file):
        print(
            f"Configuration file {config_file} not found. Please ensure the file exists and contains your Google Scholar user ID."
        )
        sys.exit(1)
    try:
        with open(config_file, "r") as f:
            config = yaml.safe_load(f)
        scholar_user_id = config.get("scholar_userid")
        if not scholar_user_id:
            print(
                "No 'scholar_userid' found in the configuration file. Please add 'scholar_userid' to _data/socials.yml."
            )
            sys.exit(1)
        return scholar_user_id
    except yaml.YAMLError as e:
        print(
            f"Error parsing YAML file {config_file}: {e}. Please check the file for correct YAML syntax."
        )
        sys.exit(1)


SCHOLAR_USER_ID: str = load_scholar_user_id()
OUTPUT_FILE: str = "_data/citations.yml"


def atomic_write(path: Path, content: str) -> None:
    """Readers see a complete file, including when a fetch is interrupted."""
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile(mode="w", encoding="utf-8", dir=path.parent, delete=False) as handle:
        temporary = Path(handle.name)
        try:
            handle.write(content)
            handle.close()
            temporary.replace(path)
        finally:
            temporary.unlink(missing_ok=True)


def get_scholar_citations(sync_publications: bool = False, force: bool = False) -> None:
    """Fetch citations and optionally import missing publications."""
    print(f"Fetching citations for Google Scholar ID: {SCHOLAR_USER_ID}")
    today = datetime.now().strftime("%Y-%m-%d")
    existing_data = None

    # Check if the output file was already updated today
    if os.path.exists(OUTPUT_FILE):
        try:
            with open(OUTPUT_FILE, "r") as f:
                existing_data = yaml.safe_load(f)
            if (
                existing_data
                and "metadata" in existing_data
                and "last_updated" in existing_data["metadata"]
            ):
                print(f"Last updated on: {existing_data['metadata']['last_updated']}")
                if (
                    not force
                    and existing_data["metadata"]["last_updated"] == today
                    and (not sync_publications or existing_data["metadata"].get("publications_last_updated") == today)
                ):
                    print("Citations data is already up-to-date. Skipping fetch.")
                    return
        except Exception as e:
            print(
                f"Warning: Could not read existing citation data from {OUTPUT_FILE}: {e}. The file may be missing or corrupted."
            )

    citation_data = {"metadata": {"last_updated": today}, "papers": {}}

    try:
        author_data = publications.fetch_profile(SCHOLAR_USER_ID)
    except Exception as e:
        print(
            f"Error fetching author data from Google Scholar for user ID '{SCHOLAR_USER_ID}': {e}. Please check your internet connection and Scholar user ID."
        )
        sys.exit(1)

    if not author_data:
        print(
            f"Could not fetch author data for user ID '{SCHOLAR_USER_ID}'. Please verify the Scholar user ID and try again."
        )
        sys.exit(1)

    if not author_data.get("publications"):
        print(f"No publications found in author data for user ID '{SCHOLAR_USER_ID}'.")
        sys.exit(1)

    for pub in author_data["publications"]:
        try:
            pub_id = pub.get("pub_id") or pub.get("author_pub_id")
            if not pub_id:
                print(
                    f"Warning: No ID found for publication: {pub.get('bib', {}).get('title', 'Unknown')}. This publication will be skipped."
                )
                continue

            title = pub.get("bib", {}).get("title", "Unknown Title")
            year = pub.get("bib", {}).get("pub_year", "Unknown Year")
            citations = pub.get("num_citations", 0)

            print(f"Found: {title} ({year}) - Citations: {citations}")

            citation_data["papers"][pub_id] = {
                "title": title,
                "year": year,
                "citations": citations,
            }
        except Exception as e:
            print(
                f"Error processing publication '{pub.get('bib', {}).get('title', 'Unknown')}': {e}. This publication will be skipped."
            )

    if not citation_data["papers"]:
        print("No valid publication IDs returned. Keeping existing citation data.")
        sys.exit(1)

    # Prepare every output before touching either file. A blocked detail page
    # must not mark a partial publication import as successfully synchronized.
    bibliography = None
    if sync_publications:
        bibliography = publications.prepare_bibliography(author_data["publications"], SCHOLAR_USER_ID)
        citation_data["metadata"]["publications_last_updated"] = today
    elif existing_data and existing_data.get("metadata", {}).get("publications_last_updated"):
        citation_data["metadata"]["publications_last_updated"] = existing_data["metadata"]["publications_last_updated"]

    try:
        if bibliography is not None:
            path = publications.MANAGED_FILE
            if not path.exists() or path.read_text(encoding="utf-8") != bibliography:
                atomic_write(path, bibliography)
                print(f"New publications saved to {path}")
        if existing_data != citation_data:
            atomic_write(Path(OUTPUT_FILE), yaml.dump(citation_data, width=1000, sort_keys=True))
            print(f"Citation data saved to {OUTPUT_FILE}")
        else:
            print("No changes in citation data. Skipping file update.")
    except Exception as e:
        print(
            f"Error saving Scholar data: {e}. Please check file permissions and disk space."
        )
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Synchronize Google Scholar citations and new publications.")
    parser.add_argument("--sync-publications", action="store_true", help="Import missing papers into _bibliography/scholar.bib.")
    parser.add_argument("--force", action="store_true", help="Fetch even if the data was checked today.")
    args = parser.parse_args()
    try:
        get_scholar_citations(sync_publications=args.sync_publications, force=args.force)
    except Exception as e:
        print(f"Unexpected error: {e}")
        sys.exit(1)
