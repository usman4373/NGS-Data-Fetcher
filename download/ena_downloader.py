"""
ENA-specific download functions
"""
import requests
from utils.helpers import convert_ftp_to_aspera

def get_fasp_links_for_dataset(accession):
    """Get Aspera links for ENA dataset (converts FTP to Aspera if needed)"""
    url = (
        "https://www.ebi.ac.uk/ena/portal/api/filereport?"
        f"accession={accession}&result=read_run&"
        "fields=run_accession,fastq_aspera,fastq_ftp&format=tsv"
    )
    try:
        r = requests.get(url, timeout=30)
        if r.status_code != 200:
            print(f"  ⚠️ Failed to fetch data for {accession}. Status code: {r.status_code}")
            return []
    except requests.exceptions.RequestException as e:
        print(f"  ✗ Network error fetching {accession}: {str(e)}")
        return []

    lines = r.text.strip().split("\n")
    if len(lines) < 2:
        print(f"  ⚠️ No data found for accession {accession}")
        return []
    
    headers = lines[0].split("\t")
    results = []

    for line in lines[1:]:
        row = dict(zip(headers, line.split("\t")))
        srr = row.get("run_accession")
        fasp = row.get("fastq_aspera", "")
        ftp = row.get("fastq_ftp", "")

        links = []
        if fasp:
            for l in fasp.split(";"):
                if l.strip():
                    if "@" not in l:
                        l = "era-fasp@" + l
                    links.append(l.strip())
        elif ftp:
            for l in ftp.split(";"):
                if l.strip():
                    # Ensure FTP link has protocol
                    if l.startswith("ftp.") and not l.startswith("ftp://"):
                        l = "ftp://" + l
                    aspera_link = convert_ftp_to_aspera(l.strip())
                    if aspera_link:
                        links.append(aspera_link)

        for link in links:
            if link:
                results.append((srr, link))

    return results
