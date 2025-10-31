# 天文光变曲线数据分析仓库

本仓库用于天文光变曲线数据的处理、分析和可视化，特别是针对系外行星过境数据的研究。

## 项目结构

```
lightcurves_analysis/
├── code/                    # 代码目录
│   ├── data_processing.py   # 多文件数据处理模块
│   ├── data_processing_sigle.py # 单文件数据处理模块
│   ├── lightcurve_period.py # 周期计算模块（多轮迭代搜索算法）
│   ├── lightcurve_period_draw.py # 光变曲线相位折叠绘制工具
│   ├── arror-period_draw.py # 带误差分析的光变曲线相位折叠绘制工具
│   └── example_usage.py     # 使用示例脚本
├── data/                    # 数据目录
│   └── HATP7b/              # HATP7b行星数据
│       └── README.md        # 数据说明文档
├── README.md                # 项目说明文档（当前文件）
├── LICENSE                  # MIT许可证
└── requirements.txt         # 项目依赖
```

## 功能模块

### 1. 数据处理模块
- `data_processing.py`: 处理多个FITS文件，包括读取数据、移除大间隙、降噪和通量校正
- `data_processing_sigle.py`: 处理单个FITS文件的专用模块，提供更灵活的文件路径输入

### 2. 周期分析模块
- `lightcurve_period.py`: 实现多轮迭代搜索算法的周期计算，通过动态调整搜索范围和精度找到最佳周期

### 3. 可视化模块
- `lightcurve_period_draw.py`: 绘制相位折叠后的光变曲线图，展示行星过境特征
- `arror-period_draw.py`: 增强版绘图工具，添加误差条和统计信息，提供更详细的数据分析视图
- `example_usage.py`: 完整分析流程示例，从数据读取到周期计算再到可视化

## 依赖项

- Python 3.7+
- NumPy
- Astropy
- Matplotlib
- SciPy

## 使用方法

### 数据处理

```python
# 使用多文件数据处理
from data_processing import get_sorted_data

time, flux = get_sorted_data()
```

```python
# 使用单文件数据处理
from data_processing_sigle import process_single_file

time, flux = process_single_file("path/to/your/fits/file.fits")
```

### 周期计算

```python
from lightcurve_period import period_culculator

# 计算最佳周期（可自定义最大迭代次数和滑动窗口大小）
period = period_culculator(max_iterations=10, window_size=5)
print(f"最佳周期: {period} 天")
```

### 数据可视化

```python
# 基本相位折叠图
# 直接运行 lightcurve_period_draw.py

# 带误差分析的相位折叠图
# 直接运行 arror-period_draw.py
```

### 完整工作流示例

请参考 `example_usage.py` 文件，它展示了从数据读取、处理、周期计算到可视化的完整流程。

## 数据说明

HATP7b 是一个热木星系外行星，围绕着一颗位于天鹅座的恒星运行。本仓库包含的观测数据来自NASA的开普勒太空望远镜。

详细的数据说明请查看 `data/HATP7b/README.md` 文件。

## 许可证

本项目采用 MIT 许可证 - 详情请查看 LICENSE 文件