import requests

URL = "https://api.openalex.org/works"

params = {
    "search": '"artificial light at night"',
    "filter": "from_publication_date:2024-10-27,to_publication_date:2026-10-27,language:en",
    "per-page": 5,
    "mailto": "YOUR_EMAIL_HERE",
}

response = requests.get(URL, params=params, timeout=30)
response.raise_for_status()
data = response.json()

print("Total matching papers:", data["meta"]["count"])
for work in data["results"]:
    print(work["publication_year"], "-", work["title"])