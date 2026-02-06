"""
GEO metadata download functions
"""
import subprocess
import os
from download.geo_downloader import resolve_gse_to_srr

def download_geo_metadata(gse_acc, output_dir):
    """Download GEO metadata in SRA CSV format (uses wget, not Aspera)"""
    try:
        # First get SRA run IDs
        srrs = resolve_gse_to_srr(gse_acc)
        if not srrs:
            print(f"  ⚠️ No SRA runs found for GEO accession {gse_acc}")
            return None
        
        # Download SRA runinfo for these runs
        sra_ids = srrs[:100]  # Limit to 100 to avoid URL too long
        efetch_url = (
            "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi"
            f"?db=sra&id={','.join(sra_ids)}&rettype=runinfo&retmode=text"
        )
        
        output_file = os.path.join(output_dir, f"{gse_acc}_sra_metadata.csv")
        
        # Use wget to download
        cmd = f"wget -q -O '{output_file}' '{efetch_url}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            # Check if file has content
            if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                # Read first few lines to check if it's valid CSV
                with open(output_file, 'r') as f:
                    lines = f.readlines()
                    if len(lines) > 1 and ',' in lines[0]:
                        print(f"  ✅ SRA metadata saved: {gse_acc}_sra_metadata.csv")
                        return f"{gse_acc}_sra_metadata.csv"
                    else:
                        # Try alternative method - use the SRA run selector
                        sra_url = f"https://trace.ncbi.nlm.nih.gov/Traces/study/?acc={','.join(sra_ids[:10])}&o=acc_s%3Aa"
                        cmd2 = f"wget -q -O '{output_file}' '{sra_url}'"
                        subprocess.run(cmd2, shell=True, capture_output=True, text=True)
                        
                        if os.path.exists(output_file) and os.path.getsize(output_file) > 0:
                            print(f"  ✅ SRA metadata saved: {gse_acc}_sra_metadata.csv")
                            return f"{gse_acc}_sra_metadata.csv"
                        else:
                            os.remove(output_file)
                            return None
            else:
                return None
        return None
    except Exception as e:
        print(f"  ⚠️ Could not download GEO (SRA) metadata for {gse_acc}: {str(e)}")
        return None
    