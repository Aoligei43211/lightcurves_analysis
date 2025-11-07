#这是实现模拟光变曲线的函数参考文档

## 1. 基础光变曲线 (base_lightcurve.py)

```python
import numpy as np

def generate_basic_light_curve(duration=100, dt=0.1, period=10, 
                             transit_depth=0.02, transit_duration=1.0):
    """
    生成基础光变曲线 - 数学逻辑说明
    
    数学原理:
    ---------
    基础光变曲线由周期性凌星信号组成，数学表达为:
    
    flux(t) = 1 - δ × I[(t mod P) ∈ [0, D]]
    
    其中:
    - flux(t): 时间t处的流量值
    - δ: 凌星深度 (transit_depth)
    - P: 轨道周期 (period)  
    - D: 凌星持续时间 (transit_duration)
    - I[condition]: 指示函数，条件为真时=1，否则=0
    - t mod P: 时间对周期取模，得到相位
    
    凌星发生时: (t mod P) ∈ [0, D] → flux(t) = 1 - δ
    其他时间: flux(t) = 1
    
    参数说明:
    ---------
    duration: 总观测时间
    dt: 时间步长
    period: 行星轨道周期
    transit_depth: 凌星深度，反映行星与恒星半径比
    transit_duration: 凌星持续时间，反映轨道倾角
    
    返回:
    ------
    time: 时间数组
    flux: 流量数组
    """
    
    # 生成时间序列
    time = np.arange(0, duration, dt)
    
    # 初始化流量为1（无凌星时的归一化流量）
    flux = np.ones_like(time)
    
    # 遍历每个时间点计算流量
    for i, t in enumerate(time):
        # 计算当前相位: (时间 模 周期) / 周期
        phase = (t % period) / period
        
        # 检查是否在凌星期间
        if phase < transit_duration/period:
            # 在凌星期间，流量下降
            flux[i] = 1 - transit_depth
    
    return time, flux

# 测试代码
if __name__ == "__main__":
    time, flux = generate_basic_light_curve()
    print(f"生成 {len(time)} 个数据点")
    print(f"时间范围: {time[0]:.1f} 到 {time[-1]:.1f}")
    print(f"流量范围: {np.min(flux):.3f} 到 {np.max(flux):.3f}")
```

## 2. 凌星深度变化 (transit_depth_variation.py)

```python
import numpy as np

def add_transit_depth_variation(time, flux, base_depth=0.02, 
                              amplitude=0.005, frequency=0.1, 
                              variation_type='all'):
    """
    添加凌星深度变化 - 数学逻辑说明
    
    数学原理:
    ---------
    深度变化模拟凌星深度的周期性变化，反映行星半径变化或恒星活动:
    
    δ(t) = δ₀ + A × sin(2πf × t)
    
    其中:
    - δ(t): 时间t处的凌星深度
    - δ₀: 基础凌星深度 (base_depth)  
    - A: 深度变化振幅 (amplitude)
    - f: 变化频率 (frequency)
    
    对于 'all' 类型: 整体深度随正弦变化
    对于 'transit' 类型: 仅凌星期间的深度变化
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组  
    base_depth: 基础凌星深度
    amplitude: 深度变化振幅
    frequency: 变化频率
    variation_type: 'all' 或 'transit'
    
    返回:
    ------
    varied_flux: 添加深度变化后的流量数组
    """
    
    # 复制基础流量，避免修改原数据
    varied_flux = flux.copy()
    
    # 生成深度变化信号: 正弦波
    depth_variation = amplitude * np.sin(2 * np.pi * frequency * time)
    
    if variation_type == 'all':
        # 整体深度变化 - 影响所有凌星事件
        transit_mask = (flux < 0.99)  # 检测凌星区域（流量下降的区域）
        
        # 对每个凌星点应用变化的深度
        for i in np.where(transit_mask)[0]:
            # 计算当前凌星深度
            current_depth = base_depth + depth_variation[i]
            # 更新流量值
            varied_flux[i] = 1.0 - current_depth
            
    elif variation_type == 'transit':
        # 仅凌星期间深度变化
        transit_indices = np.where(flux < 0.99)[0]  # 找到所有凌星点的索引
        
        if len(transit_indices) > 0:
            # 提取凌星期间的深度变化
            local_depth_variation = depth_variation[transit_indices]
            # 应用变化的深度
            varied_flux[transit_indices] = 1.0 - (base_depth + local_depth_variation)
    
    return varied_flux

# 测试代码  
if __name__ == "__main__":
    # 需要先导入基础光变曲线函数
    from base_lightcurve import generate_basic_light_curve
    
    # 生成基础曲线测试
    time, base_flux = generate_basic_light_curve()
    
    # 添加深度变化
    depth_variation_flux = add_transit_depth_variation(time, base_flux)
    
    print("深度变化测试完成")
    print(f"基础流量标准差: {np.std(base_flux):.6f}")
    print(f"深度变化流量标准差: {np.std(depth_variation_flux):.6f}")
```

## 3. 凌星持续时间变化 TDV (transit_duration_variation.py)

```python
import numpy as np

def add_transit_duration_variation(time, flux, base_period=10, base_duration=1.0,
                                 amplitude=0.1, frequency=0.3):
    """
    添加凌星持续时间变化 (TDV) - 数学逻辑说明
    
    数学原理:
    ---------
    TDV模拟凌星宽度的周期性变化，反映轨道倾角变化或轨道偏心率变化:
    
    D(t) = D₀ + A × sin(2πf × t)
    
    其中:
    - D(t): 时间t处的凌星持续时间  
    - D₀: 基础持续时间 (base_duration)
    - A: 持续时间变化振幅 (amplitude) 
    - f: 变化频率 (frequency)
    
    实际实现中，我们重新构建整个光变曲线，使用变化的持续时间。
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组（用于确定基础参数）
    base_period: 基础轨道周期
    base_duration: 基础凌星持续时间
    amplitude: 持续时间变化振幅
    frequency: 变化频率
    
    返回:
    ------
    varied_flux: 添加持续时间变化后的流量数组
    """
    
    # 创建新的流量数组，全为1（无凌星状态）
    varied_flux = np.ones_like(flux)
    
    # 从基础流量推断凌星深度
    transit_depth = 1.0 - np.min(flux)  # 计算基础凌星深度
    
    # 生成持续时间变化信号
    duration_variation = amplitude * np.sin(2 * np.pi * frequency * time)
    
    # 遍历每个时间点，重新计算凌星状态
    for i, t in enumerate(time):
        # 计算当前持续时间（基础值 + 正弦变化）
        current_duration = base_duration + duration_variation[i]
        # 确保持续时间不为负
        current_duration = max(0.1, current_duration)
        
        # 计算当前相位
        phase = (t % base_period) / base_period
        
        # 检查是否在凌星期间（使用变化的持续时间）
        if phase < current_duration/base_period:
            # 在凌星期间，应用固定的凌星深度
            varied_flux[i] = 1 - transit_depth
    
    return varied_flux

# 测试代码
if __name__ == "__main__":
    from base_lightcurve import generate_basic_light_curve
    
    time, base_flux = generate_basic_light_curve()
    tdv_flux = add_transit_duration_variation(time, base_flux)
    
    print("TDV测试完成")
    print(f"基础流量凌星点数: {np.sum(base_flux < 0.99)}")
    print(f"TDV后凌星点数: {np.sum(tdv_flux < 0.99)}")
```

## 4. 凌星时间漂移 TTV (transit_timing_variation.py)

```python
import numpy as np

def add_transit_timing_variation(time, flux, base_period=10, base_duration=1.0,
                               amplitude=0.2, frequency=0.05):
    """
    添加凌星计时变化 (TTV) - 数学逻辑说明
    
    数学原理:
    ---------
    TTV模拟凌星中心时间的周期性偏移，反映轨道摄动或额外行星影响:
    
    Δt = A × sin(2πf × t)
    t_actual = t_nominal + Δt
    
    其中:
    - Δt: 时间偏移量
    - A: TTV振幅 (amplitude)
    - f: TTV频率 (frequency)  
    - t_nominal: 理论凌星时间 = n × P
    - t_actual: 实际凌星时间
    
    实际实现中，我们调整时间坐标来模拟凌星时间的偏移。
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组
    base_period: 基础轨道周期
    base_duration: 基础凌星持续时间  
    amplitude: TTV振幅
    frequency: TTV频率
    
    返回:
    ------
    varied_flux: 添加TTV后的流量数组
    """
    
    # 创建新的流量数组，全为1
    varied_flux = np.ones_like(flux)
    
    # 从基础流量推断凌星深度
    transit_depth = 1.0 - np.min(flux)
    
    # 生成TTV信号（时间偏移）
    ttv_shift = amplitude * np.sin(2 * np.pi * frequency * time)
    
    # 遍历每个时间点，应用时间偏移
    for i, t in enumerate(time):
        # 调整时间：实际时间 = 理论时间 + TTV偏移
        adjusted_t = t + ttv_shift[i]
        
        # 使用调整后的时间计算相位
        phase = (adjusted_t % base_period) / base_period
        
        # 检查是否在凌星期间
        if phase < base_duration/base_period:
            # 在凌星期间，应用固定的凌星深度
            varied_flux[i] = 1 - transit_depth
    
    return varied_flux

# 测试代码
if __name__ == "__main__":
    from base_lightcurve import generate_basic_light_curve
    
    time, base_flux = generate_basic_light_curve()
    ttv_flux = add_transit_timing_variation(time, base_flux)
    
    print("TTV测试完成") 
    
    # 简单的凌星中心检测
    def find_transit_centers(time, flux):
        """辅助函数：查找凌星中心时间"""
        centers = []
        in_transit = False
        transit_start = 0
        
        for i, (t, f) in enumerate(zip(time, flux)):
            if f < 0.99 and not in_transit:
                in_transit = True
                transit_start = t
            elif f >= 0.99 and in_transit:
                in_transit = False
                centers.append((transit_start + t) / 2)
        
        return centers[:3]  # 返回前3个凌星中心
    
    print(f"基础凌星中心: {find_transit_centers(time, base_flux)}")
    print(f"TTV凌星中心: {find_transit_centers(time, ttv_flux)}")
```

## 5. 综合模拟 (combined_simulation.py)

```python
import numpy as np
from base_lightcurve import generate_basic_light_curve
from transit_depth_variation import add_transit_depth_variation
from transit_duration_variation import add_transit_duration_variation  
from transit_timing_variation import add_transit_timing_variation

def generate_realistic_light_curve(scenario='default'):
    """
    生成现实场景的光变曲线 - 综合各种效应
    
    数学原理:
    ---------
    现实光变曲线是多种物理效应的叠加:
    
    flux_final(t) = [基础光变曲线]
                    × [深度变化效应] 
                    × [TDV效应]
                    × [TTV效应]
                    + [测量噪声]
    
    每种效应都通过调整相应的物理参数来实现。
    
    参数说明:
    ---------
    scenario: 场景类型
        - 'default': 默认参数
        - 'active_star': 活跃恒星场景（强深度变化）
        - 'multi_planet': 多行星系统（强TTV）
        - 'eccentric_orbit': 偏心轨道（强TDV）
    
    返回:
    ------
    time: 时间数组
    complete_flux: 综合效应后的流量数组  
    base_flux: 基础流量数组（用于比较）
    """
    
    # 基础参数
    base_params = {
        'duration': 100,      # 总观测时间
        'dt': 0.1,           # 时间分辨率
        'period': 10,        # 轨道周期
        'transit_depth': 0.02, # 凌星深度
        'transit_duration': 1.0 # 凌星持续时间
    }
    
    # 根据场景调整参数
    scenario_params = {
        'default': {
            'depth_amp': 0.003, 'depth_freq': 0.08,  # 深度变化参数
            'tdv_amp': 0.15, 'tdv_freq': 0.4,       # TDV参数
            'ttv_amp': 0.2, 'ttv_freq': 0.06,       # TTV参数
            'noise_level': 0.001                    # 噪声水平
        },
        'active_star': {
            'depth_amp': 0.008, 'depth_freq': 0.12, # 强深度变化
            'tdv_amp': 0.1, 'tdv_freq': 0.3,
            'ttv_amp': 0.1, 'ttv_freq': 0.04, 
            'noise_level': 0.002
        },
        'multi_planet': {
            'depth_amp': 0.002, 'depth_freq': 0.05,
            'tdv_amp': 0.08, 'tdv_freq': 0.2,
            'ttv_amp': 0.5, 'ttv_freq': 0.08,       # 强TTV
            'noise_level': 0.001
        },
        'eccentric_orbit': {
            'depth_amp': 0.001, 'depth_freq': 0.03,
            'tdv_amp': 0.4, 'tdv_freq': 0.1,        # 强TDV
            'ttv_amp': 0.05, 'ttv_freq': 0.02,
            'noise_level': 0.0015
        }
    }
    
    params = scenario_params.get(scenario, scenario_params['default'])
    
    # 生成基础光变曲线
    time, base_flux = generate_basic_light_curve(**base_params)
    
    # 逐步添加各种效应
    current_flux = base_flux.copy()
    
    # 1. 添加凌星深度变化
    current_flux = add_transit_depth_variation(
        time, current_flux, 
        amplitude=params['depth_amp'], 
        frequency=params['depth_freq'],
        variation_type='all'
    )
    
    # 2. 添加凌星持续时间变化 (TDV)
    current_flux = add_transit_duration_variation(
        time, current_flux,
        amplitude=params['tdv_amp'],
        frequency=params['tdv_freq']
    )
    
    # 3. 添加凌星计时变化 (TTV)
    current_flux = add_transit_timing_variation(
        time, current_flux,
        amplitude=params['ttv_amp'],
        frequency=params['ttv_freq']
    )
    
    # 4. 添加测量噪声（高斯白噪声）
    measurement_noise = np.random.normal(0, params['noise_level'], len(current_flux))
    complete_flux = current_flux + measurement_noise
    
    return time, complete_flux, base_flux

def generate_individual_effects_comparison():
    """
    生成单一效应比较数据
    
    返回所有单一效应的光变曲线，用于分析每种效应的独立影响
    """
    time, base_flux = generate_basic_light_curve()
    
    # 生成各种单一效应
    effects = {
        'base': base_flux,
        'depth_only': add_transit_depth_variation(time, base_flux.copy()),
        'tdv_only': add_transit_duration_variation(time, base_flux.copy()), 
        'ttv_only': add_transit_timing_variation(time, base_flux.copy()),
        'noise_only': base_flux + np.random.normal(0, 0.001, len(base_flux))
    }
    
    return time, effects

# 测试代码
if __name__ == "__main__":
    print("生成综合光变曲线...")
    
    # 测试不同场景
    scenarios = ['default', 'active_star', 'multi_planet', 'eccentric_orbit']
    
    for scenario in scenarios:
        time, complete_flux, base_flux = generate_realistic_light_curve(scenario)
        print(f"{scenario}场景: 流量标准差 = {np.std(complete_flux):.6f}")
    
    # 测试单一效应
    time, effects = generate_individual_effects_comparison()
    print(f"生成 {len(effects)} 种单一效应数据")
```

## 术语修正说明

现在所有文件都使用了正确的术语定义：

1. **TTV (Transit Timing Variations)**: 凌星中心时间变化 - 在 `transit_timing_variation.py` 中实现
2. **TDV (Transit Duration Variations)**: 凌星持续时间变化 - 在 `transit_duration_variation.py` 中实现  
3. **Transit Depth Variation**: 凌星深度变化 - 在 `transit_depth_variation.py` 中实现

每个文件都有详细的数学逻辑说明和测试代码，可以直接运行验证功能。