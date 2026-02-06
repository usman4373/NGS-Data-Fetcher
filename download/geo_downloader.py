"""
GEO-specific download functions
"""
import requests
import csv
import io

def resolve_gse_to_srr(gse):
    """Resolve GEO accession to SRA run accessions"""
    try:
        esearch = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi",
            params={"db": "gds", "term": gse, "retmode": "json"},
            timeout=30
        )
        esearch.raise_for_status()
        esearch = esearch.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to search for GEO accession {gse}: {str(e)}")
        return []
    except ValueError as e:
        print(f"  ✗ Invalid JSON response for GEO accession {gse}: {str(e)}")
        return []

    ids = esearch.get("esearchresult", {}).get("idlist", [])
    if not ids:
        print(f"  ⚠️ No IDs found for GEO accession {gse}")
        return []

    try:
        elink = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/elink.fcgi",
            params={"dbfrom": "gds", "db": "sra", "id": ids[0], "retmode": "json"},
            timeout=30
        )
        elink.raise_for_status()
        elink = elink.json()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to link GEO to SRA for {gse}: {str(e)}")
        return []
    except ValueError as e:
        print(f"  ✗ Invalid JSON response for linking {gse}: {str(e)}")
        return []

    sra_ids = elink.get("linksets", [{}])[0].get("linksetdbs", [{}])[0].get("links", [])
    if not sra_ids:
        print(f"  ⚠️ No SRA IDs found for GEO accession {gse}")
        return []

    try:
        efetch = requests.get(
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi",
            params={
                "db": "sra",
                "id": ",".join(sra_ids),
                "rettype": "runinfo",
                "retmode": "text",
            },
            timeout=30
        )
        efetch.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Failed to fetch SRA runinfo for {gse}: {str(e)}")
        return []

    try:
        reader = csv.DictReader(io.StringIO(efetch.text))
        return sorted({row["Run"] for row in reader if row.get("Run")})
    except Exception as e:
        print(f"  ✗ Failed to parse SRA runinfo for {gse}: {str(e)}")
        return []
    