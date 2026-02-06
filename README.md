![cover](images/cover.png)

## 📑 Table of contents

1. [📝 Overview](#-overview)
2. [📦 Installation](#-installation)
3. [🏃 How to run](#-how-to-run)
4. [📂 Input file formats](#-input-file-formats)
5. [🔄 Workflow](#-workflow)
6. [📚 Citation](#-citation)
7. [🤝 Acknowledgements](#-acknowledgements)
8. [👥 Contributions](#-contributions)
9. [📣 Issues and Support](#-issues-and-support)


## 📝 Overview

- <p align="justify"> NGS-Data-Fetcher is a command-line tool that supports downloading raw FASTQ.gz files for a broad range of popular sequencing assays; including bulk and single-cell RNA-seq, ATAC-seq, ChIP-seq, Hi-C, whole-genome/exome sequencing, metagenomics, immune-repertoire sequencing, and other high-throughput NGS datasets, from ENA (European Nucleotide Archive) and GEO (Gene Expression Omnibus) via IBM Aspera. </p>
- It requires a dataset accession ID, and the script automatically retrieves and downloads all available raw `FASTQ.gz` files for the corresponding study.
- It also supports custom ftp/aspera links to download specific samples rather than the whole dataset(s).
- It supports high-speed downloads, resumable transfers, and robust metadata handling without requiring a VPN.
- Designed for large-scale sequencing projects where speed, stability, and automation matter.

#### ✨ Key Features

- 🚀 IBM Aspera acceleration (no VPN required)
- 🔄 Automatic resume of partial downloads
- 📊 Real-time progress, speed, and ETA reporting
- 🧠 Automatic accession type detection (ENA vs GEO)
- 📋 Metadata download for ENA and GEO datasets
- 📂 Organized output directories per dataset
- 🧾 Final CSV summary of all downloads
- ⚙️ Fully interactive terminal-based UI

#### **Note: It downloads those datasets that are publicly available; restricted datasets are not supported.**

## 📦 Installation

- Prerequisites
    - Python 3.8 or higher
    - Aspera CLI installed and configured

### Step-by-Step Setup

1. Clone the repository
    
```
git clone https://github.com/usman4373/NGS-Data-Fetcher
tar -xvf NGS-Data-Fetcher-main.zip
cd NGS-Data-Fetcher-main
```

2. Create conda environment

```
conda create --name ngsdata python=3.11 -y
conda activate ngsdata
conda install hcc::aspera-cli -y
```

3. Verify

```
which ascp
ascp -h
```

4. Check Aspera key location

```
~/anaconda3/pkgs/aspera-cli-3.9.6-h5e1937b_0/etc/asperaweb_id_dsa.openssh
```

5. Install python package

```
pip install requests
```

## 🏃 How to Run

- Starting the tool

```
python main.py
```

- Configuration Steps
    - Set Output Directory
    - Select Download Mode
        - ENA/GEO (full dataset): For accession IDs (PRJNA873625, GSE12345)
        - Custom links (CSV/TSV): For pre-generated download links
    - Configure Aspera Settings
        - Choose appropriate bandwidth based on your network
    - Upload Input File
        - Upload a text file with accession IDs (for ENA/GEO mode)
        - Upload CSV/TSV file with download links (for Custom links mode)
    - Start Download
        - Click the "🚀 Download Dataset(s)" button

## 📂 Input File Formats

1. ENA/GEO (Full Dataset Download)

- File format: Plain text (.txt) with one accession per line

```
PRJNA545678
GSE123456
GSE928376
GSE987654
PRJNA982625
```

2. Custom Links (CSV/TSV)
- File format: CSV or TSV with specific columns
- Required columns:
    - dataset_accession: Identifier for the dataset
    - accession_ids: Sample/run accession (optional)
    - ftp_links: Full download link (Aspera or FTP)

Example CSV/TSV:

| dataset_accession | accession_ids | ftp_links (or aspera links)                                                            |
| ----------------- | ------------ | --------------------------------------------------------------------------------------- |
| PRJNA9826         | SRR12345678  | `era-fasp@fasp.sra.ebi.ac.uk:/vol1/fastq/SRR123/078/SRR12345678/SRR12345678_1.fastq.gz` |
| GSE928376         | SRR87654321  | `ftp://ftp.sra.ebi.ac.uk/vol1/fastq/SRR876/021/SRR87654321_1.fastq.gz`                  |
| Project_X         | SRR55555555  | `era-fasp@fasp.sra.ebi.ac.uk:/vol1/fastq/SRR555/555/SRR55555555/SRR55555555_1.fastq.gz` |

## 🔄 Workflow

#### Step 1: Initialization

- User Input → File Upload → Configuration Validation

#### Step 2: Accession Processing

- For each accession the app:
    1. Detects type (ENA/GEO)
    2. Creates output directory
    3. Download metadata files
    4. Resolve to download links

#### NOTE: To support interrupted and resumed download sessions, the tool first verifies (Step 3) the local file state. This prevents re-downloading completed files while allowing partial and missing files to be efficiently resumed or fetched.

#### Step 3: File Status Check

- For each file the app:
    1. Checks if file exists locally
    2. Compare with remote file size
    3. Categorize as:
        - Complete (local size = remote size)
        - Partial (local size < remote size)
        - Missing (no local file)

#### **Note: To resume an interrupted download, ensure you provide the exact same input file and output directory path used previously.**

#### Step 4: Download Execution

- Priority order:
    1. Resume partial downloads
    2. Download missing files
    3. Skip already completed files

#### Step 5: Progress Monitoring

Real-time updates:
  - File progress percentage
  - Download speed
  - ETA
  - Errors/warnings

#### Step 6: Completion & Reporting

- Final steps:
    1. Generate summary report
    2. Save statistics to CSV
    3. Display completion metrics

#### Output Directory Structure

```
output_directory/
├── dataset_01/
│   ├── metadata_file
│   ├── SRR12345678_1.fastq.gz
│   └── SRR12345678_2.fastq.gz
├── dataset_02/
│   ├── metadata_file
│   └── SRR87654321.fastq.gz
└── download_summary.csv
```

## 📚 Citation

If you use this tool in your research, please cite:

```
NGS-Data-Fetcher. GitHub: https://github.com/usman4373/NGS-Data-Fetcher
```

## 🤝 Acknowledgements
    - European Nucleotide Archive (ENA) - For providing comprehensive nucleotide sequence data
    - Gene Expression Omnibus (GEO) - For hosting functional genomics data
    - NCBI SRA - For sequencing read archive access
    - IBM Aspera - For high-speed transfer protocol
    - Python libraries

#### Development

- <p align="justify"> This tool/workflow was developed to address the need for high-speed, reliable, batch downloading of public NGS data with proper error handling and progress tracking. </p>

## 👥 Contributions

- Contributions are welcome! Please:
    - Fork the repository
    - Create a feature branch
    - Submit a pull request with detailed description

## 📣 Issues and Support
- Report bugs via GitHub Issues
- Include error messages and reproduction steps
- For installation issues, include your system details

---
