# Changelog v1.6

## 🚀 New Features

### 1. Smart Recursive Scanning & Pruning
*   **Feature**: Implemented a "Smart Scanner" that recursively walks directories.
*   **Pruning**: Added support for date-based pruning. If `start_date` or `end_date` is provided, folders named with dates (e.g., `20231020_Park`) outside the range are skipped entirely, significantly improving performance on large archives.
*   **Logic**:
    *   **Parent Folders**: Enforced strict `yyyyMMdd-yyyyMMdd...` or `yyyyMMdd...` parsing logic.
    *   **Prefixing**: Locations from parent folders are now automatically prefixed to child folders (e.g., Parent `2023_Japan` + Child `Tokyo` -> Location `Japan_Tokyo`).
    *   **Hybrid Parsing**: Custom regex (`structure_pattern`) now **only applies to the last folder**, allowing flexible naming for leaf directories while maintaining strict structure for parents.

### 2. Alternatives & Manual Correction
*   **AI Candidates**: The system now stores the top 5 (configurable via `top_k`) recognition results in the database (`candidates_json` column).
*   **Thresholding**: Introduced `recognition.alternatives_threshold` (default 70).
    *   If the top match confidence is > 70%, only the top match is written to metadata.
    *   If < 70%, a list of "Alternatives" is written to the EXIF `UserComment`.
*   **Web UI**:
    *   The "Correct ID" modal now displays a clickable list of **"AI Alternatives"**.
    *   Clicking an alternative instantly updates the label.
*   **Smart Renaming**:
    *   When a label is manually corrected, the file is **automatically renamed and moved** if the filename template uses `{species_cn}`, `{species_sci}`, or `{confidence}`.
    *   The confidence score in the filename is updated to `100pct` to reflect manual verification.

### 3. NAS / WebDAV Support
*   **Support**: Confirmed support for WebDAV/SMB via OS-level mounting.
*   **Documentation**: Added `docs/NAS_SETUP.md` with detailed mounting instructions.

## 🛠️ Improvements & Fixes

### Metadata (EXIF/IPTC/XMP)
*   **Unification**: Standardized "Title" and "Description" fields to always use the format `ChineseName (ScientificName)`.
*   **Subject Field**: Explicitly cleared the `XPSubject` field to avoid redundancy in Windows Explorer.
*   **Encoding Fix**: Resolved Windows CLI encoding issues by passing filenames inside the `exiftool` argument file.
*   **Safety**: Used `-E` flag and HTML entity escaping (`&#xa;`) to safely handle newlines in comments.

### Configuration
*   **Structure Pattern**: Refined `structure_pattern` logic to prevent greedy regex matching from consuming parent directory paths.
*   **Top-K**: Enabled `top_k` configuration for all recognition modes (Local & API).

### Database
*   **Scan History**: Added `scan_history` table to track pipeline execution stats (duration, count, range).
*   **Migration**: Added schema migration to automatically add `candidates_json` to existing databases.

## 👨‍💻 Developer Notes
*   **Refactoring**: Extracted folder date parsing logic into `PathParser.parse_folder_name` static method.
*   **API**: Updated `/api/update_label` to handle file system operations (move/rename) and EXIF write-back.
