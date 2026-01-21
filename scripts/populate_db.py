import sys
import os
import logging

# Add src to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.metadata.ioc_manager import IOCManager

logging.basicConfig(level=logging.INFO)

def populate():
    db_path = "data/db/feathertrace.db"
    xlsx_path = "config/Multiling IOC 15.1_d.xlsx"
    
    print(f"Populating {db_path} from {xlsx_path}...")
    
    manager = IOCManager(db_path)
    manager.import_ioc_data(xlsx_path)
    manager.close()
    
    print("Done.")

if __name__ == "__main__":
    populate()
