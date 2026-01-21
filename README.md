# FeatherTrace (羽迹) - 智能鸟类摄影管理系统

**Version:** 1.3  
**Status:** Stable (Multi-Model, Secure Config, Robust)

FeatherTrace 是一个为鸟类摄影师打造的自动化管理流水线。它利用计算机视觉（YOLOv8）和多模态大模型（BioCLIP/懂鸟API）技术，自动完成照片的**鸟类检测、画质筛选、物种识别、元数据注入**以及**归档整理**，并提供一个本地 Web 界面进行检索、人工修正和原图比对。

---

## ✨ 核心功能

*   **🔍 自动检测与裁剪**: 使用 YOLOv8 自动识别照片中的鸟类，并基于边界框进行智能裁剪。
*   **🧠 多引擎识别**:
    *   **BioCLIP (Local)**: 免费、离线。支持 **v1** 和 **v2** 模型切换。针对显卡优化 (FP16/Caching)。
    *   **懂鸟 (Dongniao API)**: 专为中国鸟类优化，识别准确率极高。
    *   **HuggingFace API**: 标准云端推理支持。
*   **⚡ 性能与稳定性**:
    *   **智能去重**: 基于文件哈希防止重复处理。
    *   **Auto Region**: 根据文件夹名称自动切换“中国/全球”名录。
    *   **Anti-Crash**: 针对 Windows 文件锁和显存峰值做了深度优化。
*   **🛡️ 安全配置**: 敏感 API Key 存储在独立的 `secrets.yaml` 中，防止泄露。
*   **💻 高级 Web 图库**:
    *   **原图/裁切图切换**: 实时对比。
    *   **人工修正**: 支持中英文模糊搜索。
    *   **系统管理**: 一键重置系统数据。

---

## 🛠️ 环境依赖

*   **Python 3.10+**
*   **ExifTool**: 必须安装并添加到系统 PATH。
*   **GPU**: 推荐 NVIDIA RTX 30/40 系列 (8GB+ 显存最佳，已优化支持 6GB)。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置系统

**基础配置 (`config/settings.yaml`)**:
修改 `processing.device` 或 `recognition.mode`。

**安全配置 (`config/secrets.yaml`)**:
新建此文件（或使用模板），填入你的 API Key：

```yaml
recognition:
  dongniao:
    key: "YOUR_DONGNIAO_KEY"
  api:
    key: "YOUR_HF_TOKEN"
```

### 3. 初始化

首次运行流水线会自动导入 IOC 鸟类名录。如果需要手动导入：
```bash
python scripts/import_ioc_data.py
```

### 4. 运行流水线

将照片放入 `data/raw` 下的子文件夹（如 `20231020_OlympicPark`）。

```bash
python src/pipeline_runner.py
```

### 5. 启动 Web 图库

```bash
python src/web/app.py
```
浏览器访问: `http://localhost:8000`

---

## ⚙️ 常见操作

*   **切换本地模型**: 在 `settings.yaml` 中设置 `local.model_type` 为 `bioclip` 或 `bioclip-2`。
*   **重置系统**: 访问 Web 界面的 `/admin` 页面，点击“彻底重置”。
*   **查看架构**: 详见 `docs/ARCHITECTURE.md`。

---
**License**: MIT  
**Author**: 鱼酱 with Gemini Assistant