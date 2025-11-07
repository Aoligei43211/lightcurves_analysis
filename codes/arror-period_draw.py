
'''绘制周期图
实现功能：
    1. 绘制周期图，展示差值的方差——周期的关系
    2. 支持自定义周期范围和精度
    3. 从HDF5文件读取数据
实现过程细节及原理：
    一、获取数据
        1.从HDF5文件中获取处理后的数据（时间time和光通量flux）
    二、循环遍历周期范围
        2. 循环遍历周期（用period存储，初始值为start，终值为end，每次增加step）范围，每次增加指定精度
        3. 对每个周期，进行时间折叠操作（使用numpy的mod函数来进行取余），将时间数据映射到[0,period)区间
        4. 对折叠后的时间数据进行排序从而得到对应于周期的flux序列（排序后的time_folded的时间的索引没变，依然对应于原来的flux的索引，而time_foleded的时间顺序是折叠之后的顺序，将折叠之后的顺序通过索引给flux重新排序，让flux的数据与原来的时间数据对应起来）
        5. 计算排序后的flux序列的差值方差，作为该周期的指标
        6. 存储每个周期及其对应的差值方差
    三、绘制周期图
        7. 使用matplotlib.pyplot绘制周期图，x轴为周期，y轴为差值的方差
        8. 绘制完成后，显示周期图
'''

import numpy as np
from hdf5_manager import HDF5Manager
from config_manager import ConfigManager
from matplotlib import pyplot as plt

# 设置中文字体支持
plt.rcParams["font.family"] = ["Microsoft YaHei"]  # 设置全局字体为微软雅黑，支持中文显示
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 后续使用numpy的arange函数生成周期数组，这里不需要预先定义

# 指定绘制精度
while True:
    try:
        precision_input = input("请输入绘制精度（10的负指数）：")
        if not precision_input:  # 处理空输入
            print("错误：请输入有效的精度值")
            continue
        precision = int(precision_input)
        if precision <= 0:  # 确保精度为正数
            print("错误：精度必须为正整数")
            continue
        break
    except ValueError:
        print("错误：请输入有效的整数值")

# 指定循环范围
while True:
    try:
        start_input = input("请输入周期起点（浮点数）：")
        if not start_input:  # 处理空输入
            print("错误：请输入有效的周期起点")
            continue
        start = float(start_input)
        if start <= 0:  # 确保起点为正数
            print("错误：周期起点必须为正数")
            continue
        
        end_input = input("请输入周期终点（浮点数）：")
        if not end_input:  # 处理空输入
            print("错误：请输入有效的周期终点")
            continue
        end = float(end_input)
        if end <= start:  # 确保终点大于起点
            print("错误：周期终点必须大于周期起点")
            continue
        break
    except ValueError:
        print("错误：请输入有效的浮点数值")

# 只调用一次数据读取
print("arro-period_draw.py正在从HDF5文件获取数据...")
try:
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 从配置文件获取HDF5文件路径
    hdf5_path = config_manager.get('data.hdf5_path')
    target_name = 'HATP7b'  # 目标星体名称
    file_name = 'processed_combined'  # 综合处理后的数据组名称
    
    # 初始化HDF5管理器
    hdf5_manager = HDF5Manager(hdf5_path)
    
    # 从HDF5文件读取数据
    # 首先尝试读取处理后的数据
    # 读取处理后的光通量数据（第二个参数为属性数据，可忽略）
    denoised_flux, _ = hdf5_manager.get_processed_data(target_name, file_name)
    # 如果没有处理后的数据，尝试读取预处理数据
    if denoised_flux is None:
        print("未找到处理后的数据，尝试读取预处理数据...")
        time, flux = hdf5_manager.get_preprocessed_data(target_name, file_name)
    else:
        # 如果有处理后的数据，还需要读取对应的时间数据
        print("找到处理后的数据，正在读取时间数据...")
        time, _ = hdf5_manager.get_preprocessed_data(target_name, file_name)
        flux = denoised_flux
    
    # 如果仍然没有数据，尝试读取综合数据
    if time is None or flux is None:
        print("未找到预处理或处理后的数据，尝试读取综合数据...")
        time, flux, _, _ = hdf5_manager.get_comprehensive_data(target_name)
    
    # 检查数据有效性
    if time is None or flux is None or len(time) == 0 or len(flux) == 0:
        print("错误：无法获取有效数据，程序退出")
        exit()
        
    print(f"成功获取数据：时间点数量 = {len(time)}, 通量数据数量 = {len(flux)}")
except Exception as e:
    print(f"获取数据时发生错误：{e}")
    print("程序退出")
    exit()

# 循环设计 - 使用numpy的arange函数生成均匀间隔的周期数组
# 这样可以避免浮点数精度问题，同时提高代码可读性
step = 10 ** (-precision)
periods = np.arange(start, end + step, step)
# 初始化存储差值方差的数组
D_value = []

# 遍历每个周期，计算对应的差值方差
for period in periods:
    # 时间折叠
    time_folded = np.mod(time, period)  # 获取时间数据并进行取余操作

    # 处理flux，使其变成对应于time_folded的flux（flux和time的索引天然对应，用排序后的索引，flux对应的仍然是time只是按折叠后的时间顺序排序）
    index = np.argsort(time_folded)#返回time_folded排序后按大小排列的时间索引，每个索引对应于原来flux的索引
    sorted_flux = flux[index]#根据索引排序flux，得到对应于折叠后time_folded的flux序列

    # 计算差值方差
    D_value_variance = np.var(np.diff(sorted_flux))

    # 存储差值方差
    D_value.append(D_value_variance)

#绘图
plt.figure(figsize=(15,7))
plt.plot(periods,D_value,'b-',markersize=1)
plt.ylabel("差值方差")
plt.xlabel(f"周期 精度=10^(-{precision})")
plt.title(f"方差_周期图 起点={start} 终点={end} 精度={precision}")
plt.grid(True)
plt.show()