"""
Progress tracking utilities
"""
import time
import subprocess
import os

def download_file(link, target_dir, bandwidth, filename=None, counter=None, total_files=None):
    """Download file using Aspera only (converts FTP links if needed)"""
    from config import ASCP_PATH, ASPERA_KEY, SSH_PORT
    from utils.helpers import normalize_ftp_link, convert_ftp_to_aspera, get_remote_file_size
    from utils.file_utils import format_file_size, format_time
    
    # Step 1: Normalize and convert FTP to Aspera if needed
    original_link = link
    
    # Check if it's already an Aspera link
    is_aspera_link = "@" in link and ":" in link
    
    if not is_aspera_link:
        # First normalize the link
        normalized_link = normalize_ftp_link(link)
        if normalized_link and normalized_link.startswith("ftp://"):
            link = normalized_link
        
        # Then convert to Aspera
        aspera_link = convert_ftp_to_aspera(link)
        if aspera_link:
            link = aspera_link
        else:
            return False, "FTP link not convertible to Aspera"
    
    # Step 2: Extract filename
    if not filename:
        if "@" in link and ":" in link:
            filename = link.split(":")[-1].split("/")[-1]
        else:
            filename = link.split("/")[-1]
    
    # Clean filename (remove query parameters if any)
    filename = filename.split('?')[0]
    
    target_path = os.path.join(target_dir, filename)
    
    # Step 3: Get remote file size
    remote_size = get_remote_file_size(link)
    remote_size_formatted = format_file_size(remote_size)
    
    # Step 4: Check if file already exists and handle partial downloads
    resume_download = False
    if os.path.exists(target_path):
        local_size = os.path.getsize(target_path)
        
        if remote_size:
            if local_size == remote_size:
                counter_str = f"[{counter}/{total_files}] " if counter else ""
                print(f"{counter_str}✓ Already downloaded: {filename} ({remote_size_formatted})")
                return True, f"Already downloaded ({remote_size_formatted})"
            elif local_size < remote_size:
                print(f"  ↻ Partial file found: {filename} ({format_file_size(local_size)}/{remote_size_formatted}) - will resume")
                resume_download = True
                # Don't remove the file - Aspera will resume it with -k flag
            else:
                print(f"  ⚠️ Local file larger than remote: {filename}. Re-downloading...")
                try:
                    os.remove(target_path)
                except:
                    pass
        else:
            print(f"  ⚠️ Could not verify remote size for {filename}. Re-downloading...")
            if os.path.exists(target_path):
                try:
                    os.remove(target_path)
                except:
                    pass

    # Step 5: Aspera command
    counter_str = f"[{counter}/{total_files}] " if counter else ""
    print(f"{counter_str}⬇️ Downloading {filename} ({remote_size_formatted})...")
    
    # Build Aspera command
    cmd = [
        ASCP_PATH,
        "-QT",  # disable encryption for faster transfer
        "-l", bandwidth,
        "-P", SSH_PORT,
        "-k", "1",
        "-i", ASPERA_KEY,
        link,
        target_dir
    ]

    try:
        start_time = time.time()

        # Run the download process (do NOT pipe stdout)
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL
        )

        # Progress tracking via local file size (reliable)
        last_size = 0
        last_check = start_time

        while process.poll() is None:
            time.sleep(1)
            current_time = time.time()

            if os.path.exists(target_path):
                current_size = os.path.getsize(target_path)
                delta_bytes = current_size - last_size
                delta_time = current_time - last_check

                if delta_time > 0 and delta_bytes > 0:
                    current_speed = delta_bytes / delta_time
                    speed_str = format_file_size(current_speed) + "/s"

                    if remote_size:
                        remaining_bytes = remote_size - current_size
                        if remaining_bytes > 0 and current_speed > 0:
                            eta = format_time(remaining_bytes / current_speed)
                        else:
                            eta = "--:--:--"

                        percent = min(100, int((current_size / remote_size) * 100))
                        print(
                            f"\r{counter_str}  Progress: {percent:3d}% | "
                            f"Speed: {speed_str:>10} | ETA: {eta:>8}",
                            end="",
                            flush=True
                        )
                    else:
                        print(
                            f"\r{counter_str}  Downloaded: {format_file_size(current_size)} | "
                            f"Speed: {speed_str:>10}",
                            end="",
                            flush=True
                        )

                last_size = current_size
                last_check = current_time

        process.wait()
        print()  # New line after progress bar
        
        # Step 6: Verify download
        if process.returncode == 0:
            if os.path.exists(target_path):
                final_size = os.path.getsize(target_path)
                elapsed = time.time() - start_time
                
                if elapsed > 0:
                    speed_bps = final_size / elapsed
                    speed_str = format_file_size(speed_bps) + "/s"
                    
                    if remote_size and final_size == remote_size:
                        print(f"{counter_str}✓ Complete: {filename} ({format_file_size(final_size)}, avg speed: {speed_str})")
                        return True, f"Complete ({format_file_size(final_size)})"
                    else:
                        print(f"{counter_str}✓ Downloaded: {filename} ({format_file_size(final_size)}, avg speed: {speed_str})")
                        return True, f"Downloaded ({format_file_size(final_size)})"
                else:
                    print(f"{counter_str}✓ Downloaded: {filename} ({format_file_size(final_size)})")
                    return True, f"Downloaded ({format_file_size(final_size)})"
            else:
                print(f"{counter_str}✗ File not created: {filename}")
                return False, "File not created"
        else:
            print(f"{counter_str}✗ Aspera download failed for {filename}: Exit code {process.returncode}")
            
            return False, f"Aspera failed: Exit code {process.returncode}"
            
    except FileNotFoundError:
        print(f"{counter_str}✗ Aspera executable not found: {ASCP_PATH}")
        return False, "Aspera not installed"
    except Exception as e:
        print(f"{counter_str}✗ Unexpected error for {filename}: {str(e)}")
        return False, f"Error: {str(e)}"
    