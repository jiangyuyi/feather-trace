# FeatherTrace 配置指南

本文档详细介绍了 FeatherTrace 的各项配置选项。系统主要使用 `config/` 目录下的两个 YAML 文件进行配置：

1.  `settings.yaml`: 主配置文件，包含路径、处理逻辑和应用行为设置。
2.  `secrets.yaml`: 安全配置文件，用于存储 API 密钥（此文件不会被 Git 追踪）。

---

## 1. 主配置 (`settings.yaml`)

### A. 路径配置 (`paths`)

控制 FeatherTrace 从哪里读取图片以及将结果保存到何处。

| 参数 | 描述 | 默认值 / 示例 |
| :--- | :--- | :--- |
| `allowed_roots` | **安全设置**。Web 界面和文件系统提供程序允许访问的根目录列表。**如果您添加了新的盘符或 NAS 挂载点，必须在此处添加。** | `["D:/Photos", "Z:/NAS"]` |
| `sources` | 定义需要扫描图片的源目录列表。 | 见下文 |

#### 源目录定义 (`sources`)
`sources` 列表中的每一项可以包含以下属性：
*   `path`: 文件夹的绝对路径。
*   `recursive`: `true` 表示递归扫描子文件夹。
*   `enabled`: `true` 表示启用此源。
*   `structure_pattern` (可选): 用于从文件夹结构中提取元数据（日期、地点）的正则表达式。
    *   *默认*: 使用内部逻辑猜测 `YYYYMMDD_地点` 格式。
    *   *自定义*: 使用命名组 `(?P<date>...)` 和 `(?P<location>...)`。

```yaml
sources:
  - path: "Z:/Photos/2024"
    recursive: true
    enabled: true
    # 示例：匹配 "2024-01-27 [奥森公园]" 这样的文件夹
    structure_pattern: "(?P<date>\\d{4}-\\d{2}-\\d{2}) \\\\[(?P<location>.*)\\]"
```

#### 输出配置 (`paths.output`)

| 参数 | 描述 |
| :--- | :--- |
| `root_dir` | 处理后图片的保存根目录。 |
| `write_back_to_source` | `true`: 将 EXIF 数据直接写回**源文件**。`false` (默认): 仅修改复制到 `root_dir` 的文件。 |
| `structure_template` | 定义处理后图片的文件夹结构和文件名格式。 |

**模板变量:**
*   `{date}`, `{year}`, `{month}`, `{day}`: 从文件夹名或 EXIF 获取的日期。
*   `{location}`: 从文件夹名获取的地点。
*   `{species_cn}`: 鸟种中文名 (例如 "麻雀")。
*   `{species_sci}`: 拉丁学名 (例如 "Passer montanus")。
*   `{confidence}`: 识别置信度 (0-100)。
*   `{filename}`: 原始文件名。
*   `{source_structure}`: 保留源目录的相对层级结构。

---

### B. 处理设置 (`processing`)

控制计算机视觉流水线的参数。

| 参数 | 描述 | 默认值 |
| :--- | :--- | :--- |
| `device` | 硬件加速。选项: `cuda` (NVIDIA GPU), `cpu`, `auto`。 | `cuda` |
| `yolo_model` | YOLOv8 检测模型文件的路径。 | `yolov8n.pt` |
| `confidence_threshold` | **检测**鸟类目标的最低置信度 (0-1)。 | `0.5` |
| `blur_threshold` | 拉普拉斯方差阈值。低于此分数的图片会被标记为模糊。 | `40.0` |
| `target_size` | 识别前裁切图的缩放尺寸 (像素)。 | `640` |
| `crop_padding` | 在检测到的鸟类方框周围额外保留的像素。 | `200` |

---

### C. 识别设置 (`recognition`)

配置用于识别物种的 AI 引擎。

| 参数 | 描述 | 选项 |
| :--- | :--- | :--- |
| `mode` | 使用的识别引擎。 | `local` (BioCLIP 本地), `api` (HuggingFace API), `dongniao` (懂鸟 API) |
| `region_filter` | 候选词过滤器。`auto` 会根据文件夹名关键词自动切换。 | `null` (全球), `china` (仅中国分布), `auto` |
| `top_k` | 保存的备选物种数量。 | `5` |
| `alternatives_threshold` | 如果首选结果置信度高于此值 (0-100)，Web 界面将不显示备选建议（认为非常可信）。 | `70` |
| `low_confidence_threshold` | 低于此分数的匹配将被标记为“不确定”。 | `60` |

#### 引擎特定配置

**本地模型 (BioCLIP):**
```yaml
local:
  model_type: "bioclip-2" # 推荐使用 "bioclip-2" 以获得更高精度
  batch_size: 512         # 文本编码批次大小 (不用改)
  inference_batch_size: 16 # 图片推理批次大小 (如果显存不足请调小此值)
```

---

### D. 参考数据 (`paths` 部分续)

指向必需的数据库和字典文件的路径。通常不需要更改，除非您移动了 `data` 文件夹。

*   `db_path`: SQLite 数据库文件。
*   `ioc_list_path`: 包含 IOC 世界鸟类名录的 Excel 文件。
*   `china_list`: 用于过滤中国鸟种的文本文件。

---

## 2. 密钥配置 (`secrets.yaml`)

此文件保存您的 API 密钥。默认情况下不存在此文件，您需要复制 `config/secrets.example.yaml` 来创建它。

### 结构

```yaml
recognition:
  # HuggingFace (仅当 mode 为 'api' 时需要)
  api:
    key: "hf_..."

  # 懂鸟 (仅当 mode 为 'dongniao' 时需要)
  dongniao:
    key: "your_key..."
```

---

## 3. 环境变量

您也可以使用环境变量覆盖部分设置（适用于 Docker/云环境）：

*   `FT_PORT`: Web 服务器端口 (默认: 8000)
*   `FT_HOST`: Web 服务器主机 (默认: 0.0.0.0)

```