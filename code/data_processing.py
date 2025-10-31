"""
天文观测数据处理模块

该模块提供了处理天文观测FITS文件数据的功能，包括：
- 读取多个FITS文件
- 处理时间序列和通量数据
- 移除大间隙
- 降噪处理
- 数据拼接和排序

使用方法：
    get_sorted_data()  # 调用函数获取处理后的数据

返回值：
    time_sorted, flux_sorted: 排序后的时间数组和通量数组
"""
import numpy as np
import os
from astropy.io import fits
import glob

def remove_large_gaps(time, flux, max_gap_days=0.5):
    """
    移除时间序列中的大间隙
    
    参数：
        time: 时间数组
        flux: 通量数组
        max_gap_days: 最大允许间隙（天）
    
    返回：
        处理后的时间和通量数组
    """
    # 计算时间差
    time_diff = np.diff(time)
    
    # 找到大于最大间隙的索引
    gap_indices = np.where(time_diff > max_gap_days)[0] + 1
    
    # 如果有大间隙，返回第一个间隙前的数据
    if len(gap_indices) > 0:
        return time[:gap_indices[0]], flux[:gap_indices[0]]
    
    return time, flux

def get_sorted_data():
    """
    读取并处理FITS文件中的数据
    
    返回：
        time_sorted: 排序后的时间数组
        flux_sorted: 排序后的通量数组
    """
    # 设置FITS文件路径
    folder = r'D:\program\Python\projects\astronomy\data\HATP7b'
    
    # 获取所有FITS文件
    fits_files = glob.glob(os.path.join(folder, '*.fits'))
    
    # 存储处理后的数据
    all_time = []
    all_flux = []
    
    # 处理每个文件
    for file in fits_files:
        try:
            # 打开FITS文件
            with fits.open(file) as hdul:
                # 读取数据
                data = hdul[1].data
                
                # 提取时间和通量数据
                time = data['TIME']
                flux = data['PDCSAP_FLUX']
                
                # 移除NaN值
                valid_mask = ~np.isnan(time) & ~np.isnan(flux)
                time = time[valid_mask]
                flux = flux[valid_mask]
                
                # 移除大间隙
                time, flux = remove_large_gaps(time, flux)
                
                # 添加到总数据
                all_time.append(time)
                all_flux.append(flux)
                
                print(f"成功处理文件: {file}")
                
        except Exception as e:
            print(f"处理文件 {file} 时出错: {e}")
    
    # 合并所有数据
    if all_time and all_flux:
        # 合并时间和通量数组
        merged_time = np.concatenate(all_time)
        merged_flux = np.concatenate(all_flux)
        
        # 按时间排序
        sort_indices = np.argsort(merged_time)
        time_sorted = merged_time[sort_indices]
        flux_sorted = merged_flux[sort_indices]
        
        # 交互式去除空白
        print(f"\n共处理 {len(fits_files)} 个文件")
        print(f"总数据点数量: {len(time_sorted)}")
        
        # 询问是否进行降噪处理
       降噪选择 = input("是否进行降噪处理？(y/n): ")
        if 降噪选择.lower() == 'y':
            window_size = int(input("请输入降噪窗口大小 (默认10): ") or "10")
            flux_sorted = noise_reduction(flux_sorted, window_size)
        
        return time_sorted, flux_sorted
    else:
        print("未找到有效数据")
        return None, None

def noise_reduction(flux, window_size=10):
    """
    使用移动平均法进行降噪
    
    参数：
        flux: 通量数组
        window_size: 移动窗口大小
    
    返回：
        降噪后的通量数组
    """
    # 使用numpy的卷积函数实现移动平均
    window = np.ones(window_size) / window_size
    flux_smoothed = np.convolve(flux, window, mode='same')
    
    return flux_smoothed

def flux_correction(flux, median_filter_size=50):
    """
    对通量数据进行校正
    
    参数：
        flux: 通量数组
        median_filter_size: 中值滤波窗口大小
    
    返回：
        校正后的通量数组
    """
    # 计算全局中值
    flux_median = np.median(flux)
    
    # 返回归一化的通量
    return flux / flux_median

if __name__ == "__main__":
    time, flux = get_sorted_data()
    if time is not None and flux is not None:
        print(f"处理完成，数据点数量: {len(time)}")
