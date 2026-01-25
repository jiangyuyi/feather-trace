# FeatherTrace (羽迹) - 智能鸟类摄影管理系统

**Version:** 1.6  
**Status:** Stable (Smart Scanning, Auto-Renaming, NAS Support)

FeatherTrace 是一个为鸟类摄影师打造的自动化管理流水线。它利用计算机视觉（YOLOv8）和多模态大模型技术，自动完成照片的**检测、筛选、识别、元数据注入**以及**层级归档**，并提供一个支持异步批处理的 Web 界面。

---

## ✨ 核心功能

*   **📂 智能扫描与解析**:
    *   **Smart Scanning**: 支持按日期范围过滤文件夹，极大提升对大规模图库的处理效率。
    *   **混合解析**: 父目录采用标准格式 (`yyyyMMdd-yyyyMMdd...`)，子目录支持自定义正则，灵活适应各种整理习惯。
*   **🧠 多引擎识别与备选**:
    *   **Top-K Candidates**: 自动保存 AI 的前 5 个识别结果。
    *   **人工校对辅助**: 在 Web 界面提供“AI 备选”建议列表，一键修正。
    *   **引擎支持**: BioCLIP (Local v1/v2), 懂鸟 (Dongniao API), HuggingFace API。
*   **🛠️ 动态归档与重命名**:
    *   **Smart Renaming**: 当您修正物种名时，系统会自动重命名文件并将其移动到正确的分类文件夹中。
    *   **EXIF/IPTC**: 自动写入标准化的标题 (`中文名 (拉丁名)`) 和标签。低置信度结果会在备注中列出备选项。
*   **🌐 虚拟文件系统 (VFS)**: 
    *   完美支持挂载的 NAS (WebDAV/SMB) 路径。
*   **💻 高级 Web UI**:
    *   **异步批处理**: 支持指定日期范围运行流水线。
    *   **对比预览**: 按住图片实时对比“裁切图”与“原图”。

---

## 🛠️ 环境依赖

*   **Python 3.10+**
*   **ExifTool**: 必须安装并添加到系统 PATH（系统会自动进行环境检查）。
*   **GPU**: 推荐 NVIDIA RTX 系列（支持 FP16 加速）。

---

## 🚀 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 (`config/settings.yaml`)

```yaml
paths:
  allowed_roots: ["D:/Photos", "Z:/NAS_Photos"]
  sources:
    - path: "Z:/NAS_Photos/Raw"
      recursive: true
  output:
    structure_template: "{year}/{location}/{species_cn}/{filename}"
```

### 3. 启动 Web 界面

```bash
python src/web/app.py
```
访问 `http://localhost:8000`。

---

## 🤝 鸣谢与致谢 (Acknowledgements)

本项目的数据支持与核心算法离不开以下开源项目和数据服务的贡献：

### 📚 数据与标准 (Data & Standards)
*   **IOC World Bird List**: [https://www.worldbirdnames.org/new/](https://www.worldbirdnames.org/new/)  
    提供全球鸟类分类与命名标准。
*   **Catalogue of Life China (中国生物物种名录)**: [http://www.sp2000.org.cn/](http://www.sp2000.org.cn/)  
    提供中国鸟类中文名录与分类参考。

### 🧠 模型与算法 (Models & Algorithms)
*   **BioCLIP Model**: [https://imageomics.github.io/bioclip/](https://imageomics.github.io/bioclip/)  
    基于大规模生物图像训练的视觉模型，本项目核心识别引擎。
*   **懂鸟 API (Dongniao)**: [https://ai.open.hhodata.com/#introduce](https://ai.open.hhodata.com/#introduce)  
    提供高精度的中国本土鸟类识别服务。

### 🏗️ 核心开源依赖 (Core Open Source Projects)
本项目构建于以下优秀的开源项目之上：
*   **FastAPI**: 高性能 Web API 框架。
*   **Ultralytics YOLOv8**: 最先进的实时物体检测模型。
*   **PyTorch**: 深度学习基础框架。
*   **HuggingFace Transformers**: 模型加载与推理库。
*   **ExifTool (by Phil Harvey)**: 业界标准的元数据读写工具。
*   **Pillow (PIL)**: Python 图像处理库。
*   **Bootstrap**: 响应式前端界面框架。

---

**License**: MIT  
**Author**: 鱼酱 with Gemini Assistant
