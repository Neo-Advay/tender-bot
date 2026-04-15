import requests

URL = "https://api.ted.europa.eu/v3/notices/search"

payload = {
    "query": 'FT ~ "messebau"',
    "scope": "ACTIVE",
    "limit": 100,
    "page": 1,
    "paginationMode": "PAGE_NUMBER",
    "checkQuerySyntax": False,
    # Start minimal to avoid "invalid fields" issues; add more fields after you see the response shape.
    "fields": [
        "publication-date",
        "notice-title",
        "buyer-name",
        "buyer-country",
        "notice-type"
    ]
}

r = requests.post(URL, json=payload, headers={"Accept": "*/*", "Content-Type": "application/json"})
print("Status:", r.status_code)

if r.status_code != 200:
    print(r.text)
    raise SystemExit(1)

data = r.json()
notices = data.get("notices", [])
print("Notices returned:", len(notices))

for n in notices:
    title = n.get("notice-title", {}).get("eng") or n.get("notice-title", {}).get("deu", "N/A")
    buyer = list(n.get("buyer-name", {}).values())
    buyer = buyer[0][0] if buyer else "N/A"

    print(f"""
Publication: {n.get('publication-number')}
Date:        {n.get('publication-date')}
Type:        {n.get('notice-type')}
Buyer:       {buyer}
Country:     {n.get('buyer-country', ['N/A'])[0]}
Title:       {title}
Link:        {n.get('links', {}).get('html', {}).get('ENG', 'N/A')}
{'-'*60}""")
    
#for n in notices:
#    print(n)#("-", n.get("publication-number", n))