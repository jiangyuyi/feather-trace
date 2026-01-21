# FeatherTrace Architecture Documentation

**Version:** 1.3
**Date:** 2026-01-21

## 1. System Overview

FeatherTrace is an automated post-processing and management system for bird photography. It transforms raw field photos into an organized, identified, and searchable digital library.

### Core Philosophy
*   **Privacy First**: Default local processing (BioCLIP) with optional cloud acceleration (Dongniao/HF).
*   **Safety**: Non-destructive to raw files. Hash-based deduplication to prevent redundant processing.
*   **Stability**: Optimized for consumer hardware (RTX 4060 Laptop target) with FP16 precision and batching.

---

## 2. Directory Structure

```text
feather_trace/
├── config/
│   ├── settings.yaml         # Main public configuration (Paths, Thresholds)
│   ├── secrets.yaml          # [GitIgnored] Private Keys (Dongniao/HF API)
│   ├── ioc_list.xlsx         # IOC World Bird List Source
│   ├── china_bird_list.txt   # Whitelist for 'China' region mode
│   └── foreign_countries.txt # Keywords for Auto-Region detection
├── data/
│   ├── db/
│   │   └── feathertrace.db   # SQLite Database
│   ├── models/               # Local Model Cache
│   │   ├── bioclip/          # BioCLIP v1 weights
│   │   └── bioclip-2/        # BioCLIP v2 weights
│   ├── raw/                  # [Input] Raw photos organized by folder
│   └── processed/            # [Output] Cropped & Renamed photos
├── docs/                     # Documentation
├── scripts/                  # Utilities (Import, Reset, Test)
├── src/
│   ├── core/                 # Computer Vision (YOLO, OpenCV)
│   ├── metadata/             # Data Layer (IOCManager, ExifTool)
│   ├── recognition/          # Inference Engines (Local, Dongniao, HF)
│   ├── utils/                # Helpers (Config Loader)
│   ├── web/                  # FastAPI Web Application
│   └── pipeline_runner.py    # Main ETL Entry Point
└── tests/                    # Unit Tests
```

---

## 3. Key Components

### 3.1. The ETL Pipeline (`src/pipeline_runner.py`)
The pipeline orchestrates the flow of data:
1.  **Ingest**: Scans `data/raw`. Parses folder names to determine `Location` and `Date`.
2.  **Deduplication**: Calculates partial SHA256 hash of the source file. Skips if hash exists in DB.
3.  **Region Strategy**:
    *   **Auto Mode**: Checks if folder location contains a country name from `foreign_countries.txt`.
        *   Match -> Use Global Taxonomy.
        *   No Match -> Use China Taxonomy (subset).
4.  **Processing**:
    *   **Detection**: YOLOv8 (`src/core/detector.py`) finds bird bounding boxes.
    *   **Quality**: Laplacian variance check (`src/core/quality.py`) filters blurry images.
    *   **Cropping**: Extracts the subject with padding.
5.  **Recognition**: Dispatches to the configured engine.
6.  **Archiving**: Writes Metadata (IPTC/XMP) and moves result to `data/processed`.
7.  **Indexing**: Records metadata, file hash, and original path in SQLite.

### 3.2. Recognition Engines (`src/recognition`)
Designed with a Strategy Pattern to support multiple backends:

*   **Local (BioCLIP)**:
    *   Supports `bioclip` and `bioclip-2`.
    *   **Optimizations**: FP16 precision, Autocast, Text Feature Caching (1000x speedup for subsequent images), Batching.
*   **Dongniao API**:
    *   Specialized for Chinese birds.
    *   Robust parsing for inconsistent API response formats (List vs Dict).
*   **HuggingFace API**:
    *   Standard Zero-Shot classification via `router.huggingface.co`.

### 3.3. Data & Metadata (`src/metadata`)
*   **IOCManager**:
    *   Manages `feathertrace.db`.
    *   **Schema**:
        *   `taxonomy`: Imported from IOC Excel. Support fuzzy search.
        *   `photos`: Stores identifying info, confidence, hash, and path mapping.
    *   **Self-Healing**: Auto-imports taxonomy if table is empty on startup.
*   **Config Loader**:
    *   Merges `settings.yaml` and `secrets.yaml` to ensure security.

### 3.4. Web Interface (`src/web`)
A FastAPI application serving a Bootstrap 5 frontend.
*   **Gallery**: Grid view with "Lazy Loading".
*   **Interaction**:
    *   **Toggle View**: Instant switch between Cropped and Raw image (mapped via DB).
    *   **Edit**: Fuzzy search dropdown to manually correct species.
*   **Admin**: Dashboard for statistics and **System Reset** (handles file locking robustness).

---

## 4. Data Flow

1.  **User** places photos in `data/raw/20231020_Park`.
2.  **User** runs `python src/pipeline_runner.py`.
    *   Pipeline reads config & secrets.
    *   Pipeline loads Taxonomy.
    *   Pipeline processes images -> updates DB.
3.  **User** starts `python src/web/app.py`.
    *   App initializes DB connection (safe check).
    *   User browses `http://localhost:8000`.
    *   User notices wrong ID -> Clicks Edit -> Searches "Sparrow" -> Saves.
    *   App updates DB `primary_bird_cn` and sets `confidence` to 1.0.

---

## 5. Security & Stability Features

*   **Secrets Management**: API Keys are isolated in `secrets.yaml` (GitIgnored).
*   **Concurrency**: Database connections use `timeout=30.0` and proper closing logic to prevent locking on Windows.
*   **Resilience**:
    *   Pipeline skips already processed files (Dedup).
    *   Web Admin allows "Force Reset" even if files are locked (Rename-then-Delete strategy).
    *   Pipeline auto-recovers missing taxonomy data.
