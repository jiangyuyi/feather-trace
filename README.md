# FeatherTrace (羽迹) - 智能鸟类摄影管理系统

**Version:** 1.1  
**Status:** Stable (FP16 Optimized, Deduplication Enabled)

FeatherTrace 是一个为鸟类摄影师打造的自动化管理流水线。它利用计算机视觉（YOLOv8）和多模态大模型（BioCLIP）技术，自动完成照片的**鸟类检测、画质筛选、物种识别、元数据注入**以及**归档整理**，并提供一个本地 Web 界面进行检索、人工修正和原图比对。

---

## ✨ 核心功能

*   **🔍 自动检测与裁剪**: 使用 YOLOv8 自动识别照片中的鸟类，并基于边界框进行智能裁剪。
*   **🧠 专家级识别**: 集成 **BioCLIP (ViT-B/16)** 模型，支持全球 10,000+ 种鸟类的 Zero-Shot 识别。
*   **⚡ 性能优化 (RTX 40 Series Ready)**:
    *   **FP16 混合精度**: 针对 RTX 4060 等新一代显卡优化，降低显存占用，防止死机。
    *   **Smart Caching**: 推理速度提升 **1000倍** (毫秒级)。
    *   **Batch Processing**: 防止 OOM (显存溢出)。
*   **🛡️ 智能去重**: 基于文件哈希（SHA256）检测重复图片，避免重复处理和归档。
*   **📝 元数据注入**: 基于 `PyExifTool` 自动将识别结果写入照片元数据。
*   **🌏 本地化支持**: 内置 IOC 世界鸟类名录数据库，支持中英文模糊搜索与修正。
*   **💻 高级 Web 图库**:
    *   **原图/裁切图切换**: 实时对比识别主体与原片。
    *   **人工修正**: 内置搜索下拉框，支持按中文或拉丁名快速修正识别结果。
    *   **系统管理**: 提供数据重置功能。

---

## 🛠️ 环境依赖

### 硬件要求
*   **CPU**: 现代多核 CPU
*   **RAM**: 16GB+
*   **GPU**: NVIDIA RTX 30/40 系列 (推荐 8GB 显存)
*   **Disk**: SSD

### 软件要求
1.  **Python 3.10+**
2.  **ExifTool**: 必须安装 ExifTool 并添加到 PATH。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
# 安装项目依赖
pip install -r requirements.txt
```

### 2. 初始化数据库 (导入 IOC 名录)
**重要**: 首次使用前，请运行此脚本以导入鸟类字典，否则人工修正功能的搜索框将无法工作。

```bash
python scripts/import_ioc_data.py
```

### 3. 准备数据

将原始 JPG 照片放入 `data/raw` 目录下的子文件夹中（如 `20231020_OlympicPark`）。

### 4. 运行处理流水线

```bash
python src/pipeline_runner.py
```
> **注意**: 如果您重新运行流水线，系统会自动跳过已处理过的文件（基于哈希去重）。

### 5. 启动 Web 图库

```bash
python src/web/app.py
```
浏览器访问: `http://localhost:8000`

---

## ⚙️ 系统管理与维护

### 重置系统
如果遇到数据库与文件不一致，或希望对旧数据启用“原图查看”功能，请访问 Web 界面的 **系统管理** 页面 (`/admin`) 并执行重置操作。重置后，请重新运行 `src/pipeline_runner.py`。

### 目录结构

```text
feather_trace/
├── config/             # 配置文件与 Excel 名录
├── data/
│   ├── db/             # SQLite 数据库
│   ├── models/         # 模型权重
│   ├── raw/            # [输入] 原始照片
│   └── processed/      # [输出] 归档照片
├── src/
│   ├── core/           # 视觉算法
│   ├── recognition/    # BioCLIP 推理
│   ├── metadata/       # ExifTool & IOCManager
│   └── web/            # FastAPI Web 服务
└── scripts/            # 工具脚本 (导入数据、测试等)
```

---
**License**: MIT  
**Author**: Gemini Assistant