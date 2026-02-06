"""
File and size formatting utilities
"""
def format_file_size(size_bytes):
    """Format file size in human-readable format"""
    if size_bytes is None:
        return "Unknown"
    
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0
    return f"{size_bytes:.1f} PB"

def format_time(seconds):
    """Format time in human-readable format"""
    if seconds is None or seconds < 0:
        return "--:--:--"
    
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours:02d}:{minutes:02d}:{secs:02d}"
    else:
        return f"{minutes:02d}:{secs:02d}"

def check_existing_files(output_dir, links):
    """Check which files already exist and compare with remote sizes"""
    import os
    from .helpers import get_remote_file_size, convert_ftp_to_aspera
    from .file_utils import format_file_size
    
    existing_files = []
    partial_files = []
    missing_files = []
    
    for srr, link in links:
        if link.startswith("ftp.") and not link.startswith("ftp://"):
            link = "ftp://" + link
        
        if link.startswith("ftp://"):
            link = convert_ftp_to_aspera(link)
            if not link:
                continue
        
        if "@" in link and ":" in link:
            filename = link.split(":")[-1].split("/")[-1]
        else:
            filename = link.split("/")[-1]
        
        # Clean filename
        filename = filename.split('?')[0]
        file_path = os.path.join(output_dir, filename)
        
        if os.path.exists(file_path):
            local_size = os.path.getsize(file_path)
            remote_size = get_remote_file_size(link)
            
            if remote_size:
                if local_size == remote_size:
                    existing_files.append((srr, link, filename, local_size, remote_size, "Complete"))
                elif local_size < remote_size:
                    partial_files.append((srr, link, filename, local_size, remote_size, f"Partial ({local_size}/{remote_size})"))
                else:
                    missing_files.append((srr, link, filename, local_size, remote_size, "Corrupted"))
            else:
                missing_files.append((srr, link, filename, local_size, None, "Unverifiable"))
        else:
            missing_files.append((srr, link, filename, 0, None, "Missing"))
    
    return existing_files, partial_files, missing_files
