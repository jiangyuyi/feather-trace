from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
import sqlite3
import yaml
from pathlib import Path
import os

import logging
import sqlite3
import sys
import yaml
import shutil
import os
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

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI()

# Load config
config_path = BASE_DIR / "config" / "settings.yaml"
with open(config_path, 'r', encoding='utf-8') as f:
    config = yaml.safe_load(f)

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

# --- Helper ---
def get_db_conn():
    conn = sqlite3.connect(db_path)
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
    
    cursor.execute("SELECT COUNT(*) FROM photos")
    total_photos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(DISTINCT scientific_name) FROM photos")
    total_species = cursor.fetchone()[0]
    
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
            conn = get_db_conn() # Close any open connections first?
            conn.close() 
            # Force remove file
            try:
                os.remove(db_path)
            except PermissionError:
                # If file is locked, try truncating tables
                logger.warning("DB file locked, trying truncate...")
                conn = get_db_conn()
                conn.execute("DELETE FROM photos")
                conn.execute("DELETE FROM sqlite_sequence WHERE name='photos'")
                conn.commit()
                conn.close()

        # 2. Clear Processed Directory
        if processed_dir.exists():
            for item in processed_dir.iterdir():
                if item.is_file() or item.is_symlink():
                    item.unlink()
                elif item.is_dir():
                    shutil.rmtree(item)
        
        # 3. Re-init DB (Schema only)
        # IOCManager(str(db_path)).close() # This will create tables
        # But we also need to re-import taxonomy?
        # Actually, if we delete the file, we lose taxonomy.
        # Better strategy: Only delete FROM photos.
        
        # Let's retry strategy: Only clear 'photos' table and 'processed' dir.
        # This preserves the imported IOC taxonomy.
        conn = get_db_conn()
        conn.execute("DELETE FROM photos")
        conn.execute("DELETE FROM sqlite_sequence WHERE name='photos'")
        conn.commit()
        conn.close()
        
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
        return {"status": "success"}
    except Exception as e:
        logger.error(f"Update failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        manager.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['web']['host'], port=config['web']['port'])

def get_db_conn():
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn

@app.get("/", response_class=HTMLResponse)
async def index(request: Request, q: str = ""):
    conn = get_db_conn()
    cursor = conn.cursor()
    
    if q:
        # Search by name, location, or date
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
    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "photos": photos,
        "query": q
    })

@app.get("/download/{filename}")
async def download_file(filename: str):
    file_path = processed_dir / filename
    if file_path.exists():
        return FileResponse(path=file_path, filename=filename)
    return {"error": "File not found"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['web']['host'], port=config['web']['port'])
