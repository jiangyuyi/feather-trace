# 项目说明：FeatherTrace (羽迹)

**版本:** 1.6
**语言:** Python 3.10+
**描述:** 个人鸟类摄影自动化流水线与管理系统。

---

## 更新日志 (v1.6)
详细更新请查阅 `docs/CHANGELOG_v1.6_zh.md`。核心亮点：
1.  **智能扫描**: 支持基于日期的递归扫描与文件夹剪枝 (Pruning)。
2.  **备选结果**: 数据库存储 Top-K 识别结果，Web 端提供一键修正建议。
3.  **智能重命名**: 人工修正物种后，自动重命名并移动文件，同步更新 EXIF。
4.  **元数据**: 统一了 Title/Description 格式 (`中文名 (拉丁名)`)，修复了 Windows 编码问题。

---

## 1. 系统架构

系统包含三个核心组件：
1.  **Pipeline (ETL)**: 负责图像摄取、智能扫描、检测 (YOLO)、识别 (BioCLIP/Dongniao)、元数据写入 (ExifTool) 和归档。
2.  **Database (SQLite)**: 存储 IOC 分类树 (Taxonomy)、照片索引 (Photos) 及识别备选项 (Candidates)。
3.  **Web Interface (FastAPI)**: 提供浏览、搜索、人工校对（含 AI 建议）和系统管理功能。

---

## 2. 关键模块说明

### A. 预处理 (`src/core`)
*   **SmartScanner**: 支持 `yyyyMMdd` 范围过滤的递归扫描器。
*   **PathParser**: 混合解析逻辑——父级目录强制标准格式，末级目录支持自定义正则。
*   **VFS/NAS**: 通过 OS 挂载支持 WebDAV/SMB。

### B. 识别引擎 (`src/recognition`)
*   **BioCLIP (Local)**: FP16 优化，支持 Top-K 输出。
*   **Dongniao (API)**: 支持国内高精度识别。
*   **Candidates**: 将多项备选结果存入数据库 `candidates_json`。

### C. 数据管理 (`src/metadata`)
*   **IOCManager**: 数据库封装。
*   **ExifWriter**: 
    *   **安全写入**: 解决 Windows 路径编码与换行符问题。
    *   **字段统一**: 确保 Title/Description 格式一致，清空冗余 Subject。

### D. Web 服务 (`src/web`)
*   **前端**: Bootstrap 5 + Vanilla JS。支持原图对比。
*   **智能编辑**: 修改物种名时触发文件重命名 (Rename/Move) 和 EXIF 回写。
*   **管理**: 支持按日期范围启动批处理任务。

---

## 3. 维护指南

*   **重置**: 访问 `/admin` 页面可清空数据库重建索引。
*   **网络存储**: 请参考 `docs/NAS_SETUP_zh.md`。
*   **配置**: 修改 `config/settings.yaml` 调整识别阈值 (`alternatives_threshold`) 和命名模版。

---
