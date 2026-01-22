# FeatherTrace 系统架构文档 (v1.5)

## 1. 核心设计理念

FeatherTrace 1.5 引入了**虚拟文件系统 (VFS)** 层，旨在打破对本地物理路径的依赖，实现“多源接入、按需处理、原位回写”。

### 关键组件：
*   **StorageProvider (IO 抽象层)**: 定义了统一的文件操作接口。目前实现了 `LocalProvider`，未来可无缝扩展 `WebDAVProvider` 或 `SMBProvider`。
*   **PathParser & PathGenerator**: 实现了路径与元数据的双向映射。`Parser` 利用正则从路径提取信息，`Generator` 利用模版生成归档路径。
*   **TaskManager**: 在 Web 服务后端管理异步流水线线程，通过 WebSocket 提供实时反馈。

---

## 2. 目录结构

```text
feather_trace/
├── src/
│   ├── core/
│   │   ├── io/               # VFS 核心实现
│   │   │   ├── provider.py   # 抽象基类
│   │   │   ├── local.py      # 本地文件实现 (含安全检查)
│   │   │   ├── fs_manager.py # 调度器
│   │   │   ├── path_parser.py# 输入路径解析
│   │   │   ├── path_generator.py # 输出路径模版
│   │   │   └── temp_manager.py # 远程文件本地化缓存
│   │   ├── detector.py       # YOLOv8 鸟类检测
│   │   └── processor.py      # 图像裁切与缩放
│   ├── recognition/          # AI 识别引擎策略
│   ├── metadata/             # 数据库与 EXIF 处理
│   ├── web/                  # FastAPI 异步 Web 服务
│   └── pipeline_runner.py    # 批处理流水线核心
```

---

## 3. 数据流逻辑

### 3.1 批处理流程 (Pipeline)
1.  **扫描 (VFS)**: 遍历 `sources` 配置中的所有路径。
2.  **解析 (PathParser)**: 从当前文件路径提取 `Date` 和 `Location`。
3.  **去重**: 计算文件部分哈希，对比 SQLite 数据库。
4.  **本地化 (TempManager)**: 如果文件在远程，则下载到临时目录；本地文件则直接引用。
5.  **AI 处理**: 运行检测、画质检测、模型推理。
6.  **路径生成 (PathGenerator)**: 根据模版生成目标位置（支持 `{species_cn}` 等变量）。
7.  **回写 (Metadata Writeback)**: 
    *   写入处理后的照片。
    *   (可选) 写入原始照片。
8.  **索引**: 更新数据库记录。

### 3.2 Web UI 交互
*   **静态资源映射**: 利用 FastAPI 的 `mount` 功能，将 `allowed_roots` 中的物理路径映射为 Web 可访问的 `/static/roots/{n}` URL。
*   **WebSocket 控制台**: 前端通过 WS 连接后端 `TaskManager`，实时获取流水线日志输出。

---

## 4. 安全与性能优化

*   **安全沙箱**: `LocalProvider` 会校验所有路径是否属于 `allowed_roots` 白名单，防止目录遍历攻击。
*   **内存优化**: 
    *   `BioCLIP` 本地推理支持文本特征缓存，识别速度提升 1000 倍。
    *   大量采用 `Generator` 迭代文件，避免一次性加载数万个文件路径。
*   **稳定性**:
    *   `ExifTool` 采用 Argfile 模式，解决 Windows 平台中文路径和标签的乱码问题。
    *   所有阻塞式 Web 路由均采用同步 `def` 定义，运行在独立线程池，确保 Web 界面永不卡死。