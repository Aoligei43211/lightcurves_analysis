'''光变曲线相位折叠与误差可视化工具

功能说明：
    1. 从data_processing模块获取处理后的时间和通量数据
    2. 计算最佳拟合周期并绘制相位折叠后的光变曲线图，包含误差条
    3. 提供高质量的数据可视化，包括误差分析和统计信息
    
实现原理：
    - 使用data_processing模块的get_sorted_data()函数获取处理后的数据
    - 通过period_culculator函数计算最佳折叠周期
    - 对时间数据应用折叠处理，对通量数据计算误差统计
    - 绘制带有误差条的相位折叠图
    
依赖包：
    - matplotlib: 用于数据可视化
    - numpy: 用于数值计算和统计分析
    - lightcurve_period: 自定义模块，提供周期计算功能
    - data_processing: 自定义模块，提供数据处理功能'''

import numpy as np
from matplotlib import pyplot as plt
from lightcurve_period import period_culculator
from data_processing import get_sorted_data

# 设置中文字体支持
plt.rcParams["font.family"] = ["Microsoft YaHei"]  # 设置全局字体为微软雅黑，支持中文显示
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 从data_processing模块获取数据
print("正在从data_processing获取处理后的数据...")
time, flux = get_sorted_data()

if time is None or flux is None:
    print("无法获取数据，程序退出")
    exit()

print(f"成功获取数据：时间点数量 = {len(time)}, 通量数据数量 = {len(flux)}")

# 计算通量数据的统计特性
flux_mean = np.mean(flux)
flux_std = np.std(flux)
flux_min = np.min(flux)
flux_max = np.max(flux)

print(f"通量统计信息：")
print(f"  平均值: {flux_mean:.6f}")
print(f"  标准差: {flux_std:.6f}")
print(f"  最小值: {flux_min:.6f}")
print(f"  最大值: {flux_max:.6f}")

# 获取折叠周期 - 使用period_culculator函数计算最佳周期
period = period_culculator()
print(f"使用计算得到的最佳周期：{period} 天")

# 执行时间折叠操作
folded_time = np.mod(time, period)

# 为每个数据点计算误差
# 这里使用标准差的1/3作为误差条长度，实际应用中可能需要使用数据本身的误差信息
errors = np.ones_like(flux) * flux_std / 3.0

# 创建一个更大的画布用于更详细的展示
plt.figure(figsize=(12, 8))

# 绘制带有误差条的相位折叠图
errorbar = plt.errorbar(
    folded_time, 
    flux, 
    yerr=errors, 
    fmt='b.', 
    markersize=2, 
    ecolor='lightblue', 
    elinewidth=1, 
    capsize=1, 
    label=f'周期={period:.4f}天'
)

# 添加统计信息文本框
stats_text = f"\n".join([
    f"平均值: {flux_mean:.6f}",
    f"标准差: {flux_std:.6f}",
    f"数据点数: {len(time)}",
    f"周期: {period:.4f} 天"
])

plt.figtext(0.02, 0.02, stats_text, fontsize=10, 
           bbox=dict(facecolor='white', alpha=0.8, boxstyle='round,pad=0.5'))

# 设置图表标题和标签
plt.title(f"HATP7b 的相位折叠图（带误差分析）")
plt.xlabel(f"折叠时间（周期={period:.4f}天）")
plt.ylabel("校正后的光通量")

# 添加网格线和图例
plt.grid(True, linestyle='--', alpha=0.7)
plt.legend(loc='best')

# 优化布局并显示
plt.tight_layout()
plt.subplots_adjust(bottom=0.1)
plt.show()