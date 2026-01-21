import pytest
import os
from pathlib import Path
from src.pipeline_runner import FeatherTracePipeline

# Mocking the pipeline to avoid loading heavy models during init
class MockPipeline(FeatherTracePipeline):
    def __init__(self):
        # Skip super init
        pass

def test_file_hash(tmp_path):
    # Create a dummy file
    p = tmp_path / "test_file.jpg"
    p.write_bytes(b"A" * 5000 + b"B" * 5000 + b"C" * 5000)
    
    pipeline = MockPipeline()
    h1 = pipeline._calculate_file_hash(p)
    
    # Modify middle should verify partial hash logic?
    # Our hash logic reads start, middle, end.
    # Total 15000 bytes.
    # Read 4096 (start) -> "AAAA..."
    # Seek size//2 = 7500. Read 4096 -> "BBBB..."
    # Seek -4096. Read 4096 -> "CCCC..."
    
    # Create duplicate file
    p2 = tmp_path / "test_file_2.jpg"
    p2.write_bytes(b"A" * 5000 + b"B" * 5000 + b"C" * 5000)
    h2 = pipeline._calculate_file_hash(p2)
    
    assert h1 == h2
    
    # Create diff file (diff at end)
    p3 = tmp_path / "test_file_3.jpg"
    p3.write_bytes(b"A" * 5000 + b"B" * 5000 + b"D" * 5000)
    h3 = pipeline._calculate_file_hash(p3)
    
    assert h1 != h3
