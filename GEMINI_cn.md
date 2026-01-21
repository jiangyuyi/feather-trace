# 项目说明：FeatherTrace (羽迹)

**版本:** 1.3
**语言:** Python 3.10+
**描述:** 个人鸟类摄影自动化流水线与管理系统。

---

## 更新日志 (v1.3)
1.  **架构升级**: 引入 `config_loader` 实现配置与密钥分离 (`settings.yaml` + `secrets.yaml`)。
2.  **多模型支持**: 本地识别模块支持 **BioCLIP** 和 **BioCLIP-2** 切换。
3.  **API 增强**: 
    *   **懂鸟**: 修复了列表格式响应的解析 bug。
    *   **HuggingFace**: 更新了 API 端点 (`router.huggingface.co`) 并实现了完整的 Base64 调用逻辑。
4.  **鲁棒性**: 
    *   Web Admin 的“系统重置”功能增加了针对 Windows 文件锁的强力修复策略（重命名删除、GC 回收）。
    *   Web App 启动时自动修复数据库 Schema。

---

## 1. 系统架构

系统包含三个核心组件：
1.  **Pipeline (ETL)**: 负责图像摄取、检测 (YOLO)、识别 (BioCLIP/Dongniao/HF)、元数据写入 (ExifTool) 和归档。
2.  **Database (SQLite)**: 存储 IOC 分类树 (Taxonomy) 和照片索引 (Photos)。
3.  **Web Interface (FastAPI)**: 提供浏览、搜索、下载、人工校对和系统管理功能。

---

## 2. 关键模块说明

### A. 预处理 (`src/core`)
*   **Detector**: 使用 `yolov8n.pt` 检测鸟类目标。
*   **Processor**: 智能裁剪与 Resize。
*   **Quality**: 基于拉普拉斯方差过滤模糊废片。

### B. 识别引擎 (`src/recognition`)
*   **BioCLIP (Local)**:
    *   支持 `bioclip` 和 `bioclip-2`。
    *   FP16 + Batching + Caching 优化。
*   **Dongniao (API)**:
    *   支持国内高精度识别。
    *   健壮的 JSON 解析逻辑。
*   **HuggingFace (API)**:
    *   支持 Zero-Shot Image Classification。

### C. 数据管理 (`src/metadata`)
*   **IOCManager**: 封装数据库操作。支持从 Excel 导入分类数据。支持模糊搜索。
*   **Deduplication**: 基于文件 SHA256 哈希去重。

### D. Web 服务 (`src/web`)
*   **前端**: Bootstrap 5 + Vanilla JS。支持原图查看与模态框编辑。
*   **后端**: FastAPI。
*   **管理**: 提供数据库重置和统计面板。

---

## 3. 维护指南

*   **重置**: 访问 `/admin` 页面可清空数据库重建索引。
*   **密钥管理**: 修改 `config/secrets.yaml`。
*   **模型切换**: 修改 `config/settings.yaml` 中的 `local.model_type`。
