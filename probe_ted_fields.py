# # probe_simple.py
# import requests

# responses = requests.get("https://api.ted.europa.eu/v3/notices/search", timeout=10)
# print(responses.status_code)
# # probe_simple.py
# import requests
# print("__________________________")
# response = requests.post(
#     "https://api.ted.europa.eu/v3/notices/search",
#     json={
#         "query": 'FT ~ "messebau"',
#         "scope": "ACTIVE",
#         "limit": 1,
#         "page": 1,
#         "paginationMode": "PAGE_NUMBER",
#         "onlyLatestVersions": True,
#         "fields": ["publication-number"],
#     },
#     headers={"Accept": "application/json", "Content-Type": "application/json"},
#     timeout=15,
#     verify=False,   # ← temporarily disable SSL verification
# )
# print(response.status_code)
# print(response.text[:500])
import requests
import urllib3
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
TED_SEARCH_URL = "https://api.ted.europa.eu/v3/notices/search"

CANDIDATE_FIELDS = [
    "publication-number",
    "publication-date",
    "notice-title",
    "buyer-name",
    "buyer-country",
    "notice-type",
    "deadline-receipt-tenders",
    "cpv-code",
    "links",
]

payload_base = {
    "query": 'FT ~ "messebau"',
    "scope": "ACTIVE",
    "limit": 1,
    "page": 1,
    "paginationMode": "PAGE_NUMBER",
    "onlyLatestVersions": True,
}

headers = {
    "Accept": "application/json",
    "Content-Type": "application/json",
}

for field in CANDIDATE_FIELDS:
    payload = dict(payload_base)
    payload["fields"] = [field]

    try:
        response = requests.post(
            TED_SEARCH_URL,
            json=payload,
            headers=headers,
            timeout=(5, 30),
            verify=False,
        )

        if response.status_code == 200:
            print(f"OK   -> {field}")
        else:
            print(f"BAD  -> {field} | HTTP {response.status_code} | {response.text[:200]}")
    except Exception as e:
        print(f"ERR  -> {field} | {e}")