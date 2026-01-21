# Project Specification: FeatherTrace
**Version:** 1.1
**Project Name:** feather_trace
**Language:** Python 3.10+
**Description:** A personal bird photography automation pipeline and management system. It automates focus detection, cropping, AI species recognition (BioCLIP), metadata injection, and provides a local web interface for searching, retrieval, and manual annotation.

---

## 1. System Architecture

The system consists of three main components:
1.  **The Pipeline (ETL):** Ingests raw photos, processes them (deduplication, quality check, cropping), identifies species, and archives them.
2.  **The Database:** Stores IOC taxonomy data and photo metadata (including raw/processed mapping) for fast retrieval.
3.  **The Web Interface:** A lightweight local server to browse, search, edit, and download images.

---

## 2. Directory Structure

```text
feather_trace/
├── config/
│   ├── settings.yaml         # Configuration (API keys, thresholds, paths)
│   └── ioc_list.xlsx         # IOC World Bird List (Excel Source)
├── data/
│   ├── db/
│   │   └── feathertrace.db   # SQLite Database
│   ├── raw/                  # Input folder for raw images (Read-only)
│   └── processed/            # Output folder for archived images
├── src/
│   ├── core/
│   │   ├── detector.py       # YOLOv8 logic (Object Detection)
│   │   ├── quality.py        # OpenCV logic (Blur/Sharpness detection)
│   │   └── processor.py      # Image manipulation (Pillow cropping/resizing)
│   ├── recognition/
│   │   ├── bioclip_base.py   # Abstract Base Class for inference
│   │   ├── inference_local.py# BioCLIP model (FP16 optimized)
│   ├── metadata/
│   │   ├── ioc_manager.py    # DB interaction for Taxonomy & Photos
│   │   └── exif_writer.py    # PyExifTool wrapper for writing metadata
│   ├── web/
│   │   ├── app.py            # FastAPI entry point
│   │   ├── templates/        # HTML templates (Admin, Index)
│   │   └── static/           # CSS/JS
│   └── pipeline_runner.py    # Main ETL script
├── requirements.txt
└── README.md
```

---

## 3. Module Requirements

### A. Pre-processing (`src/core`)
1.  **Object Detection (YOLOv8):**
    * Detect objects with class ID `14` (Bird).
2.  **Quality Check (OpenCV):**
    * Laplacian Variance method for sharpness score.
3.  **Deduplication:**
    * **Hash-based**: Calculate partial SHA256 of raw files to prevent re-processing.

### B. Recognition Engine (`src/recognition`)
1.  **BioCLIP Optimization:**
    * **FP16 Inference**: Enabled for RTX 30/40 series GPUs to prevent memory spikes.
    * **Caching**: Cache text embeddings for 1000x faster inference.
    * **Batching**: Process text labels in batches to avoid OOM.

### C. Data & Metadata (`src/metadata`)
1.  **IOC Database Integration:**
    * Import full taxonomy from Excel (`ioc_list.xlsx`).
    * Support fuzzy search (Chinese/Scientific names).
2.  **ExifTool Integration:**
    * Write `IPTC:Keywords` and `XMP:Description`.

### D. Database Schema (SQLite)

**Table 1: `taxonomy`**
* `id`, `scientific_name`, `chinese_name`, `family_cn`, `order_cn`

**Table 2: `photos`**
* `id`, `file_path` (Processed), `filename`
* `original_path` (Absolute path to RAW file)
* `file_hash` (For deduplication)
* `captured_date`, `location_tag`
* `primary_bird_cn`, `scientific_name`, `confidence_score`

### E. Web Interface (`src/web`)
1.  **Framework:** FastAPI.
2.  **Features:**
    * **Gallery View:** Grid layout with Toggle View (Raw/Processed).
    * **Search:** Filter by species, location, date.
    * **Manual Annotation:** Modal to correct species using fuzzy search dropdown.
    * **Admin Dashboard:** System stats and "Reset System" functionality.
    * **Download:** Download both processed and raw images.

---

## 4. Workflows

### Workflow 1: Data Ingest (`pipeline_runner.py`)
1.  **Scan:** Iterate `data/raw`.
2.  **Dedup:** Check file hash against DB. Skip if exists.
3.  **Process:** Detect -> Crop -> Recognize.
4.  **Archive:** Save to `data/processed`.
5.  **Index:** Insert into DB with `original_path` and `file_hash`.

### Workflow 2: Web Interaction
1.  User browses gallery.
2.  User clicks "Toggle" to compare Raw vs Processed.
3.  If recognition is wrong, User clicks "Edit", searches for correct species, and saves.
4.  Backend updates DB record (Confidence set to 1.0).

---
