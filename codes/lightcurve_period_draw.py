'''光变曲线相位折叠绘制工具

功能说明：
    1. 从HDF5文件获取处理后的时间和通量数据
    2. 计算最佳拟合周期并绘制单个相位折叠后的光变曲线图
    3. 提供清晰的图表展示，包括中文标题和标签

实现原理：
    - 使用HDF5管理器从配置文件指定的路径读取预处理数据
    - 通过period_culculator函数计算最佳折叠周期
    - 对时间数据应用折叠处理并绘制相位折叠图

依赖包：
    - matplotlib: 用于数据可视化
    - numpy: 用于数值计算
    - lightcurve_period: 自定义模块，提供周期计算功能
    - config_manager: 配置管理模块
    - hdf5_manager: HDF5数据管理模块'''

import numpy as np
import h5py
from matplotlib import pyplot as plt
from config_manager import ConfigManager
from hdf5_manager import HDF5Manager

# 设置中文字体支持
plt.rcParams["font.family"] = ["Microsoft YaHei"]  # 设置全局字体为微软雅黑，支持中文显示
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 初始化配置管理器和HDF5管理器
config_manager = ConfigManager()
hdf5_path = config_manager.get('data.hdf5_path')
target_name = config_manager.get('data.hdf5_targets.default_target')# 获取默认目标名称
file_name = config_manager.get('data.hdf5_targets.default_file')# 获取默认文件名

# 从HDF5文件获取数据
print("正在从HDF5文件获取处理后的数据...")
hdf5_manager = HDF5Manager(hdf5_path)

# 从HDF5文件读取time和flux数据
time_dataset = config_manager.get('data.hdf5_datasets.time_data')
flux_dataset = config_manager.get('data.hdf5_datasets.flux_data')

time, flux = hdf5_manager.read_preprocessed_data(target_name, file_name, time_dataset, flux_dataset)

if time is None or flux is None:
    print("无法从HDF5文件读取数据，程序退出")
    exit()

print(f"成功获取数据：时间点数量 = {len(time)}, 通量数据数量 = {len(flux)}")

# 从HDF5文件获取periodogram数据和最佳周期
period = 2.204736  # 默认值
try:
    print(f"尝试从HDF5文件读取periodogram数据")
    print(f"目标路径: {hdf5_path}")
    print(f"目标组: {target_name}")
    print(f"文件组: {file_name}")
    
    # 使用h5py直接读取periodogram数据，根据HDF5结构调整路径
    with h5py.File(hdf5_path, 'r') as f:
        # 构建完整的periodogram路径
        # 根据指令，使用HATP7b/processed_combined/processed/periodogram路径
        if target_name == 'HATP7b':
            # 对于HATP7b目标，使用特定路径
            periodogram_path = 'HATP7b/processed_combined/processed/periodogram'
        else:
            # 对于其他目标，使用原有路径结构
            periodogram_path = f'{target_name}/{file_name}/processed/periodogram'
        
        print(f"完整路径: {periodogram_path}")
        
        # 检查路径是否存在
        if periodogram_path in f:
            periodogram = f[periodogram_path][:]
            print(f"成功读取periodogram数据，形状: {periodogram.shape}")
            
            # 检查是否有best_period属性
            if 'best_period' in f[periodogram_path].attrs:
                period = f[periodogram_path].attrs['best_period']
                print(f"从属性读取最佳周期: {period} 天")
            else:
                # 如果没有属性，从数据中计算（方差最小的周期）
                periods = periodogram[:, 0]  # 第一列是周期值
                variances = periodogram[:, 1]  # 第二列是方差值
                best_idx = np.argmin(variances)
                period = periods[best_idx]
                print(f"从periodogram数据计算的最佳周期：{period} 天")
        else:
            # 打印HDF5文件结构以调试
            print(f"路径 {periodogram_path} 不存在！")
            print(f"HDF5文件顶层结构: {list(f.keys())}")
            if 'HATP7b' in f:
                print(f"HATP7b组内容: {list(f['HATP7b'].keys())}")
                if 'processed_combined' in f['HATP7b']:
                    print(f"processed_combined组内容: {list(f['HATP7b/processed_combined'].keys())}")
                    if 'processed' in f['HATP7b/processed_combined']:
                        print(f"processed组内容: {list(f['HATP7b/processed_combined/processed'].keys())}")
            
            # 尝试导入并运行period_culculator函数计算周期数据
            print("未找到periodogram数据，正在调用period_culculator计算最佳周期...")
            try:
                # 导入period_culculator函数
                from lightcurve_period import period_culculator
                # 调用函数计算并保存最佳周期
                best_period, _ = period_culculator()
                print(f"成功计算并保存最佳周期: {best_period} 天")
                period = best_period
                
                # 重新打开HDF5文件读取新生成的周期数据
                print("重新读取计算后的periodogram数据...")
                with h5py.File(hdf5_path, 'r') as f_new:
                    if periodogram_path in f_new:
                        periodogram = f_new[periodogram_path][:]
                        print(f"成功读取新生成的periodogram数据，形状: {periodogram.shape}")
                        
                        # 再次检查best_period属性
                        if 'best_period' in f_new[periodogram_path].attrs:
                            period = f_new[periodogram_path].attrs['best_period']
                            print(f"从属性读取最佳周期: {period} 天")
                    else:
                        print("计算完成后仍未找到periodogram数据，使用计算结果")
                        
            except Exception as calc_error:
                print(f"调用period_culculator时出错：{calc_error}")
                print("使用默认周期：2.204736 天")
                import traceback
                traceback.print_exc()
except Exception as e:
    print(f"获取periodogram数据时出错：{e}")
    print("使用默认周期：2.204736 天")
    import traceback
    traceback.print_exc()

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
