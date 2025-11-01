# 天文数据分析系统

一个用于处理和分析天文光变曲线的Python工具集，支持TESS数据格式，提供数据预处理、降噪处理和周期分析功能。

## 功能特性

### 核心功能
- **HDF5数据管理**: 使用HDF5格式高效存储和管理天文数据
- **多卷积核降噪**: 支持多种卷积核参数的高斯降噪算法
- **周期图绘制**: 自动计算和绘制光变曲线的周期图
- **配置驱动处理**: 基于JSON配置文件的数据处理流程

### 数据处理流程
1. **数据读取**: 从FITS文件读取TESS光变曲线数据
2. **预处理**: 时间标准化和通量归一化
3. **降噪处理**: 多卷积核高斯平滑降噪
4. **周期分析**: 计算最佳周期并绘制周期图
5. **结果存储**: 将处理结果保存到HDF5文件

## 项目结构

```
astronomy/
├── codes/                 # 源代码目录
│   ├── config_manager.py  # 配置管理模块
│   ├── hdf5_manager.py    # HDF5数据管理
│   ├── lightcurves_filtering.py  # 光变曲线降噪
│   ├── arror-period_draw.py      # 周期图绘制
│   └── ...
├── config/                # 配置文件目录
│   └── app_config.json    # 应用配置
├── data/                  # 数据文件目录
│   ├── HATP7b/           # HATP7b目标数据
│   └── hatp7b_data.h5    # HDF5数据文件
└── README.md             # 项目说明
```

## 安装依赖

安装所需的Python包：

```bash
pip install -r requirements.txt
```

## 使用方法

### 1. 配置设置
编辑 `config/app_config.json` 文件，设置数据路径和处理参数。

### 2. 数据预处理
运行数据预处理脚本，将FITS文件转换为HDF5格式：

```python
from codes.data_processing import preprocess_data
preprocess_data()
```

### 3. 降噪处理
使用多卷积核进行降噪处理：

```python
from codes.lightcurves_filtering import noise_reduction
noise_reduction()
```

### 4. 周期分析
绘制光变曲线的周期图：

```python
from codes.arror_period_draw import main
main()
```

## 配置说明

主要配置参数：

- **数据路径**: `data.base_path`, `data.hdf5_path`
- **处理参数**: `processing.gaussian_sigma`, `processing.normalization`
- **卷积核配置**: `processing.noise_reduction.kernels`
- **周期搜索**: `processing.period_search_range`

## 技术栈

- **Python 3.x**
- **NumPy**: 数值计算
- **Matplotlib**: 数据可视化
- **H5Py**: HDF5文件操作
- **Astropy**: 天文数据处理

## 许可证

本项目采用MIT许可证。

## 贡献

欢迎提交Issue和Pull Request来改进这个项目。
