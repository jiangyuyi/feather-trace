# Project Specification: FeatherTrace
**Version:** 1.6
**Project Name:** feather_trace
**Language:** Python 3.10+
**Description:** A personal bird photography automation pipeline and management system. It automates focus detection, cropping, AI species recognition (BioCLIP/Dongniao/HF), metadata injection, and provides a local web interface for searching, retrieval, and manual annotation.

---

## 1. System Architecture

The system consists of three main components:
1.  **The Pipeline (ETL):** Ingests raw photos, processes them (deduplication, quality check, cropping), identifies species, and archives them. Supports recursive scanning with smart pruning based on date ranges.
2.  **The Database:** Stores IOC taxonomy data, photo metadata, scan history, and recognition candidates.
3.  **The Web Interface:** A lightweight local server to browse, search, edit, and download images.

---

## 2. Directory Structure

```text
feather_trace/
├── config/
│   ├── settings.yaml         # Main Config (includes structure_pattern, top_k, thresholds)
│   ├── secrets.yaml          # Private Keys (GitIgnored)
│   └── ioc_list.xlsx         # IOC World Bird List
├── data/
│   ├── db/
│   │   └── feathertrace.db   # SQLite Database
│   ├── raw/                  # Input folder
│   └── processed/            # Output folder
├── docs/
│   ├── NAS_SETUP.md          # Guide for WebDAV/SMB
│   └── CHANGELOG_v1.6.md     # Latest updates
├── src/
│   ├── core/                 # Detection, Quality, Processing
│   │   └── io/               # PathParser, PathGenerator, SmartScanner logic
│   ├── recognition/
│   │   ├── bioclip_base.py
│   │   ├── inference_local.py # Supports BioCLIP v1 & v2
│   │   ├── inference_dongniao.py
│   │   ├── inference_api.py   # HuggingFace
│   ├── metadata/
│   │   ├── ioc_manager.py
│   │   └── exif_writer.py    # Handles Metadata injection & renaming
│   ├── utils/                # config_loader.py
│   ├── web/
│   │   ├── app.py
│   │   └── templates/
│   └── pipeline_runner.py
├── requirements.txt
└── README.md
```

---

## 3. Module Requirements

### A. Pre-processing
*   **Smart Scanning**: Recursive directory walker with date-based pruning for efficiency.
*   **Path Parsing**: Supports hybrid logic—Strict standard format for parents (`yyyyMMdd-yyyyMMdd...`), Regex for leaf folders.
*   **Object Detection (YOLOv8)**: Detects birds.
*   **Quality Check**: Filters blurry images.

### B. Recognition Engine
*   **Local**: BioCLIP v1/v2 (FP16 optimized).
*   **Dongniao**: API based (China optimized).
*   **Candidates**: Returns Top-K results; stores candidates in DB for manual review.

### C. Configuration
*   **Secure Loading**: Merges `settings.yaml` and `secrets.yaml`.
*   **Region Auto-Switch**: Automatically selects taxonomy based on folder name (Foreign vs Domestic).
*   **NAS/Remote Support**: Supports WebDAV/SMB via OS-level mounting.

### D. Web Interface
*   **Gallery**: Toggle Raw/Processed view.
*   **Edit**: 
    *   Manual correction with "AI Alternatives" suggestion list.
    *   **Smart Renaming**: Automatically renames/moves files and updates EXIF when species is changed.
*   **Admin**: System reset, stats, and batch pipeline triggering with date filters.

---

## 4. Workflows

### Workflow 1: Data Ingest
1.  **Scan & Prune**: Iterate sources; skip folders outside user-defined date range.
2.  **Process**: Detect -> Crop -> Recognize (Top-K).
3.  **Archive**: Save to `data/processed`.
4.  **Metadata**: Write EXIF (Title, Description, Keywords). If low confidence, list alternatives in `UserComment`.
5.  **Index**: Insert into DB (including JSON candidates).

### Workflow 2: Web Interaction
1.  User browses gallery.
2.  User corrects ID.
    *   System suggests AI alternatives.
    *   Upon save: File is renamed/moved (if template uses species name), EXIF is updated, Database is updated.

---