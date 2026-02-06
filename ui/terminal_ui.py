"""
Terminal user interface functions
"""
import os
import subprocess
import re
import csv
import io
from config import ASCP_PATH, ASPERA_KEY
from utils.helpers import detect_accession_type
from download.ena_downloader import get_fasp_links_for_dataset
from download.geo_downloader import resolve_gse_to_srr
from metadata.ena_metadata import download_ena_metadata
from metadata.geo_metadata import download_geo_metadata
from utils.file_utils import check_existing_files
from utils.progress import download_file
import time

def clear_screen():
    """Clear terminal screen"""
    os.system('cls' if os.name == 'nt' else 'clear')

def print_header():
    """Print application header"""
    clear_screen()
    print("=" * 70)
    print("🧬 NGS-Data-Fetcher")
    print("=" * 70)
    print()

def check_aspera():
    """Check if Aspera is properly installed and configured"""
    global ASPERA_KEY
    
    print("🔍 Checking Aspera configuration...")
    
    # Check ascp command
    try:
        result = subprocess.run([ASCP_PATH, "--version"], capture_output=True, text=True, check=False)
        if result.returncode != 0:
            print(f"✗ Aspera CLI (`{ASCP_PATH}`) is not working properly.")
            print(f"  Error: {result.stderr}")
            return False
        else:
            version_info = result.stdout.strip()
            print(f"  ✅ Aspera CLI version: {version_info}")
    except FileNotFoundError:
        print(f"✗ Aspera CLI (`{ASCP_PATH}`) not found. Please install Aspera CLI.")
        print(f"  You can install it via conda: `conda install -c bioconda aspera-cli`")
        return False
    
    # Check key file
    if not os.path.exists(ASPERA_KEY):
        print(f"✗ Aspera key file not found at: {ASPERA_KEY}")
        print(f"  Trying to find alternative key file...")
        
        # Try common locations
        possible_paths = [
            "~/anaconda3/pkgs/aspera-cli-3.9.6-h5e1937b_0/etc/asperaweb_id_dsa.openssh",
            "~/.aspera/connect/etc/asperaweb_id_dsa.openssh",
            "~/asperaweb_id_dsa.openssh",
            "/opt/aspera/etc/asperaweb_id_dsa.openssh",
            "/usr/local/etc/asperaweb_id_dsa.openssh",
        ]
        
        found = False
        for path in possible_paths:
            expanded = os.path.expanduser(path)
            if os.path.exists(expanded):
                print(f"  Found key at: {expanded}")
                ASPERA_KEY = expanded
                found = True
                break
        
        if not found:
            print(f"  ⚠️ No key file found. You may need to:")
            print(f"     1. Download from: https://www.ebi.ac.uk/ena/aspera/fasp_credentials/")
            print(f"     2. Or update the ASPERA_KEY variable in the script")
            return False
    
    print(f"  ✅ Aspera key file: {ASPERA_KEY}")
    
    # Test a simple Aspera connection
    print("  Testing Aspera connection...")
    test_cmd = [ASCP_PATH, "-h"]
    result = subprocess.run(test_cmd, capture_output=True, text=True)
    if result.returncode == 0:
        print("  ✅ Aspera connection test passed")
    else:
        print(f"  ⚠️ Aspera connection test failed: {result.stderr}")
    
    print()
    return True

def get_user_input():
    """Get all required inputs from user"""
    print_header()
    
    # Get output directory
    output_dir = input("📁 Enter output directory path: ").strip()
    while not output_dir:
        print("⚠️ Output directory cannot be empty!")
        output_dir = input("📁 Enter output directory path: ").strip()
    
    # Get download mode
    print("\n📊 Select download mode:")
    print("  1. ENA / GEO (full dataset)")
    print("  2. Custom links (CSV / TSV)")
    
    mode_choice = input("\nEnter choice (1 or 2): ").strip()
    while mode_choice not in ['1', '2']:
        print("⚠️ Invalid choice!")
        mode_choice = input("Enter choice (1 or 2): ").strip()
    
    mode = "ENA / GEO (full dataset)" if mode_choice == '1' else "Custom links (CSV / TSV)"
    
    # Get input file
    print(f"\n📄 Enter path to input file:")
    if mode_choice == '1':
        print("  (Text file with accession IDs, one per line)")
    else:
        print("  (CSV/TSV file with dataset_accession and ftp_links columns)")
    
    input_file = input("File path: ").strip()
    while not os.path.exists(input_file):
        print(f"⚠️ File not found: {input_file}")
        input_file = input("File path: ").strip()
    
    # Get bandwidth
    print("\n🚀 Select Aspera bandwidth:")
    print("  1. 100 Mbps (Slow but stable)")
    print("  2. 200 Mbps (Moderate speed)")
    print("  3. 500 Mbps (Good balance)")
    print("  4. 1000 Mbps (High speed)")
    print("  5. Enter custom value")
    
    bandwidth_choice = input("\nEnter choice (1-5): ").strip()
    while bandwidth_choice not in ['1', '2', '3', '4', '5']:
        print("⚠️ Invalid choice!")
        bandwidth_choice = input("Enter choice (1-5): ").strip()
    
    bandwidth_map = {
        '1': '100m',
        '2': '200m',
        '3': '500m',
        '4': '1000m'
    }
    
    if bandwidth_choice == '5':
        bandwidth = input("Enter custom bandwidth (e.g., 300m): ").strip()
        while not re.match(r'^\d+[mk]?$', bandwidth, re.IGNORECASE):
            print("⚠️ Invalid bandwidth format! Use format like '300m' or '1g'")
            bandwidth = input("Enter custom bandwidth: ").strip()
    else:
        bandwidth = bandwidth_map[bandwidth_choice]
    
    return output_dir, mode, input_file, bandwidth

def process_custom_links_mode(output_dir, input_file, bandwidth):
    """Process custom links mode"""
    summary = []
    
    try:
        # Detect delimiter
        if input_file.endswith('.tsv'):
            delimiter = '\t'
        else:
            delimiter = ','
        
        with open(input_file, 'r') as f:
            content = f.read()
        
        reader = csv.DictReader(
            io.StringIO(content),
            delimiter=delimiter
        )
        
        # Validate required columns
        required_columns = ["dataset_accession", "ftp_links"]
        reader_fieldnames = reader.fieldnames or []
        missing_columns = [col for col in required_columns if col not in reader_fieldnames]
        if missing_columns:
            print(f"✗ Missing required columns in input file: {', '.join(missing_columns)}")
            print(f"  Available columns: {', '.join(reader_fieldnames)}")
            return summary
        
        rows = list(reader)
        total = len(rows)
        
        if total == 0:
            print("⚠️ Input file is empty!")
            return summary
        
        print(f"\n📥 Processing {total} custom links...")
        
        for i, row in enumerate(rows, 1):
            dataset = row["dataset_accession"]
            accession = row.get("accession_ids", "NA")
            link = row["ftp_links"]
            
            if not link or not link.strip():
                print(f"  ⚠️ Skipping empty link for dataset {dataset}")
                summary.append({
                    "Dataset": dataset,
                    "Accession": accession,
                    "Type": "Custom link",
                    "Status": "Skipped (empty link)"
                })
                continue
            
            # Clean dataset name
            safe_dataset = "".join(c for c in dataset if c.isalnum() or c in (' ', '-', '_')).rstrip()
            outdir = os.path.join(output_dir, safe_dataset)
            os.makedirs(outdir, exist_ok=True)
            
            print(f"\n📥 Processing [{i}/{total}] `{dataset}` → `{accession}`")
            
            # Extract filename
            if link.strip().startswith("ftp://"):
                filename = link.strip().split("/")[-1]
            elif "@" in link and ":" in link:
                filename = link.strip().split(":")[-1].split("/")[-1]
            else:
                filename = link.strip().split("/")[-1]
            
            # Clean filename
            filename = filename.split('?')[0]
            
            # Download using Aspera only
            success, status_msg = download_file(link.strip(), outdir, bandwidth, filename, i, total)
            
            summary.append({
                "Dataset": dataset,
                "Accession": accession,
                "Type": "Custom link",
                "Status": status_msg
            })
            
    except Exception as e:
        print(f"✗ Error processing input file: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return summary

def process_ena_geo_mode(output_dir, input_file, bandwidth):
    """Process ENA/GEO mode"""
    summary = []
    
    try:
        with open(input_file, 'r') as f:
            content = f.read()
        
        accessions = [
            l.strip()
            for l in content.splitlines()
            if l.strip() and not l.strip().startswith("#")
        ]
        
        if not accessions:
            print("⚠️ No valid accessions found in input file!")
            return summary

        total_datasets = len(accessions)

        for i, acc in enumerate(accessions, 1):
            print(f"\n{'='*70}")
            print(f"📦 Processing dataset [{i}/{total_datasets}]: `{acc}`")
            print(f"{'='*70}")

            # Detect accession type
            acc_type = detect_accession_type(acc)
            print(f"  📍 Detected as {acc_type} accession")

            # Clean accession for filesystem safety
            safe_acc = "".join(c for c in acc if c.isalnum() or c in (' ', '-', '_')).rstrip()
            outdir = os.path.join(output_dir, safe_acc)
            os.makedirs(outdir, exist_ok=True)

            # Download metadata file
            print(f"  📋 Downloading metadata...")
            metadata_file = None

            if acc_type == "GEO":
                metadata_file = download_geo_metadata(acc, outdir)
            else:  # ENA accession
                metadata_file = download_ena_metadata(acc, outdir)

            if metadata_file:
                print(f"  ✅ Metadata saved: `{metadata_file}`")
            else:
                print(f"  ⚠️ Could not download metadata")
            
            time.sleep(0.5)

            links = []

            if acc_type == "GEO":
                srrs = resolve_gse_to_srr(acc)
                if srrs:
                    print(f"  🔗 Found {len(srrs)} SRA runs")
                    for srr in srrs:
                        srr_links = get_fasp_links_for_dataset(srr)
                        if srr_links:
                            links.extend(srr_links)
                else:
                    print(f"  ⚠️ No SRA runs found for GEO accession {acc}")
            else:  # ENA accession
                links = get_fasp_links_for_dataset(acc)
            
            if not links:
                print(f"  ⚠️ No download links found for {acc}")
                summary.append({
                    "Dataset": acc,
                    "Type": acc_type,
                    "Total files": 0,
                    "Complete": 0,
                    "Downloaded": 0,
                    "Status": "No files found"
                })
            else:
                # Check for existing files
                existing_files, partial_files, missing_files = check_existing_files(outdir, links)
                
                print(f"  📊 File status: {len(existing_files)} complete, {len(missing_files)} to download")
                
                # Report existing files
                if existing_files:
                    print(f"  ✓ Complete: {len(existing_files)} files")
                

                # Download files: partial first, then missing
                files_to_download = []
                
                # Add partial files first (for resuming)
                for srr, link, filename, local_size, remote_size, status in partial_files:
                    files_to_download.append((srr, link, filename, local_size, remote_size, "Partial"))
                
                # Add missing files (new downloads)
                for srr, link, filename, local_size, remote_size, status in missing_files:
                    files_to_download.append((srr, link, filename, local_size, remote_size, "Missing"))
                
                total_to_download = len(files_to_download)
                
                if total_to_download > 0:
                    print(f"  ⬇️ Downloading {total_to_download} files via Aspera ({len(partial_files)} to resume, {len(missing_files)} new)...")
                    for j, (srr, link, filename, local_size, remote_size, status) in enumerate(files_to_download, 1):
                        success, message = download_file(link, outdir, bandwidth, filename, j, total_to_download)
                        if not success:
                            print(f"      ⚠️ Failed: {message}")
                
                summary.append({
                    "Dataset": acc,
                    "Type": acc_type,
                    "Total files": len(links),
                    "Complete": len(existing_files),
                    "Downloaded": total_to_download,
                    "Status": f"{len(existing_files)} complete, {total_to_download} downloaded"
                })
                
    except Exception as e:
        print(f"✗ Error processing accessions: {str(e)}")
        import traceback
        traceback.print_exc()
    
    return summary
