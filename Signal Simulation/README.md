# 天文信号模拟工具

本项目实现了多种天文信号噪声模拟功能，可用于生成带各种噪声的凌星信号。

## 功能说明

### 1. TTV噪声模拟（凌星时间变化）
- 文件: `ttv_only.py`
- 功能: 生成带凌星时间变化(TTV)噪声的信号
- 原理: 通过周期性偏移凌星时间点来模拟TTV现象
- 核心参数: TTV振幅、频率

### 2. TDV噪声模拟（凌星持续时间变化）
- 文件: `tdv_only.py`
- 功能: 生成带凌星持续时间变化(TDV)噪声的信号
- 原理: 通过周期性改变凌星持续时间来模拟TDV现象
- 核心参数: TDV振幅、频率

### 3. 凌星深度变化噪声模拟
- 文件: `depth_variation.py`
- 功能: 生成带凌星深度变化噪声的信号
- 原理: 支持单频率或多频率叠加的深度变化
- 核心参数: 频率列表、振幅列表、变化类型

### 4. 组合噪声模拟
- 文件: `combined_noise.py`
- 功能: 组合多种噪声类型（TTV、TDV、深度变化）
- 原理: 按配置依次应用各种噪声，支持灵活组合
- 特点: 可通过配置文件控制每种噪声的开启/关闭和参数

## 配置文件

配置文件位于: `..\config\signal_simulation_config.json`

主要配置项:
- `base_params`: 基础光变曲线参数
- `ttv_params`: TTV噪声参数
- `tdv_params`: TDV噪声参数
- `depth_variation_params`: 深度变化噪声参数
- `output`: 输出文件和组名配置

## 使用方法

### 1. 直接运行单个模拟文件

```bash
# 生成TTV噪声信号
python ttv_only.py

# 生成TDV噪声信号
python tdv_only.py

# 生成深度变化噪声信号
python depth_variation.py

# 生成组合噪声信号
python combined_noise.py
```

### 2. 指定配置文件运行

```bash
python ttv_only.py --config path/to/custom_config.json
```

### 3. 作为模块导入使用

```python
from ttv_only import generate_ttv_signal
from tdv_only import generate_tdv_signal
from depth_variation import generate_depth_variation_signal
from combined_noise import generate_combined_noise_signal

# 生成TTV信号
time, base_flux, ttv_flux = generate_ttv_signal()

# 生成组合噪声信号
time, base_flux, combined_flux, applied_noises = generate_combined_noise_signal()
```

## 输出格式

所有模拟信号都保存在HDF5文件中（默认路径见配置文件），按信号类型分组存储。

HDF5文件结构:
- `/ttv_only`: TTV噪声信号
- `/tdv_only`: TDV噪声信号
- `/depth_variation`: 深度变化噪声信号
- `/combined_noise`: 组合噪声信号

每个组包含:
- `time`: 时间序列数据
- `flux`: 流量数据
- 元数据属性（包含生成参数、时间戳等）

## 依赖项

- Python 3.6+
- NumPy
- h5py

## 安装依赖

```bash
pip install numpy h5py
```

## 注意事项

1. 确保配置文件中的路径使用双反斜杠（Windows系统）
2. 所有时间参数必须为正数
3. 凌星深度必须在(0, 1)范围内
4. 多频率深度变化时，频率列表和振幅列表长度必须相同
5. 振幅参数必须为非负数

## 错误处理

所有函数都包含完整的参数验证和异常处理，运行时错误会被捕获并提供详细信息。