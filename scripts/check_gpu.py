import torch
import sys
import time

print(f"Python Version: {sys.version}")
print(f"PyTorch Version: {torch.__version__}")

if not torch.cuda.is_available():
    print("CUDA is NOT available. Aborting test.")
    sys.exit(0)

print(f"CUDA Available: Yes")
print(f"Current Device: {torch.cuda.get_device_name(0)}")
print(f"CUDA Version: {torch.version.cuda}")

try:
    print("\n--- Starting Tensor Computation Test ---")
    # 1. Allocate small tensor
    print("Allocating tensor on GPU...")
    x = torch.rand(1000, 1000).cuda()
    y = torch.rand(1000, 1000).cuda()
    
    # 2. Perform computation
    print("Performing matrix multiplication...")
    start = time.time()
    z = torch.matmul(x, y)
    torch.cuda.synchronize() # Wait for completion
    end = time.time()
    
    print(f"Computation successful! Time taken: {end - start:.4f}s")
    print("GPU seems stable for basic operations.")
    
except Exception as e:
    print(f"\nCRITICAL ERROR during GPU test: {e}")