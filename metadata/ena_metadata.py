"""
ENA metadata download functions
"""
import subprocess
import os

def download_ena_metadata(ena_acc, output_dir):
    """Download ENA metadata in TSV format (uses wget, not Aspera)"""
    try:
        ena_url = (
            "https://www.ebi.ac.uk/ena/portal/api/filereport?"
            f"accession={ena_acc}&result=read_run&"
            "fields=study_accession,experiment_accession,run_accession,"
            "sample_accession,secondary_sample_accession,first_public,"
            "fastq_ftp,fastq_aspera,fastq_bytes,fastq_md5,sample_alias,"
            "instrument_model,library_layout,library_strategy,library_source&format=tsv"
        )
        
        output_file = os.path.join(output_dir, f"{ena_acc}_metadata.tsv")
        cmd = f"wget -q -O '{output_file}' '{ena_url}'"
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            with open(output_file, 'r') as f:
                lines = f.readlines()
                if len(lines) > 1:
                    print(f"  ✅ ENA metadata saved: {ena_acc}_metadata.tsv")
                    return f"{ena_acc}_metadata.tsv"
                else:
                    os.remove(output_file)
                    return None
        return None
    except Exception as e:
        print(f"  ⚠️ Could not download ENA metadata for {ena_acc}: {str(e)}")
        return None
    
