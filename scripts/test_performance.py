import os
import sys
import torch
import time
import logging
import psutil
from pathlib import Path

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.recognition.inference_local import LocalBirdRecognizer

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(message)s')

def get_gpu_memory():
    if torch.cuda.is_available():
        return torch.cuda.memory_allocated(0) / 1024**2
    return 0

def test_performance():
    print("=== FeatherTrace Performance Optimization Test ===")
    
    # 1. Setup Test Data
    # Generate 10,000 dummy species to simulate full IOC list
    print(f"Generating 10,000 candidate labels...")
    candidates = [f"Species {i}" for i in range(10000)]
    # Add some real ones to match the image if possible, though not strictly needed for perf test
    candidates.append("Passer montanus") 
    
    # Find test image
    test_image = Path("data/raw/20231020_TestPark/test_bird.jpg")
    if not test_image.exists():
        # Fallback
        for root, dirs, files in os.walk("data/raw"):
            for f in files:
                if f.lower().endswith(('.jpg', '.jpeg')):
                    test_image = Path(root) / f
                    break
            if test_image.exists(): break
            
    if not test_image.exists():
        print("Error: No test images found.")
        return

    # 2. Initialize Model
    print("\n--- Initializing Model ---")
    mem_before_load = get_gpu_memory()
    start_load = time.time()
    recognizer = LocalBirdRecognizer(device="cuda")
    load_time = time.time() - start_load
    mem_after_load = get_gpu_memory()
    print(f"Model Load Time: {load_time:.2f}s")
    print(f"Model Memory Delta: {mem_after_load - mem_before_load:.2f} MB")

    # 3. First Prediction (Cold Start - Encoding Text)
    print("\n--- Run 1: Cold Start (Encoding 10,000 Text Labels) ---")
    torch.cuda.reset_peak_memory_stats()
    start_time = time.time()
    
    recognizer.predict(str(test_image), candidates, top_k=5)
    
    end_time = time.time()
    peak_mem = torch.cuda.max_memory_allocated(0) / 1024**2
    curr_mem = get_gpu_memory()
    
    print(f"Time Taken: {end_time - start_time:.4f}s")
    print(f"Peak Memory: {peak_mem:.2f} MB")
    print(f"Current Memory (with Cache): {curr_mem:.2f} MB")
    
    # 4. Second Prediction (Warm Start - Using Cache)
    print("\n--- Run 2: Warm Start (Using Cached Features) ---")
    torch.cuda.reset_peak_memory_stats()
    start_time = time.time()
    
    recognizer.predict(str(test_image), candidates, top_k=5)
    
    end_time = time.time()
    peak_mem = torch.cuda.max_memory_allocated(0) / 1024**2
    
    print(f"Time Taken: {end_time - start_time:.4f}s")
    print(f"Peak Memory: {peak_mem:.2f} MB")

    print("\n=== Summary ===")
    print("Optimization Validation:")
    print("1. Batching effective? Yes, if Run 1 Peak Memory < 2GB (approx).")
    print("2. Caching effective? Yes, if Run 2 is significantly faster than Run 1.")

if __name__ == "__main__":
    test_performance()
