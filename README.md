# FeatherTrace (羽迹) - 智能鸟类摄影管理系统

**版本:** 1.0.7
**状态:** 稳定 (修复 Web 界面 Unicode 路径问题)

FeatherTrace 是一个专为鸟类摄影师打造的自动化管理流水线。它利用计算机视觉 (YOLOv8) 和多模态大模型 (BioCLIP) 技术，自动完成照片的**检测、筛选、物种识别、元数据注入**以及**层级归档**，并提供一个支持人工校对的本地 Web 界面。

本项目是我个人的第一个从零开始完全使用Vibe Coding的项目，使用了Gemini CLI 、Claude Code with MiniMax2.1/GLM4.7，作为一个观鸟爱好者，图片库的识别和整理一直是我的一大痛点，这个项目也算是圆了几年前的一个小梦想。

[查看更新日志](docs/CHANGELOG_v1.6_zh.md) | [架构文档](docs/ARCHITECTURE.md)

---

## ✨ 核心功能

* **📂 智能导入与解析**:
  * **智能扫描**: 递归扫描文件夹，支持按日期范围过滤，极大提升处理效率。
  * **混合解析**: 支持标准的父目录格式 (`yyyyMMdd-...`) 和基于正则的子目录解析。
* **🧠 多引擎识别**:
  * **引擎支持**: BioCLIP (本地 v1/v2), 懂鸟 (国内优化 API), HuggingFace API。
  * **Top-K 候选**: 自动保存 AI 的前 5 个预测结果供人工复核。
  * **智能建议**: Web 界面提供“AI 备选”下拉菜单，一键修正物种。
* **🛠️ 动态归档**:
  * **自动整理**: 当您修正物种名时，系统会自动重命名文件并将其移动到正确的分类文件夹中。
  * **元数据**: 自动写入标准化的 EXIF/IPTC 数据（标题、关键词）。
* **🌐 网络存储支持**:
  * 通过操作系统挂载，完美支持 NAS (WebDAV/SMB) 路径。
* **💻 高级 Web 界面**:
  * **批处理**: 异步触发指定日期范围的处理任务。
  * **对比预览**: 实时切换"裁切细节图"与"原始环境图"。
  * **分类树筛选**: 交互式物种分类导航，动态翻页保持一致体验。
  * **等宽网格**: CSS Grid 布局确保照片始终等宽显示，无论每行数量多少。

---

## 📸 Web 界面预览

![WebUI Preview](docs/webui_screenshot_placeholder.png)

*支持物种分类筛选、动态翻页和原图对比功能。*

---

## 🛠️ 环境要求

* **操作系统**: Windows 10/11, macOS, 或 Linux。
* **Python**: 3.10 或更高版本。
* **GPU (可选)**: 推荐使用 NVIDIA RTX 系列显卡以加速本地 BioCLIP 推理（需要 CUDA 12.1+）。

---

## 🚀 部署指南

### ⚡ 一键部署脚本 (推荐)

我们提供了自动化部署脚本，支持 Windows/macOS/Linux，自动完成环境检测、依赖安装、配置向导等步骤。

#### Windows 用户

**方法 1: 右键运行 (推荐)**
1. 进入 `scripts` 文件夹
2. 右键点击 `deploy.ps1`
3. 选择 "以 PowerShell 运行"

**方法 2: PowerShell 终端运行**
```powershell
# 进入项目目录
cd feather_trace

# 设置执行策略（首次运行需要）
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser -Force

# 运行部署脚本
.\scripts\deploy.ps1
```

> **说明**: Windows 默认禁止运行 PowerShell 脚本，需要设置执行策略。右键运行可绕过此限制。

#### Linux / macOS / WSL 用户

```bash
# 进入项目目录
cd feather_trace

# 运行部署脚本 (完整部署)
bash scripts/deploy.sh deploy

# 或仅安装依赖
bash scripts/deploy.sh install

# 或仅配置
bash scripts/deploy.sh config

# 或启动 Web 服务
bash scripts/deploy.sh web
```

#### 可用命令

| 命令 | 说明 |
|------|------|
| `deploy` | 完整部署流程 (推荐) |
| `install` | 仅安装依赖 |
| `config` | 运行配置向导 |
| `update` | 更新项目 |
| `cuda` | 安装 CUDA (GPU 支持) |
| `web` | 启动 Web 服务 |
| `help` | 显示帮助 |

#### 部署流程

脚本会自动执行以下步骤：

| 步骤 | 操作 | 说明 |
|------|------|------|
| 1 | 环境检测 | 检测 Python、Git、ExifTool、GPU |
| 2 | 自动安装 | 缺失的软件通过包管理器自动安装 |
| 3 | 切换镜像 | pip 和 HuggingFace 切换到国内源 |
| 4 | 克隆项目 | 从 Gitee 镜像克隆 (国内用户友好) |
| 5 | 安装依赖 | 创建虚拟环境并安装 Python 包 |
| 6 | 配置向导 | 交互式设置照片源目录、输出目录等 |
| 7 | 生成配置 | 自动生成 `settings.yaml` 和 `secrets.yaml` |

#### 交互式界面预览

```
┌────────────────────────────────────────┐
│     🪶 羽迹 FeatherTrace 一键部署       │
├────────────────────────────────────────┤
│  [1] 🚀 开始部署                        │
│  [2] ⚙️  配置选项                       │
│  [3] 📦 更新项目                        │
│  [4] ⬇️  下载模型                       │
│  [5] ▶️  启动服务                       │
│  [6] 📖 查看帮助                       │
│  [7] ❌  退出                           │
└────────────────────────────────────────┘
```

#### GitHub 国内访问

脚本默认从 **Gitee 镜像** 克隆（https://gitee.com/jiangyuyi/feather-trace），确保国内用户可以快速下载。

---

### 1. 安装依赖

#### 步骤 A: 安装 ExifTool (必须)

ExifTool 用于写入照片元数据，必须单独安装。

**Windows:**

```bash
# 方法1: 使用 Chocolatey (推荐)
chocolatey install exiftool

# 方法2: 手动安装
# 1. 下载: https://exiftool.org/install.html#Win32
# 2. 解压后将 exiftool(-a).exe 重命名为 exiftool.exe
# 3. 放入系统 PATH (如 C:\Windows\) 或自定义目录
```

**macOS:**

```bash
# 使用 Homebrew
brew install exiftool
```

**Linux:**

```bash
# Debian/Ubuntu
sudo apt install libimage-exiftool-perl

# 或从源码编译
```

> **重要**: 确保在终端运行 `exiftool -ver` 能正常显示版本号。

#### 步骤 B: 克隆代码并安装 Python 依赖

```bash
# 1. 克隆代码
git clone https://github.com/your-repo/feather_trace.git
cd feather_trace

# 2. 创建虚拟环境 (推荐)
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. 安装 Python 依赖
pip install -r requirements.txt
```

#### 步骤 C: 预下载 BioCLIP 模型 (可选，推荐)

首次使用本地识别时，系统会自动下载 BioCLIP 模型（约 300MB）。如需预下载：

```bash
# 使用模型下载脚本
python scripts/download_model.py

# 或手动下载
# BioCLIP v2 (推荐): hf.co/imageomics/bioclip-v2
# BioCLIP v1: hf.co/imageomics/bioclip
```

> 模型默认缓存至 `~/.cache/huggingface/hub/`。

---

### 2. 配置

FeatherTrace 使用 YAML 进行配置。

1. **主设置**: 编辑 `config/settings.yaml` 来定义您的照片源路径和输出结构。
2. **密钥**: 如果使用云端 API (懂鸟或 HuggingFace)，请复制示例密钥文件：

   ```bash
   # Windows 复制命令
   copy config\secrets.example.yaml config\secrets.yaml
   ```

   然后编辑 `config/secrets.yaml` 填入您的 API Key。

👉 **[阅读完整配置指南](docs/CONFIGURATION.md)** 了解所有可用选项。

---

### 3. NAS / 远程存储

要处理存储在 NAS (群晖, 威联通等) 上的照片，您必须先将网络共享挂载为本地驱动器。

👉 **[阅读 NAS 设置指南](docs/NAS_SETUP_zh.md)**。

---

### 4. 启动系统

#### A. 启动 Web 界面 (推荐)

这将启动本地 Web 服务器，用于浏览、编辑和触发批处理任务。

```bash
python src/web/app.py
```

* 访问地址: `http://localhost:8000`
* **提示**: 进入 "Admin (管理)" 页面来触发您的第一次扫描。

**首次启动检查清单:**

- [ ] `exiftool` 命令可正常执行
- [ ] `config/settings.yaml` 中的路径已正确配置
- [ ] `allowed_roots` 包含所有需要访问的盘符
- [ ] 照片源目录中有符合命名格式的文件夹 (`YYYYMMDD_地点`)

#### B. 命令行接口 (高级)

您也可以不通过 Web 界面直接运行流水线。

```bash
# 运行流水线，处理指定日期范围的照片
python src/pipeline_runner.py --start 20240101 --end 20240131
```

---

### 5. 常见问题

**Q: 启动报错 "exiftool not found"**
A: 确保 ExifTool 已安装并添加到系统 PATH。重启终端后再试。

**Q: 本地 BioCLIP 识别首次运行很慢**
A: 首次运行时需要下载模型（约 300MB），后续会缓存使用。

**Q: CUDA out of memory**
A: 在 `settings.yaml` 中将 `device` 改为 `cpu`，或减小 `local.inference_batch_size`。

**Q: Windows 中文路径乱码**
A: 确保系统区域设置支持 UTF-8，或使用英文路径。

---

## 🤝 致谢

* **IOC World Bird List**: [https://www.worldbirdnames.org/](https://www.worldbirdnames.org/) (分类学标准)
* **BioCLIP**: [https://imageomics.github.io/bioclip/](https://imageomics.github.io/bioclip/) (视觉模型)
* **懂鸟**: [https://ai.open.hhodata.com/](https://ai.open.hhodata.com/) (中国鸟类识别 API)

---

**许可证**: MIT
**作者**: 鱼酱 (with Gemini Assistant)
