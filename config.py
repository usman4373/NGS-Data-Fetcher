"""
Configuration settings for the Aspera downloader
"""
import os

# ===================== CONFIG =====================
ASCP_PATH = "ascp"
ASPERA_KEY = os.path.expanduser(
    "~/anaconda3/pkgs/aspera-cli-3.9.6-h5e1937b_0/etc/asperaweb_id_dsa.openssh"
)
SSH_PORT = "33001"
