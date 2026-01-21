import logging
import sqlite3
import sys
import yaml
import shutil
import os
import gc
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

# Add project root to path for imports
BASE_DIR = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(BASE_DIR))

from src.metadata.ioc_manager import IOCManager
from src.utils.config_loader import load_config

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load config
config = load_config(str(BASE_DIR / "config" / "settings.yaml"), str(BASE_DIR / "config" / "secrets.yaml"))

db_path = BASE_DIR / config['paths']['db_path']
processed_dir = BASE_DIR / config['paths']['processed_dir']
raw_dir = BASE_DIR / config['paths']['raw_dir']

logger.info(f"Project Base Directory: {BASE_DIR}")
logger.info(f"Processed Images Directory: {processed_dir}")
logger.info(f"Raw Images Directory: {raw_dir}")

if not processed_dir.exists():
    logger.error(f"Processed directory does not exist: {processed_dir}")

# Mount static files
app.mount("/static/processed", StaticFiles(directory=str(processed_dir)), name="processed")
# Mount raw files for "Original View"
if raw_dir.exists():
    app.mount("/static/raw", StaticFiles(directory=str(raw_dir)), name="raw")

templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))

# --- Initialization ---
def init_app_db():
    """Initialize DB schema on startup and ensure connection is closed immediately."""
    logger.info("Checking database schema...")
    try:
        # Create a transient manager just to init the DB
        mgr = IOCManager(str(db_path))
        mgr.close()
        del mgr
        gc.collect() # Force cleanup
    except Exception as e:
        logger.error(f"Startup DB Initialization failed: {e}")

# Run initialization
init_app_db()

# --- Helper ---
def get_db_conn():
    # Increased timeout to 30s to handle locking, check_same_thread for safety in async
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def get_dir_size(path: Path) -> float:
    total_size = 0
    if not path.exists(): return 0
    for dirpath, dirnames, filenames in os.walk(path):
        for f in filenames:
            fp = os.path.join(dirpath, f)
            if not os.path.islink(fp):
                total_size += os.path.getsize(fp)
    return round(total_size / (1024 * 1024), 2) # MB

# --- API Models ---
class UpdateLabelRequest(BaseModel):
    photo_id: int
    scientific_name: str
    chinese_name: str

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, q: str = ""):
    conn = get_db_conn()
    cursor = conn.cursor()
    
    if q:
        query = f"%{q}%"
        cursor.execute('''
            SELECT * FROM photos 
            WHERE primary_bird_cn LIKE ? 
               OR scientific_name LIKE ? 
               OR location_tag LIKE ? 
               OR captured_date LIKE ?
            ORDER BY captured_date DESC
        ''', (query, query, query, query))
    else:
        cursor.execute('SELECT * FROM photos ORDER BY captured_date DESC LIMIT 50')
    
    photos = cursor.fetchall()
    
    # Process photos to add relative original path for web serving
    display_photos = []
    for p in photos:
        p_dict = dict(p)
        if p_dict['original_path']:
            try:
                abs_orig = Path(p_dict['original_path'])
                rel_raw = abs_orig.relative_to(raw_dir)
                p_dict['web_raw_path'] = str(rel_raw).replace('\\', '/')
            except ValueError:
                p_dict['web_raw_path'] = None
        else:
            p_dict['web_raw_path'] = None
        display_photos.append(p_dict)

    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "photos": display_photos,
        "query": q
    })

@app.get("/admin", response_class=HTMLResponse)
async def admin_dashboard(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor()
    
    try:
        cursor.execute("SELECT COUNT(*) FROM photos")
        total_photos = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(DISTINCT scientific_name) FROM photos")
        total_species = cursor.fetchone()[0]
    except sqlite3.OperationalError:
        # Table might not exist if reset failed previously
        total_photos = 0
        total_species = 0
    finally:
        conn.close()
    
    storage_mb = get_dir_size(processed_dir)
    
    stats = {
        "total_photos": total_photos,
        "total_species": total_species,
        "storage_usage": storage_mb
    }
    
    return templates.TemplateResponse("admin.html", {
        "request": request,
        "stats": stats
    })

@app.post("/api/admin/reset")
async def reset_system():
    try:
        # 1. Clear Database (Delete file)
        if db_path.exists():
            # Force GC to clean up any lingering connection handles from this process
            gc.collect()
            
            # Try to rename first (sometimes works better than delete on locked files)
            # Then delete the renamed file
            temp_path = db_path.with_suffix(".db.del")
            try:
                if temp_path.exists(): os.remove(temp_path)
                os.rename(db_path, temp_path)
                os.remove(temp_path)
                logger.info("Database file deleted (via rename).")
            except (PermissionError, OSError) as e:
                # If file is locked, try truncating tables
                logger.warning(f"DB file locked ({e}), trying truncate...")
                try:
                    conn = get_db_conn()
                    # Check if table exists before delete
                    cursor = conn.cursor()
                    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='photos'")
                    if cursor.fetchone():
                        conn.execute("DELETE FROM photos")
                        conn.execute("DELETE FROM sqlite_sequence WHERE name='photos'")
                    conn.commit()
                    conn.close()
                except Exception as ex:
                    logger.error(f"Truncate failed: {ex}")
                    raise ex

        # 2. Clear Processed Directory
        if processed_dir.exists():
            for item in processed_dir.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Failed to delete {item}: {e}")
        
        # 3. Re-init DB (Schema + Taxonomy)
        logger.info("Re-initializing database schema...")
        init_app_db() # Use the robust init function
        
        # Check taxonomy
        manager = IOCManager(str(db_path))
        conn = manager.conn
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM taxonomy")
        if cursor.fetchone()[0] == 0:
            logger.info("Taxonomy empty after reset. Re-importing...")
            excel_path = BASE_DIR / config['paths']['ioc_list_path']
            if excel_path.exists():
                manager.import_from_excel(str(excel_path))
        
        manager.close()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return {"status": "error", "detail": str(e)}

        # 2. Clear Processed Directory
        if processed_dir.exists():
            for item in processed_dir.iterdir():
                try:
                    if item.is_file() or item.is_symlink():
                        item.unlink()
                    elif item.is_dir():
                        shutil.rmtree(item)
                except Exception as e:
                    logger.warning(f"Failed to delete {item}: {e}")
        
        # 3. Re-init DB (Schema + Taxonomy)
        # We use IOCManager to recreate tables immediately
        logger.info("Re-initializing database schema...")
        manager = IOCManager(str(db_path))
        
        # Check if taxonomy needs import (it will be empty if file was deleted)
        conn = manager.conn
        cursor = conn.cursor()
        cursor.execute("SELECT count(*) FROM taxonomy")
        if cursor.fetchone()[0] == 0:
            logger.info("Taxonomy empty after reset. Re-importing...")
            excel_path = BASE_DIR / config['paths']['ioc_list_path']
            if excel_path.exists():
                manager.import_from_excel(str(excel_path))
        
        manager.close()
        
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Reset failed: {e}")
        return {"status": "error", "detail": str(e)}

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = processed_dir / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    return {"error": "File not found"}

@app.get("/download_raw")
async def download_raw_file(path: str):
    # path is the relative path inside data/raw
    file_path = raw_dir / path
    # Security check to prevent path traversal
    if raw_dir not in file_path.resolve().parents:
         return {"error": "Access denied"}
         
    if file_path.exists():
        return FileResponse(path=file_path, filename=file_path.name)
    return {"error": "File not found"}

@app.get("/api/search_species")
async def search_species(q: str):
    if not q or len(q) < 1:
        return []
    
    manager = IOCManager(str(db_path))
    results = manager.search_species(q, limit=20)
    manager.close()
    return results

@app.post("/api/update_label")
async def update_label(req: UpdateLabelRequest):
    manager = IOCManager(str(db_path))
    try:
        manager.update_photo_species(req.photo_id, req.scientific_name, req.chinese_name)
        # Note: In a real app, we should also update the file EXIF and filename here,
        # but for now we just update the DB view.
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        manager.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['web']['host'], port=config['web']['port'])