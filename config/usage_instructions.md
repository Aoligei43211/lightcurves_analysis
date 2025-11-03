# 天文数据分析系统配置文件使用说明

## 配置文件概述
`app_config.json` 是系统的核心配置文件，定义了数据路径、处理参数、可视化和日志设置。所有参数通过 `config_manager.py` 统一管理。

## 配置对象详解

### 1. data 数据路径配置
- **base_path**: 基础数据目录路径
- **hatp7b_path**: HATP7b 星体数据目录
- **hdf5_path**: HDF5 数据文件路径
- **hdf5_groups**: HDF5 文件中的组结构
  - `preprocessed`: 预处理数据组
  - `processed`: 处理后数据组  
  - `attributes`: 属性数据组
- **hdf5_datasets**: HDF5 数据集名称
  - `time_data`: 时间数据
  - `flux_data`: 光通量数据
  - `processed_time`: 处理后时间数据
  - `processed_flux`: 处理后光通量数据
- **hdf5_targets**: HDF5 目标配置
  - `default_target`: 默认目标星体（如 HATP7b）
  - `default_file`: 默认文件组名称
- **对应文件**: 
  - `hdf5_manager.py` - 数据存储和读取
  - `data_processing.py` - 数据处理
  - `天文文件提取.py` - 数据提取

### 2. processing 处理参数配置
- **gaussian_sigma**: 高斯滤波标准差
- **normalization**: 是否进行数据标准化
- **noise_reduction**: 降噪参数
  - `convolution_configs`: 多组卷积核配置
    - `window_size`: 卷积窗口大小
    - `sigma`: 高斯标准差
- **period_search_range**: 周期搜索范围 [最小值, 最大值]
- **period**: 周期分析参数
  - `start`: 周期搜索起始值
  - `end`: 周期搜索结束值
  - `max_iterations`: 最大迭代次数
  - `initial_precision`: 初始精度
- **对应文件**:
  - `lightcurves_filtering.py` - 降噪处理
  - `lightcurve_period.py` - 周期分析

### 3. visualization 可视化配置
- **figure_size**: 图表尺寸 [宽度, 高度]
- **dpi**: 图像分辨率
- **save_format**: 保存格式
- **colors**: 颜色方案列表
- **对应文件**:
  - `lightcurve_period_draw.py` - 周期图表绘制
  - `lightcurve_draw.py` - 光变曲线绘制

### 4. logging 日志配置
- **level**: 日志级别
- **format**: 日志格式
- **file**: 日志文件路径
- **对应文件**:
  - `logging_config.py` - 日志系统配置

## 调试说明

### （1）如何修改要分析的文件地址
**修改数据源文件**:
- 编辑 `data.hdf5_targets.default_file` 参数
- 示例：从 "processed_combined" 改为 "1_tess2019198215352-s0014-0000000424865156-0150-s_lc"
- 修改后代码会自动读取指定子文件的数据

**修改数据目录**:
- 更新 `data.base_path` 或具体路径参数
- 确保新路径存在且包含有效数据

### （2）其他调试说明

**卷积核参数调试**:
- `processing.noise_reduction.convolution_configs` 包含多组参数
- 在 `lightcurves_filtering.py` 中用户输入 "y" 时，所有配置轮流生效
- 当前设计：输出数据会覆盖，建议修改为每个配置创建独立数据集

**周期分析参数调试**:
- 修改 `processing.period` 中的参数调整搜索范围和精度
- 注意：代码已移除硬编码默认值，完全依赖配置文件

**数据存储调试**:
- 使用 `check_hdf5_structure.py` 检查 HDF5 文件结构
- 确认目标组和文件组的存在性

## 基于对话历史的补充说明

1. **参数调用机制**: 所有配置通过 `config_manager.get()` 读取，无硬编码默认值
2. **卷积核应用**: 多组参数在降噪时依次应用，结果存储在同一 HDF5 路径
3. **文件组织结构**: HDF5 文件采用两级结构 - 目标组 → 文件组
4. **颜色配置使用**: 在绘图函数中通过索引访问 colors 数组
5. **日志系统**: 自动创建日志目录和文件，按配置级别记录

## 快速调试步骤
1. 确定要调试的模块（如周期分析、降噪处理）
2. 在配置文件中找到对应参数段
3. 修改参数值
4. 运行相应 Python 脚本
5. 检查输出结果和日志文件

注意：修改配置后无需重启系统，配置在运行时动态加载。