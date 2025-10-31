"""
天文光变曲线周期分析工具

该模块提供了计算天文光变曲线最佳周期的功能，使用多轮迭代搜索算法：
- 通过方差分析计算最佳周期
- 支持交互式参数输入
- 使用滑动窗口平均优化周期搜索
- 多轮迭代提升搜索精度

使用方法：
    period_culculator(time, flux)  # 调用函数计算最佳周期

参数：
    time: 时间数组
    flux: 通量数组
    max_iterations: 最大迭代次数（默认5）
    window_size: 滑动窗口大小（默认5）

返回值：
    best_period: 计算得到的最佳周期
"""
import numpy as np
import matplotlib.pyplot as plt
import time


def calculate_variance(time, flux, period):
    """
    计算指定周期下的差值方差
    
    参数：
        time: 时间数组
        flux: 通量数组
        period: 候选周期
    
    返回：
        variance: 差值方差
    """
    # 将时间序列折叠到一个周期内
    phase = (time % period) / period
    
    # 按相位排序
    sorted_indices = np.argsort(phase)
    phase_sorted = phase[sorted_indices]
    flux_sorted = flux[sorted_indices]
    
    # 计算相邻点的差值方差
    diffs = np.diff(flux_sorted)
    variance = np.sum(diffs ** 2) / len(diffs)
    
    return variance


def sliding_average(data, window_size):
    """
    对数据进行滑动平均平滑
    
    参数：
        data: 输入数据数组
        window_size: 滑动窗口大小
    
    返回：
        smoothed_data: 平滑后的数据数组
    """
    # 创建滑动窗口
    window = np.ones(window_size) / window_size
    
    # 使用卷积进行滑动平均
    smoothed_data = np.convolve(data, window, mode='same')
    
    return smoothed_data


def period_culculator(time, flux, max_iterations=5, window_size=5):
    """
    计算光变曲线的最佳周期
    使用多轮迭代搜索算法：
    1. 初始化与参数准备
    2. 多轮迭代搜索
    3. 输出结果
    
    参数：
        time: 时间数组
        flux: 通量数组
        max_iterations: 最大迭代次数
        window_size: 滑动窗口大小
    
    返回：
        best_period: 最佳周期
    """
    # 1. 初始化与参数准备
    print("开始周期计算...")
    start_time = time.time()
    
    # 参数验证
    if not isinstance(time, np.ndarray) or not isinstance(flux, np.ndarray):
        raise TypeError("输入数据必须是numpy数组")
    
    if len(time) != len(flux):
        raise ValueError("时间和通量数组长度必须相同")
    
    if max_iterations < 1:
        raise ValueError("最大迭代次数必须大于0")
    
    if window_size < 1:
        raise ValueError("窗口大小必须大于0")
    
    # 获取用户输入的初始周期范围和精度
    try:
        period_min = float(input("请输入周期最小值 (默认1.0): ") or "1.0")
        period_max = float(input("请输入周期最大值 (默认20.0): ") or "20.0")
        initial_precision = float(input("请输入初始精度 (默认0.01): ") or "0.01")
    except ValueError:
        print("输入错误，使用默认参数")
        period_min = 1.0
        period_max = 20.0
        initial_precision = 0.01
    
    # 边界检查
    if period_min >= period_max:
        print("周期范围无效，使用默认范围")
        period_min = 1.0
        period_max = 20.0
    
    # 2. 多轮迭代搜索
    current_min = period_min
    current_max = period_max
    current_precision = initial_precision
    
    best_period = None
    best_variance = float('inf')
    
    for iteration in range(max_iterations):
        print(f"\n迭代轮次 {iteration + 1}/{max_iterations}")
        print(f"搜索范围: [{current_min:.6f}, {current_max:.6f}], 精度: {current_precision:.6f}")
        
        # 生成周期序列
        periods = np.arange(current_min, current_max + current_precision, current_precision)
        
        # 计算每个周期的方差
        variances = []
        for i, period in enumerate(periods):
            variance = calculate_variance(time, flux, period)
            variances.append(variance)
            
            # 显示进度
            if (i + 1) % 100 == 0 or i + 1 == len(periods):
                print(f"进度: {i + 1}/{len(periods)}, 当前周期: {period:.6f}")
        
        variances = np.array(variances)
        
        # 滑动平均平滑方差序列
        smoothed_variances = sliding_average(variances, window_size)
        
        # 找到最小方差对应的周期
        min_index = np.argmin(smoothed_variances)
        current_best_period = periods[min_index]
        current_best_variance = smoothed_variances[min_index]
        
        print(f"本轮最佳周期: {current_best_period:.6f}, 方差: {current_best_variance:.6f}")
        
        # 更新全局最佳周期
        if current_best_variance < best_variance:
            best_period = current_best_period
            best_variance = current_best_variance
        
        # 缩小搜索范围，提升精度
        # 设置新的搜索范围为当前最佳周期的±10%，但不超过原范围
        range_factor = 0.1
        new_min = max(current_min, current_best_period * (1 - range_factor))
        new_max = min(current_max, current_best_period * (1 + range_factor))
        
        # 提升精度（每次迭代精度提高10倍）
        new_precision = current_precision / 10
        
        # 更新搜索参数
        current_min, current_max, current_precision = new_min, new_max, new_precision
    
    # 3. 输出结果
    end_time = time.time()
    
    print("\n周期计算完成！")
    print(f"最佳周期: {best_period:.8f}")
    print(f"最小方差: {best_variance:.8f}")
    print(f"计算耗时: {end_time - start_time:.2f} 秒")
    
    return best_period


if __name__ == "__main__":
    try:
        # 示例调用（实际使用时应替换为真实数据）
        # 这里仅作为演示
        print("欢迎使用光变曲线周期计算器")
        print("请确保已导入数据处理模块")
        
        # 实际使用时，应该从data_processing模块获取数据
        # from data_processing_sigle import get_sorted_data
        # time, flux = get_sorted_data()
        # if time is not None and flux is not None:
        #     best_period = period_culculator(time, flux)
        
    except Exception as e:
        print(f"运行出错: {e}")
