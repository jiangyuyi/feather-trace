# FeatherTrace (羽迹) - 智能鸟类摄影管理系统

**Version:** 1.5  
**Status:** Stable (Advanced VFS, Multi-Source, Async Pipeline)

FeatherTrace 是一个为鸟类摄影师打造的自动化管理流水线。它利用计算机视觉（YOLOv8）和多模态大模型技术，自动完成照片的**检测、筛选、识别、元数据注入**以及**层级归档**，并提供一个支持异步批处理的 Web 界面。

---

## ✨ 核心功能

*   **🌐 虚拟文件系统 (VFS)**: 
    *   支持任意本地路径，并为 WebDAV/SMB 等远程协议预留了架构。
    *   **安全限制**: 引入 `allowed_roots` 白名单机制，确保系统仅访问授权目录。
*   **📂 多源输入与智能解析**:
    *   支持配置多个源文件夹。
    *   **自定义解析**: 支持使用正则表达式从复杂的文件夹结构中提取“日期”和“地点”元数据。
*   **🛠️ 动态输出模版**:
    *   支持基于元数据的自定义归档结构（例如：`{year}/{location}/{species_cn}/{filename}`）。
    *   **镜像模式**: 可选择完全保留原始目录结构进行输出。
*   **🧠 多引擎识别**:
    *   **BioCLIP (Local)**: 针对显卡优化 (FP16/Caching)，支持 v1/v2 模型切换。
    *   **懂鸟 (Dongniao API)**: 专为中国鸟类优化。
*   **✍️ 元数据回写**: 
    *   自动为处理后的照片写入 IPTC/XMP 标签。
    *   **源文件回写**: 支持将识别出的鸟种信息写回原始 Raw 文件，方便其他搜索工具索引。
*   **💻 高级 Web UI**:
    *   **异步批处理**: 在 Web 界面一键启动流水线，通过 WebSocket 实时查看黑色控制台日志。
    *   **智能搜索**: 针对中国鸟类优化搜索算法，优先展示中文名匹配结果。
    *   **对比预览**: 按住图片可实时对比“裁切图”与“原图”。

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

### 2. 配置源与输出 (`config/settings.yaml`)

```yaml
paths:
  allowed_roots: ["D:/Photos", "E:/Birds"] # 允许访问的根目录
  sources:
    - path: "D:/Photos/2023_Raw"
      recursive: true
      structure_pattern: "(?P<date>\\d{8})_(?P<location>.*)" # 可选正则解析
  output:
    root_dir: "D:/Photos/Processed"
    structure_template: "{year}/{location}/{species_cn}/{filename}"
    write_back_to_source: true # 是否回写原图
```

### 3. 启动 Web 界面

```bash
python src/web/app.py
```
访问 `http://localhost:8000`，进入 **Admin & Tasks** 页面点击 **Start Pipeline** 即可开始自动化处理。

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