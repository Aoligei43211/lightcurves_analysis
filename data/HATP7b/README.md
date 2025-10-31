# HATP7b行星数据目录

本目录用于存放HATP7b系外行星的观测数据文件。

## 数据来源

这些数据来自开普勒太空望远镜的观测，包含了HATP7b行星凌星事件的光变曲线数据。

## 文件格式

数据文件为FITS格式，这是天文数据的标准格式。每个FITS文件包含以下关键字段：
- TIME: 观测时间（BJD - 2454833.0）
- PDCSAP_FLUX: 预处理后的恒星通量数据

## 数据处理

使用仓库中的`code/data_processing_sigle.py`或`code/data_processing.py`模块可以处理这些数据文件。

## 注意事项

1. 请将从NASA Exoplanet Archive或其他来源下载的HATP7b相关FITS文件存放在此目录
2. 文件命名建议遵循Kepler标准命名格式
3. 处理前请确保安装了所需的Python库（见根目录requirements.txt）
