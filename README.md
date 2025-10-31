# 天文光变曲线数据分析仓库

## 项目简介

本仓库用于天文光变曲线数据的处理、分析和可视化。主要功能包括FITS文件读取、数据处理、周期计算、光变曲线绘制等。

## 项目结构

```
├── data/           # 数据文件目录
│   └── HATP7b/     # HATP7b行星相关数据
├── code/           # 代码文件目录
│   ├── data_processing.py           # 数据处理模块
│   ├── data_processing_sigle.py     # 单文件数据处理模块
│   ├── lightcurve_period.py         # 周期计算模块
│   ├── light_curve_draw_sigle.py    # 单文件光变曲线绘制
│   ├── lightcurve_period_draw.py    # 周期计算结果绘制
│   └── ...                          # 其他辅助脚本
├── LICENSE         # MIT开源协议
└── README.md       # 项目说明文档
```

## 功能模块

### 1. 数据处理
- `data_processing.py`: 多文件数据处理主模块
- `data_processing_sigle.py`: 单文件数据处理模块，支持读取指定的FITS文件

### 2. 周期分析
- `lightcurve_period.py`: 实现多轮迭代搜索算法，计算光变曲线的最佳周期

### 3. 可视化
- `light_curve_draw_sigle.py`: 单文件光变曲线绘制
- `lightcurve_period_draw.py`: 周期分析结果可视化

## 依赖项

- Python 3.7+
- NumPy
- Astropy (用于FITS文件处理)
- Matplotlib (用于数据可视化)

## 使用方法

### 基本数据处理
```python
from code.data_processing_sigle import get_sorted_data

# 读取单个FITS文件
time, flux = get_sorted_data(file_path='path/to/your/file.fits')
```

### 周期计算
```python
from code.lightcurve_period import period_culculator

# 计算最佳周期
optimal_period = period_culculator(time, flux)
```

## 作者

[您的姓名]

## 许可证

本项目采用MIT许可证 - 详情请见LICENSE文件
