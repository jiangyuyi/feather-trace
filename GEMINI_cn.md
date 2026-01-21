# 项目说明：FeatherTrace (羽迹)

**版本:** 1.1
**语言:** Python 3.10+
**描述:** 个人鸟类摄影自动化流水线与管理系统。

---

## 更新日志 (v1.1)
1.  **稳定性修复**: 针对 RTX 4060 笔记本显卡，实施了 FP16 混合精度加载与 Batching 策略，彻底解决了模型加载死机问题。
2.  **性能飞跃**: 引入 Text Feature Caching，推理速度提升 1000 倍。
3.  **智能去重**: 在 Pipeline 中增加了基于文件内容哈希的去重机制，防止重复处理。
4.  **Web 交互升级**:
    *   新增“原图/裁切图”一键切换查看。
    *   新增“人工修正”功能，支持 IOC 名录模糊搜索（中文/拉丁名）。
    *   新增“系统管理”后台，支持一键重置数据。
5.  **数据层升级**: 数据库新增 `original_path` 与 `file_hash` 字段，支持原图映射。

---

## 1. 系统架构

系统包含三个核心组件：
1.  **Pipeline (ETL)**: 负责图像摄取、检测 (YOLO)、识别 (BioCLIP)、元数据写入 (ExifTool) 和归档。
2.  **Database (SQLite)**: 存储 IOC 分类树 (Taxonomy) 和照片索引 (Photos)。
3.  **Web Interface (FastAPI)**: 提供浏览、搜索、下载和人工校对功能。

---

## 2. 关键模块说明

### A. 预处理 (`src/core`)
*   **Detector**: 使用 `yolov8n.pt` 检测鸟类目标。
*   **Processor**: 智能裁剪与 Resize。
*   **Quality**: 基于拉普拉斯方差过滤模糊废片。

### B. 识别引擎 (`src/recognition`)
*   **BioCLIP**: 使用 `imageomics/bioclip` 模型。
*   **优化策略**: 
    *   `FP16` + `Autocast`: 降低显存占用。
    *   `Batching`: 文本特征计算分批进行 (Batch Size 512)。
    *   `Caching`: 缓存向量，避免重复计算。

### C. 数据管理 (`src/metadata`)
*   **IOCManager**: 封装数据库操作。支持从 Excel 导入分类数据。支持模糊搜索。
*   **Schema**: 
    *   `taxonomy`: 存储 10,000+ 种鸟类信息。
    *   `photos`: 存储图片路径、哈希、原图映射、识别结果。

### D. Web 服务 (`src/web`)
*   **前端**: Bootstrap 5 + Vanilla JS。支持原图查看与模态框编辑。
*   **后端**: FastAPI。提供 RESTful API (`/api/search_species`, `/api/update_label`, `/api/admin/reset`)。
*   **静态资源**: 挂载 `data/processed` 和 `data/raw`。

---

## 3. 工作流

### 初始化
1.  运行 `scripts/import_ioc_data.py` 填充分类数据库。

### 日常处理
1.  将照片导入 `data/raw/YYYYMMDD_Location/`。
2.  运行 `python src/pipeline_runner.py`。
    *   系统自动计算哈希去重。
    *   生成裁切图并归档至 `data/processed`。
    *   写入数据库。

### 浏览与修正
1.  运行 `python src/web/app.py`。
2.  在 Web 界面查看照片。
3.  点击“切换”按钮对比原图。
4.  点击“编辑”按钮，搜索正确鸟种并保存。

---

## 4. 维护
*   **重置**: 访问 `/admin` 页面可清空数据库重建索引（推荐在升级版本后使用）。
