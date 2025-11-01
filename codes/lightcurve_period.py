'''天文光变曲线周期分析工具

功能说明：
    1. 基于方差分析方法计算并返回天体光变数据的最佳拟合周期
    2. 从配置文件读取输入参数，支持批量处理
    3. 采用多轮迭代搜索算法，逐步锁定最优周期并提升精度
    4. 集成滑动平均平滑处理，减少噪声干扰
    5. 将周期分析结果存储到HDF5文件对应组中

实现原理：
    1. 从配置文件初始化搜索区间和精度参数
    2. 多轮迭代搜索，每轮执行：计算方差→滑动平均→锁定最优区间→提升精度
    3. 每轮迭代后，搜索区间缩小，精度提高一个数量级
    4. 将计算得到的periodogram保存到HDF5文件

使用方法：
    1. 独立运行：python lightcurve_period.py
       - 自动从配置文件读取参数
    2. 模块导入：from lightcurve_period import period_culculator
       - 直接调用函数：period_culculator()

注意事项：
    - 确保配置文件中设置了正确的参数值
    - 可通过修改配置文件调整搜索范围和精度

依赖包：
    - numpy: 用于高效数值计算和数组操作
    - config_manager: 用于读取配置文件
    - hdf5_manager: 用于HDF5文件操作
'''

import numpy as np
from config_manager import ConfigManager
from hdf5_manager import HDF5Manager
import h5py
from datetime import datetime

def calculate_variance(time, flux, period):
    """计算指定周期的差值方差
    
    功能：计算给定周期下，折叠后通量序列的差值方差
    输入：time（时间数组）、flux（通量数组）、period（当前周期）
    输出：方差值（float）
    """
    time_folded = np.mod(time, period)  # 时间折叠
    index = np.argsort(time_folded)
    sorted_flux = flux[index]
    return np.var(np.diff(sorted_flux))  # 方差越小，周期越优

def sliding_average(arr, window_size):
    """对输入数组做滑动平均
    
    功能：对输入数组做滑动平均，减少噪声干扰
    输入：arr（待平滑数组，如var）、window_size（窗口大小）
    输出：平滑后的数组（var_average）
    """
    if window_size < 1:
        raise ValueError("窗口大小必须大于等于1")
    
    result = np.zeros_like(arr, dtype=float)
    n = len(arr)
    
    for i in range(n):
        end_idx = min(i + window_size, n)
        result[i] = np.mean(arr[i:end_idx])
    
    return result

def period_culculator():
    """计算最佳周期
    
    功能：基于多轮迭代搜索算法计算光变曲线的最佳周期
    从配置文件读取参数，从HDF5文件读取预处理数据，将periodogram保存到HDF5文件
    
    返回:
        best_period: 最佳周期值
        final_precision: 最终精度
    """
    print("---最佳周期计算部分---")
    
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 从配置文件读取参数
    try:
        # 读取搜索范围参数
        start = config_manager.get('processing.period.start', 2.0)
        end = config_manager.get('processing.period.end', 3.0)
        
        # 读取迭代和精度参数
        max_iterations = config_manager.get('processing.period.max_iterations', 5)
        initial_precision = config_manager.get('processing.period.initial_precision', 2)
        
        # 参数验证
        if end <= start:
            raise ValueError("终止值必须大于起始值")
        if max_iterations < 1:
            raise ValueError("最大迭代次数必须大于等于1")
        if initial_precision < 0:
            raise ValueError("初始精度必须大于等于0")
        
        print(f"从配置文件读取参数成功:")
        print(f"搜索范围: [{start}, {end}]")
        print(f"最大迭代次数: {max_iterations}")
        print(f"初始精度数量级: {initial_precision}")
        print(f"注意：使用动态窗口大小计算，范围在5-20之间，基于周期候选数量自适应调整")
        
    except Exception as e:
        print(f"读取或验证配置参数失败: {e}")
        raise
    
    # 从HDF5文件读取预处理数据
    try:
        hdf5_path = config_manager.get('data.hdf5_path')
        hdf5_manager = HDF5Manager(hdf5_path)
        
        # 获取目标名称和文件名
        target_name = config_manager.get('data.hdf5_targets.default_target', 'HATP7b')
        file_name = config_manager.get('data.hdf5_targets.default_file', 'processed_combined')
        
        # 读取预处理数据
        time, flux = hdf5_manager.get_preprocessed_data(target_name, file_name)
        
        if time is None or flux is None:
            print(f"未找到预处理数据，尝试创建数据结构")
            # 尝试创建结构
            hdf5_manager.create_file_structure(target_name, file_name)
            
            # 尝试从data_processing导入get_sorted_data获取数据
            from data_processing import get_sorted_data
            time, flux = get_sorted_data()
            
            if time is None or flux is None:
                raise ValueError("无法获取有效的预处理数据")
        
        print(f"成功获取数据：{len(time)}个时间点，{len(flux)}个通量数据点")
        
    except Exception as e:
        print(f"获取数据失败：{e}")
        raise
    
    # 初始化变量
    current_start = start
    current_end = end
    current_precision = 10 ** (-initial_precision)
    best_period = None
    
    # 存储最终周期图数据
    final_periods = None
    final_var_average = None
    
    print(f"\n开始多轮迭代搜索（共{max_iterations}轮）...")
    
    # 阶段2：多轮迭代搜索（核心逻辑）
    for iteration in range(max_iterations):
        print(f"\n===== 第{iteration + 1}轮迭代 =====")
        print(f"搜索区间: [{current_start:.6f}, {current_end:.6f}]，精度: {current_precision:.6f}")
        
        # 步骤2.1：生成当前区间的周期序列
        periods = np.arange(current_start, current_end + current_precision, current_precision)
        print(f"生成周期序列，共{len(periods)}个候选周期")
        
        # 步骤2.2：计算每个周期的"折叠后通量差值方差"
        var = np.zeros_like(periods, dtype=float)
        for i, p in enumerate(periods):
            var[i] = calculate_variance(time, flux, p)
        
        # 步骤2.3：动态计算滑动窗口大小
        # 基于周期候选数量的10%，范围控制在5-20之间
        window_size = max(5, min(20, int(len(periods) * 0.1)))
        print(f"  动态计算的滑动窗口大小: {window_size}")
        
        # 步骤2.4：滑动平均平滑方差序列
        var_average = sliding_average(var, window_size)
        
        # 步骤2.5：锁定当前最优周期及下一轮区间
        min_idx = np.argmin(var_average)
        best_period = periods[min_idx]
        
        # 保存最后一轮的周期和方差数据作为最终周期图
        if iteration == max_iterations - 1:
            final_periods = periods
            final_var_average = var_average
        
        # 计算下一轮搜索区间
        interval_length = current_precision * 9
        current_start = best_period - interval_length / 2
        current_end = best_period + interval_length / 2
        
        print(f"本轮最优周期: {best_period:.6f}，方差值: {var[min_idx]:.6f}")
        print(f"下一轮搜索区间: [{current_start:.6f}, {current_end:.6f}]")
        
        # 步骤2.5：提升精度，进入下一轮迭代
        current_precision = current_precision / 10
    
    # 阶段3：输出结果
    final_precision = current_precision
    print(f"\n===== 搜索完成 =====")
    print(f"最佳周期: {best_period:.10f}")
    print(f"最终精度: {final_precision:.10f}")
    
    # 保存periodogram到HDF5文件
    try:
        # 创建periodogram数据结构（周期 + 方差）
        periodogram = np.column_stack((final_periods, final_var_average))
        
        # 确保HDF5文件结构存在
        hdf5_manager.create_file_structure(target_name, file_name)
        
        # 直接存储到HDF5文件，使用更简单的方式
        with h5py.File(hdf5_path, 'a') as f:
            # 确保处理数据组存在
            processed_path = f'{target_name}/{file_name}/processed'
            if processed_path not in f:
                f.create_group(processed_path)
            
            # 存储原始通量数据作为denoised_flux
            if 'denoised_flux' in f[processed_path]:
                del f[processed_path]['denoised_flux']
            f[processed_path].create_dataset(
                'denoised_flux',
                data=flux,
                compression='gzip'
            )
            
            # 存储周期图数据
            if 'periodogram' in f[processed_path]:
                del f[processed_path]['periodogram']
            period_ds = f[processed_path].create_dataset(
                'periodogram',
                data=periodogram,
                compression='gzip'
            )
            period_ds.attrs['description'] = '周期分析结果'
            period_ds.attrs['best_period'] = best_period
            period_ds.attrs['calculation_time'] = datetime.now().isoformat()
        
        print(f"周期图数据成功保存到HDF5文件: {hdf5_path}")
        print(f"目标组: {target_name}, 文件组: {file_name}")
        
    except Exception as e:
        print(f"保存periodogram失败: {e}")
        import traceback
        traceback.print_exc()
    
    return best_period, final_precision

# 如果作为主程序运行
if __name__ == "__main__":
    try:
        best_period, final_precision = period_culculator()
        print(f"\n计算完成！最佳周期为：{best_period:.10f}")
    except Exception as e:
        print(f"程序运行出错：{e}")
        import traceback
        traceback.print_exc()


    


        
