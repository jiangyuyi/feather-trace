import os
import logging
from pathlib import Path

# 1. Set Hugging Face Mirror
os.environ["HF_ENDPOINT"] = "https://hf-mirror.com"

from huggingface_hub import snapshot_download

logging.basicConfig(level=logging.INFO)

def download_bioclip():
    model_name = "imageomics/bioclip"
    save_dir = Path("data/models/bioclip")
    
    print(f"--- Downloading {model_name} snapshot from {os.environ['HF_ENDPOINT']} ---")
    print(f"Target directory: {save_dir.absolute()}")
    
    try:
        # Download the entire repository snapshot
        snapshot_download(
            repo_id=model_name,
            local_dir=save_dir,
            local_dir_use_symlinks=False,  # Important for Windows compatibility
            resume_download=True
        )
        
        print(f"--- Success! Model snapshot saved to {save_dir} ---")
        print("You can now verify the contents of the folder.")
        
    except Exception as e:
        print(f"\nError downloading model: {e}")
        print("Tip: Check network or try setting HTTP_PROXY/HTTPS_PROXY environment variables if you are behind a corporate proxy.")

if __name__ == "__main__":
    download_bioclip()
