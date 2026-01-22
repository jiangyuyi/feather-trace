# Project Specification: FeatherTrace
**Version:** 1.5
**Description:** A professional personal bird photography automation pipeline. Features AI-powered detection, multi-engine recognition, and a VFS-based management system.

---

## 1. System Components

1.  **VFS Layer**: Abstracted IO layer supporting Local/Remote filesystems with `allowed_roots` security.
2.  **ETL Pipeline**:
    *   **Input**: Multiple sources, regex-based metadata extraction.
    *   **Processing**: YOLOv8 Detection -> Blur Check -> Multi-Model Recognition.
    *   **Output**: Template-based directory hierarchy, IPTC/XMP metadata injection (including source writeback).
3.  **Web Interface**: FastAPI-based gallery with background task management and real-time logs.

---

## 2. Key Features (v1.5)

*   **Dynamic Pathing**: Customize how photos are read and where they are archived using `{variables}`.
*   **Source Writeback**: Direct synchronization of AI identification results to raw files.
*   **Web Batching**: Control the full pipeline from a web browser with live feedback.
*   **Advanced Search**: Specialized ranking for Chinese bird taxonomy.
*   **Robustness**: Argfile-based EXIF writing to eliminate encoding issues on Windows.

---

## 3. Configuration Highlights

```yaml
sources:
  - path: "data/raw"
    recursive: true
    structure_pattern: "(?P<date>\d{8})_(?P<location>.*)"

output:
  root_dir: "data/processed"
  structure_template: "{year}/{location}/{species_cn}/{filename}"
  write_back_to_source: true
```