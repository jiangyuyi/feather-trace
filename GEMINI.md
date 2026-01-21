# Project Specification: FeatherTrace
**Version:** 1.3
**Project Name:** feather_trace
**Language:** Python 3.10+
**Description:** A personal bird photography automation pipeline and management system. It automates focus detection, cropping, AI species recognition (BioCLIP/Dongniao/HF), metadata injection, and provides a local web interface for searching, retrieval, and manual annotation.

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
│   ├── settings.yaml         # Main Config
│   ├── secrets.yaml          # Private Keys (GitIgnored)
│   └── ioc_list.xlsx         # IOC World Bird List
├── data/
│   ├── db/
│   │   └── feathertrace.db   # SQLite Database
│   ├── raw/                  # Input folder
│   └── processed/            # Output folder
├── src/
│   ├── core/                 # Detection, Quality, Processing
│   ├── recognition/
│   │   ├── bioclip_base.py
│   │   ├── inference_local.py # Supports BioCLIP v1 & v2
│   │   ├── inference_dongniao.py
│   │   ├── inference_api.py   # HuggingFace
│   ├── metadata/
│   │   ├── ioc_manager.py
│   │   └── exif_writer.py
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
*   **Object Detection (YOLOv8)**: Detects birds.
*   **Quality Check**: Filters blurry images.
*   **Deduplication**: Hash-based check.

### B. Recognition Engine
*   **Local**: BioCLIP v1/v2 (FP16 optimized).
*   **Dongniao**: API based (China optimized).
*   **HuggingFace**: API based (Zero-shot).

### C. Configuration
*   **Secure Loading**: Merges `settings.yaml` and `secrets.yaml`.
*   **Region Auto-Switch**: Automatically selects taxonomy based on folder name (Foreign vs Domestic).

### D. Web Interface
*   **Gallery**: Toggle Raw/Processed view.
*   **Edit**: Fuzzy search for manual correction.
*   **Admin**: System reset and stats.

---

## 4. Workflows

### Workflow 1: Data Ingest
1.  **Scan & Dedup**: Iterate `data/raw`, skip duplicates.
2.  **Process**: Detect -> Crop -> Recognize (Local/API).
3.  **Archive**: Save to `data/processed`, write EXIF.
4.  **Index**: Insert into DB.

### Workflow 2: Web Interaction
1.  User browses gallery.
2.  User verifies ID using "Original View".
3.  User corrects ID using search dropdown.
4.  Backend updates DB.

---
