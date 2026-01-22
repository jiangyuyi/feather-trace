import logging
import sqlite3
import sys
import yaml
import shutil
import os
import gc
import asyncio
import threading
from contextlib import asynccontextmanager
from pathlib import Path
from fastapi import FastAPI, Request, HTTPException, WebSocket
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from typing import Optional, List

# Add project root to path for imports
BASE_DIR = Path(__file__).parent.parent.parent.absolute()
sys.path.append(str(BASE_DIR))

from src.metadata.ioc_manager import IOCManager
from src.metadata.exif_writer import ExifWriter # Added import
from src.utils.config_loader import load_config
from src.core.io.fs_manager import FileSystemManager
from src.pipeline_runner import FeatherTracePipeline # Import Pipeline

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize ExifWriter
exif_writer = ExifWriter()

# --- Task Manager (Background Pipeline) ---
class TaskManager:
    _instance = None
    
    def __init__(self):
        self.is_running = False
        self.should_stop = False # New flag
        self.logs = []
        self.websocket_clients = []
    
    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            cls._instance = TaskManager()
        return cls._instance
        
    def stop(self):
        self.should_stop = True

    def broadcast_log(self, message: str):
        self.logs.append(message)
        if len(self.logs) > 1000: self.logs.pop(0)
        
    def start_pipeline(self):
        if self.is_running:
            return False
        
        self.is_running = True
        self.logs = ["Starting pipeline..."]
        
        # Run in thread
        thread = threading.Thread(target=self._run_pipeline_thread, daemon=True)
        thread.start()
        return True

    def _run_pipeline_thread(self):
        try:
            # Setup custom logger to capture output
            log_capture = logging.getLogger()
            handler = ListLogHandler(self.logs)
            log_capture.addHandler(handler)
            
            runner = FeatherTracePipeline(str(BASE_DIR / "config/settings.yaml"))
            runner.run()
            
            logging.info("Pipeline execution completed.")
        except Exception as e:
            logging.error(f"Pipeline failed: {e}")
        finally:
            self.is_running = False
            log_capture.removeHandler(handler)

class ListLogHandler(logging.Handler):
    def __init__(self, log_list):
        super().__init__()
        self.log_list = log_list
    
    def emit(self, record):
        msg = self.format(record)
        self.log_list.append(msg)

task_manager = TaskManager.get_instance()

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_app_db()
    logger.info("Application started.")
    yield
    # Shutdown
    logger.info("Application shutting down...")
    if task_manager.is_running:
        logger.info("Stopping pipeline...")
        task_manager.stop()

app = FastAPI(lifespan=lifespan)

# Load config
config = load_config(str(BASE_DIR / "config" / "settings.yaml"), str(BASE_DIR / "config" / "secrets.yaml"))

db_path = BASE_DIR / config['paths']['db_path']
processed_dir = BASE_DIR / config['paths']['output']['root_dir'] 

# Initialize FileSystemManager for security checks
fs_manager = FileSystemManager.get_instance(config['paths'])
allowed_roots = fs_manager.local_provider.allowed_roots if fs_manager.local_provider.allowed_roots else []

logger.info(f"Project Base Directory: {BASE_DIR}")
logger.info(f"Processed Images Directory: {processed_dir}")
logger.info(f"Allowed Roots: {allowed_roots}")

if not processed_dir.exists():
    logger.error(f"Processed directory does not exist: {processed_dir}")
    processed_dir.mkdir(parents=True, exist_ok=True)

# Mount static files
app.mount("/static/processed", StaticFiles(directory=str(processed_dir)), name="processed")

# Mount allowed roots for "Original View"
for idx, root in enumerate(allowed_roots):
    if root.exists():
        app.mount(f"/static/roots/{idx}", StaticFiles(directory=str(root)), name=f"root_{idx}")

templates = Jinja2Templates(directory=str(BASE_DIR / "src" / "web" / "templates"))

# --- Initialization ---
# Call explicitly
def init_app_db():
    try:
        mgr = IOCManager(str(db_path))
        mgr.close()
        del mgr
        gc.collect()
    except Exception as e:
        logger.error(f"Startup DB Initialization failed: {e}")

# --- Helper ---
def get_db_conn():
    conn = sqlite3.connect(db_path, timeout=30.0, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def resolve_web_path(original_path_str: str) -> Optional[str]:
    """Resolves raw file path to /static/roots/... URL"""
    if not original_path_str: return None
    try:
        abs_path = Path(original_path_str).resolve()
        for idx, root in enumerate(allowed_roots):
            try:
                rel_path = abs_path.relative_to(root)
                return f"/static/roots/{idx}/{str(rel_path).replace(os.sep, '/')}"
            except ValueError: continue
    except Exception: pass
    return None

def resolve_processed_web_path(file_path_str: str) -> Optional[str]:
    """Resolves processed file path to /static/processed/... URL"""
    if not file_path_str: return None
    try:
        abs_path = Path(file_path_str).resolve()
        # Check if it's inside processed_dir
        if processed_dir in abs_path.parents:
            rel = abs_path.relative_to(processed_dir)
            return f"/static/processed/{str(rel).replace(os.sep, '/')}"
    except Exception: pass
    return None

# --- API Models ---
class UpdateLabelRequest(BaseModel):
    photo_id: int
    scientific_name: str
    chinese_name: str

# --- Routes ---

@app.get("/", response_class=HTMLResponse)
def index(request: Request, q: str = ""):
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
    
    display_photos = []
    for p in photos:
        p_dict = dict(p)
        p_dict['web_raw_path'] = resolve_web_path(p_dict.get('original_path'))
        
        # New logic for nested processed paths
        # We rely on 'file_path' column which stores absolute path
        p_dict['web_processed_path'] = resolve_processed_web_path(p_dict.get('file_path'))
        
        display_photos.append(p_dict)

    conn.close()
    
    return templates.TemplateResponse("index.html", {
        "request": request, 
        "photos": display_photos,
        "query": q
    })

@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    conn = get_db_conn()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT COUNT(*) FROM photos")
        total_photos = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(DISTINCT scientific_name) FROM photos")
        total_species = cursor.fetchone()[0]
    except:
        total_photos = 0
        total_species = 0
    finally:
        conn.close()
    
    stats = {
        "total_photos": total_photos,
        "total_species": total_species,
        "storage_usage": 0 # TODO: Calculate properly for nested structure
    }
    return templates.TemplateResponse("admin.html", {"request": request, "stats": stats})

@app.post("/api/pipeline/start")
def start_pipeline():
    if task_manager.is_running:
        return {"status": "error", "message": "Pipeline already running"}
    
    task_manager.start_pipeline()
    return {"status": "success", "message": "Pipeline started"}

@app.websocket("/ws/progress")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    try:
        last_index = 0
        while True:
            current_len = len(task_manager.logs)
            if current_len > last_index:
                new_logs = task_manager.logs[last_index:current_len]
                for log in new_logs:
                    await websocket.send_text(log)
                last_index = current_len
            
            await asyncio.sleep(0.5)
    except asyncio.CancelledError:
        # Handle server shutdown cancellation
        pass
    except Exception as e:
        # Expected disconnect or other error
        pass

@app.get("/download_raw")
def download_raw(path: str):
    # path parameter is expected to be a web path suffix or relative path
    # But since we have multiple roots, this is tricky.
    # Better to rely on static serving for viewing.
    # If user wants to "download", they can right click -> save as on the served image.
    # Implementing a generic download endpoint for arbitrary files is complex with multiple roots.
    # We will skip this for now and rely on static mounts.
    return {"error": "Use context menu to save image"}

# Existing APIs (search, update, reset) ... 
# (Keep reset logic but simplify for brevity in this rewrite, ensure full logic is present in final file)

@app.post("/api/admin/reset")
def reset_system():
    try:
        # 1. Clear DB
        if db_path.exists():
            gc.collect()
            temp_path = db_path.with_suffix(".db.del")
            try:
                if temp_path.exists(): os.remove(temp_path)
                os.rename(db_path, temp_path)
                os.remove(temp_path)
            except: pass
            
        # 2. Clear Processed
        # WARNING: This deletes the entire root output dir!
        if processed_dir.exists():
            for item in processed_dir.iterdir():
                try:
                    if item.is_file(): item.unlink()
                    elif item.is_dir(): shutil.rmtree(item)
                except: pass

        init_app_db()
        
        # Re-import taxonomy
        mgr = IOCManager(str(db_path))
        if mgr.conn.execute("SELECT count(*) FROM taxonomy").fetchone()[0] == 0:
             mgr.import_from_excel(str(BASE_DIR / config['paths']['ioc_list_path']))
        mgr.close()
        
        return {"status": "success"}
    except Exception as e:
        return {"status": "error", "detail": str(e)}

@app.get("/api/search_species")
def search_species(q: str):
    manager = IOCManager(str(db_path))
    res = manager.search_species(q, limit=20)
    manager.close()
    return res

@app.post("/api/update_label")
def update_label(req: UpdateLabelRequest):
    manager = IOCManager(str(db_path))
    
    # 1. Fetch photo details BEFORE update to get file paths
    manager.cursor.execute("SELECT * FROM photos WHERE id = ?", (req.photo_id,))
    photo = manager.cursor.fetchone()
    
    if not photo:
        manager.close()
        raise HTTPException(status_code=404, detail="Photo not found")
    
    photo = dict(photo)
    
    # 2. Get extra bird info (Family) for tags
    bird_info = manager.get_bird_info(req.scientific_name)
    family_cn = bird_info['family_cn'] if bird_info else ""
    
    # 3. Update DB
    manager.update_photo_species(req.photo_id, req.scientific_name, req.chinese_name)
    manager.close()
    
    # 4. Prepare Tags
    # Description: Just the bird name, no "AI" or score.
    # Keywords: [Chinese Name, Location, Family, Scientific Name]
    tags = {
        "IPTC:Keywords": [req.chinese_name, photo['location_tag'], family_cn, req.scientific_name],
        "XMP:Description": req.chinese_name
    }
    
    # 5. Update Metadata for Processed Image
    processed_path = photo.get('file_path')
    if processed_path and os.path.exists(processed_path):
        exif_writer.write_metadata(processed_path, tags)
    
    # 6. Update Metadata for Original Image (if exists)
    original_path = photo.get('original_path')
    if original_path and os.path.exists(original_path):
        # We might want to append "FeatherTrace" to keywords if not present, 
        # but purely replacing with the new set is safer to keep consistency with the new ID.
        # Ideally, we should read existing keywords and merge, but for now, 
        # strictly following the requirement "Update tags" with the corrected info.
        # Adding "FeatherTrace" tag to mark it as touched by our system is good practice though.
        
        # Re-creating the logic from pipeline_runner:
        source_tags = tags.copy()
        source_tags["IPTC:Keywords"] = source_tags["IPTC:Keywords"] + ["FeatherTrace"]
        
        exif_writer.write_metadata(original_path, source_tags)

    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host=config['web']['host'], port=config['web']['port'])