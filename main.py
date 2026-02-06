"""
Main entry point for the Aspera FASTQ Downloader
"""
import os
import sys
import csv
import traceback
from ui.terminal_ui import (
    print_header, check_aspera, get_user_input,
    process_custom_links_mode, process_ena_geo_mode
)

def main():
    """Main function"""
    print_header()
    
    # Check Aspera configuration
    if not check_aspera():
        print("\n❌ Please fix Aspera configuration and try again.")
        print("\n💡 Quick fix suggestions:")
        print("     Install Aspera CLI: `conda install hcc::aspera-cli -y`")
        return
    
    # Get user input
    output_dir, mode, input_file, bandwidth = get_user_input()
    
    # Create main output directory
    try:
        os.makedirs(output_dir, exist_ok=True)
        print(f"\n📁 Output directory: `{os.path.abspath(output_dir)}`")
    except Exception as e:
        print(f"✗ Cannot create output directory '{output_dir}': {str(e)}")
        return
    
    # Check if output directory is writable
    test_file = os.path.join(output_dir, ".write_test")
    try:
        with open(test_file, 'w') as f:
            f.write("test")
        os.remove(test_file)
    except Exception as e:
        print(f"✗ Output directory '{output_dir}' is not writable: {str(e)}")
        return
    
    print(f"\n🚀 Starting download with bandwidth: {bandwidth}")
    print(f"📊 Mode: {mode}")
    print("-" * 70)
    
    # Process based on mode
    if mode == "Custom links (CSV / TSV)":
        summary = process_custom_links_mode(output_dir, input_file, bandwidth)
    else:
        summary = process_ena_geo_mode(output_dir, input_file, bandwidth)
    
    # Show summary
    print(f"\n{'='*70}")
    print("✅ Download finished")
    print(f"{'='*70}")
    
    if summary:
        print("\n📊 Summary:")
        print("-" * 70)
        
        # Print summary table
        if summary:
            headers = list(summary[0].keys())
            
            # Calculate column widths
            col_widths = []
            for h in headers:
                max_width = len(str(h))
                for item in summary:
                    val = str(item.get(h, ""))
                    if len(val) > max_width:
                        max_width = len(val)
                col_widths.append(max_width + 2)  # padding
            
            # Print headers
            header_line = ""
            for i, h in enumerate(headers):
                header_line += str(h).ljust(col_widths[i])
            print(header_line)
            print("-" * len(header_line))
            
            # Print rows
            for item in summary:
                row_line = ""
                for i, h in enumerate(headers):
                    val = str(item.get(h, ""))
                    row_line += val.ljust(col_widths[i])
                print(row_line)
        
        # Show statistics
        print(f"\n📈 Statistics:")
        print(f"  Total Datasets: {len(summary)}")
        
        if summary and "Total files" in summary[0]:
            total_files = sum(item.get("Total files", 0) for item in summary if isinstance(item.get("Total files"), int))
            complete_files = sum(item.get("Complete", 0) for item in summary if isinstance(item.get("Complete"), int))
            downloaded_files = sum(item.get("Downloaded", 0) for item in summary if isinstance(item.get("Downloaded"), int))
            print(f"  Total Files: {total_files}")
            print(f"  Complete Files: {complete_files}")
            print(f"  Downloaded Files: {downloaded_files}")
        
        # Save summary to file
        summary_file = os.path.join(output_dir, "download_summary.csv")
        try:
            with open(summary_file, 'w', newline='') as f:
                if summary:
                    writer = csv.DictWriter(f, fieldnames=summary[0].keys())
                    writer.writeheader()
                    writer.writerows(summary)
            print(f"\n💾 Summary saved to: {summary_file}")
        except Exception as e:
            print(f"  ⚠️ Could not save summary file: {str(e)}")
    else:
        print("\n📭 No downloads were attempted.")
    
    print(f"\n🎉 All done! Files saved to: {output_dir}")

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n❌ Operation cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
