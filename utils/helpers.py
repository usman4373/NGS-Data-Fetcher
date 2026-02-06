"""
General helper functions
"""
import re
import subprocess
from datetime import datetime

def detect_accession_type(accession):
    """Detect if an accession is GEO or ENA based on its prefix"""
    accession = accession.upper().strip()
    
    geo_patterns = [
        r'^GSE\d+', r'^GSM\d+', r'^GPL\d+', r'^GDS\d+',
    ]
    
    for pattern in geo_patterns:
        if re.match(pattern, accession):
            return "GEO"
    
    ena_patterns = [
        r'^SR[RPX]\d+', r'^ER[RPX]\d+', r'^DR[RPX]\d+',
        r'^PRJ[EDN]\w+', r'^SAM[END]\w+',
    ]
    
    for pattern in ena_patterns:
        if re.match(pattern, accession):
            return "ENA"
    
    return "ENA"

def normalize_ftp_link(link):
    """Normalize FTP link to ensure it has proper protocol"""
    if not link or not link.strip():
        return None
    
    link = link.strip()
    
    # If link starts with ftp. but not ftp://, add protocol
    if link.startswith("ftp.") and not link.startswith("ftp://"):
        link = "ftp://" + link
    
    # If link starts with http:// or https://, keep as is
    if link.startswith(("http://", "https://", "ftp://")):
        return link
    
    # If link contains @ (Aspera link), keep as is
    if "@" in link:
        return link
    
    # Otherwise, assume it's a relative path and return None
    return None

def convert_ftp_to_aspera(ftp_link):
    """Convert FTP link to Aspera link for ENA/SRA servers"""
    if not ftp_link:
        return None
    
    ftp_link = ftp_link.strip()
    
    # First normalize the FTP link
    ftp_link = normalize_ftp_link(ftp_link)
    if not ftp_link:
        return None
    
    if ftp_link.startswith("ftp://ftp.sra.ebi.ac.uk"):
        return ftp_link.replace("ftp://ftp.sra.ebi.ac.uk", "era-fasp@fasp.sra.ebi.ac.uk:")
    elif ftp_link.startswith("ftp://ftp.ncbi.nlm.nih.gov"):
        if "/sra/" in ftp_link:
            return ftp_link.replace("ftp://ftp.ncbi.nlm.nih.gov", "anonftp@ftp-private.ncbi.nlm.nih.gov:")
        else:
            return None  # Don't use Aspera for non-SRA NCBI files
    elif ftp_link.startswith("era-fasp@") or ftp_link.startswith("anonftp@"):
        return ftp_link
    elif ftp_link.startswith("ftp://"):
        # Don't try to convert non-ENA FTP links
        return None
    
    return ftp_link

def get_remote_file_size(link):
    """Get file size from remote server using FTP (for both FTP and Aspera links)"""
    try:
        ftp_link = link
        
        # Convert Aspera link back to FTP for curl
        if link.startswith("era-fasp@fasp.sra.ebi.ac.uk:"):
            ftp_link = link.replace("era-fasp@fasp.sra.ebi.ac.uk:", "ftp://ftp.sra.ebi.ac.uk")
        elif link.startswith("anonftp@ftp-private.ncbi.nlm.nih.gov:"):
            ftp_link = link.replace("anonftp@ftp-private.ncbi.nlm.nih.gov:", "ftp://ftp.ncbi.nlm.nih.gov")
        elif link.startswith("ftp.") and not link.startswith("ftp://"):
            ftp_link = "ftp://" + link
        
        # Ensure ftp_link has protocol
        if not ftp_link.startswith(("ftp://", "http://", "https://")):
            return None
        
        cmd = f"curl -sI {ftp_link} | grep -i 'content-length' | awk '{{print $2}}' | tr -d '\\r'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        if result.returncode == 0 and result.stdout.strip():
            return int(result.stdout.strip())
    except Exception:
        pass
    return None
