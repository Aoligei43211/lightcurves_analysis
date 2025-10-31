'''光变曲线相位折叠绘制工具

功能说明：
    1. 从data_processing模块获取处理后的时间和通量数据
    2. 计算最佳拟合周期并绘制单个相位折叠后的光变曲线图
    3. 提供清晰的图表展示，包括中文标题和标签

实现原理：
    - 使用data_processing模块的get_sorted_data()函数获取处理后的数据
    - 通过period_culculator函数计算最佳折叠周期
    - 对时间数据应用折叠处理并绘制相位折叠图

依赖包：
    - matplotlib: 用于数据可视化
    - numpy: 用于数值计算
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

# 获取折叠周期 - 使用period_culculator函数计算最佳周期
period = period_culculator()
print(f"使用计算得到的最佳周期：{period} 天")

# 执行时间折叠操作
folded_time = np.mod(time, period)

# 绘制单个相位折叠图
plt.figure(figsize=(10, 6))
plt.plot(folded_time, flux, 'b.', markersize=1)  # 使用'.'表示散点图，颜色为蓝色
plt.title(f"HATP7b 的相位折叠图（周期={period:.4f}天）")
plt.xlabel(f"折叠时间（周期={period:.4f}天）")
plt.ylabel("校正后的光通量")
plt.grid(True)  # 添加网格线
plt.tight_layout()
plt.show()