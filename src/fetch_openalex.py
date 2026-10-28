import os
import time
import requests
import pandas as pd

URL = "https://api.openalex.org/works"
# MAILTO = "YOUR_EMAIL_HERE"
API_KEY = os.environ["OPENALEX_API_KEY"]
SEARCH = '"artificial light at night"'
FILTER = "from_publication_date:2024-10-27,to_publication_date:2026-10-27,language:en"
FIELDS = "id,doi,title,publication_year,primary_location,authorships,open_access,abstract_inverted_index"


def rebuild_abstract(inverted_index):
    """OpenAlex stores abstracts as {word: [positions]}; put them back in order."""
    if not inverted_index:
        return ""
    positions = {}
    for word, indexes in inverted_index.items():
        for i in indexes:
            positions[i] = word
    return " ".join(positions[i] for i in sorted(positions))


def parse_work(work):
    authorships = work.get("authorships") or []
    first_author = authorships[0]["author"]["display_name"] if authorships else ""

    location = work.get("primary_location") or {}
    source = location.get("source") or {}

    return {
        "first_author": first_author,
        "year": work.get("publication_year"),
        "venue": source.get("display_name", ""),
        "title": work.get("title", ""),
        "doi": work.get("doi", ""),
        "is_open_access": (work.get("open_access") or {}).get("is_oa", False),
        "abstract": rebuild_abstract(work.get("abstract_inverted_index")),
    }


def fetch_all():
    rows = []
    cursor = "*"
    while cursor:
        params = {
            "search": SEARCH,
            "filter": FILTER,
            "per-page": 200,
            "cursor": cursor,
            "select": FIELDS,
            # "mailto": MAILTO,
            "api_key": API_KEY,
        }
        response = requests.get(URL, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        for work in data["results"]:
            rows.append(parse_work(work))

        cursor = data["meta"].get("next_cursor")
        print(f"Fetched {len(rows)} papers so far")
        time.sleep(0.2)
    return rows


if __name__ == "__main__":
    rows = fetch_all()
    df = pd.DataFrame(rows)
    df.to_csv("data/raw/openalex_alan.csv", index=False)

    print(df.head())
    print("Shape:", df.shape)
    print("Papers without abstract:", (df["abstract"] == "").sum())