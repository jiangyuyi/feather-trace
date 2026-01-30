# 鸟纲目科属中文问题解决方案

## 问题分析

**问题位置**: `src/metadata/ioc_manager.py` 的 `import_from_excel` 方法（第131-200行）

**根本原因**: IOC Excel文件中的 `Family` 和 `Order` 列只包含拉丁名，没有中文名。代码假设这些列包含拉丁名，并且将它们同时存储到：
- `family_cn`（科中文）字段
- `order_cn`（目中文）字段

这导致这两个字段实际上存储的是拉丁名而不是中文名。

## 解决方案

### 1. 提取鸟纲目科属中文映射

从 `data/references/动物界-脊索动物门-2025-10626.xlsx` 文件中提取鸟纲的目科属中文映射：

```bash
# 提取脚本生成了以下映射文件：
data/references/
├── bird_order_mapping.csv    # 目拉丁名 -> 目中文名 (26个目)
├── bird_family_mapping.csv   # 科拉丁名 -> 科中文名 (115个科)
└── bird_genus_mapping.csv    # 属拉丁名 -> 属中文名 (504个属)
```

### 2. 更新 IOCManager 导入逻辑

修改了 `src/metadata/ioc_manager.py` 的 `import_from_excel` 方法：

- 添加了 `order_mapping` 和 `family_mapping` 参数
- 在导入时使用这些映射填充中文目科属字段
- 优先使用映射的中文名，如果没有则使用拉丁名

### 3. 更新导入脚本

修改了 `scripts/import_ioc_data.py`：

- 从CSV文件加载目科属中文映射
- 在导入IOC数据时传递这些映射
- 支持已有的属中文映射文件加载

### 4. 添加配置

在 `config/settings.yaml` 中添加了：
```yaml
references_path: "data/references"
```

### 5. 执行更新

运行了更新脚本 `update_ioc_with_chinese_taxonomy.py`：

- 从动物界文件提取鸟纲映射
- 更新了数据库中10750条记录的中文目科属

## 验证数据

更新后的数据示例：
```
Species: 苍鹰 (Accipiter gentilis)
  Order: ACCIPITRIFORMES (鹰形目)
  Family: Accipitridae (鹰科)
  Genus: Accipiter (鹰属)
```

## 使用方法

### 重新导入IOC数据（带中文目科属）

```bash
python scripts/import_ioc_data.py
```

脚本会自动：
1. 从 `data/references/bird_*.csv` 文件加载中文映射
2. 在导入IOC数据时使用这些映射填充中文字段

### 更新现有数据库

如果数据库已经导入过但缺少中文目科属：

```bash
python update_ioc_with_chinese_taxonomy.py
```

这个脚本会：
1. 提取鸟纲映射
2. 更新所有鸟类记录的中文目科属字段

## 注意事项

1. **Windows命令行显示**: 由于Windows命令行的UTF-8支持问题，中文名称在终端中可能显示为乱码，但数据库中的数据是正确的。

2. **文件路径**: 确保 `data/references/` 目录下有：
   - `bird_order_mapping.csv`
   - `bird_family_mapping.csv`
   - `bird_genus_mapping.csv`

3. **中文来源**: 所有中文名称来源于权威的《动物界-脊索动物门》Excel文件，确保准确性。

## 文件结构

```
data/references/
├── Multiling IOC 15.1_d.xlsx          # IOC物种列表
├── 动物界-脊索动物门-2025-10626.xlsx    # 完整分类学数据
├── bird_order_mapping.csv              # 目中文名映射
├── bird_family_mapping.csv             # 科中文名映射
└── bird_genus_mapping.csv              # 属中文名映射
```

## 统计信息

- **目数**: 26个（如鹰形目、雀形目、雁形目等）
- **科数**: 115个（如鹰科、雀科、鸭科等）
- **属数**: 411个（如鹰属、麻雀属、雁属等）
- **更新记录数**: 10,750条鸟类物种记录

## 未来改进

1. **自动化**: 可以定期从权威来源更新映射文件
2. **完整性检查**: 添加验证机制确保所有拉丁名都有对应的中文
3. **性能优化**: 对于大型映射文件，可以考虑使用数据库表存储