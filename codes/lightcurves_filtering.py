
'''天文光变曲线多卷积核降噪对比工具

功能说明：
    1. 支持用户交互式输入多个卷积核大小和sigma参数
    2. 从HDF5文件读取原始数据并应用高斯卷积降噪
    3. 将降噪后的数据存储到原始数据组的denoised_flux中
    4. 提供默认卷积核大小和sigma设置，增强用户体验

实现原理：
    - 从HDF5文件读取预处理数据
    - 通过noise_reduction函数对同一数据集应用不同窗口大小和sigma的高斯卷积降噪
    - 将降噪后的flux数据存储回原始数据组的processed路径下的denoised_flux数据集中

使用方法：
    运行脚本后，按照提示输入卷积核大小(window_size)和sigma值，按回车键确认
    可输入多个卷积核配置，输入空值结束
    如果不输入任何值，程序将自动使用默认值(window_size=5, sigma=1.0)

依赖包：
    - numpy: 用于数值计算
    - hdf5_manager: 自定义模块，提供HDF5文件操作
    - config_manager: 自定义模块，提供配置管理功能

注意事项：
    - 卷积核大小(window_size)和sigma值越大，降噪效果越强，但可能会丢失细节信息
    - sigma控制高斯函数的展宽程度，sigma越大，平滑效果越强
'''

import numpy as np
import h5py
from hdf5_manager import HDF5Manager
from config_manager import ConfigManager

# 初始化配置管理器和HDF5管理器
config_manager = ConfigManager()
hdf5_path = config_manager.get('data.hdf5_path')
hdf5_manager = HDF5Manager(hdf5_path)

# 获取目标名称和文件名
# 从配置文件读取默认目标和文件
TARGET_NAME = config_manager.get('data.hdf5_targets.default_target')
FILE_NAME = config_manager.get('data.hdf5_targets.default_file')

# 从HDF5文件读取预处理数据
print(f"从HDF5文件读取数据: {hdf5_path}")
print(f"目标组: {TARGET_NAME}, 文件组: {FILE_NAME}")
time_data, flux_data = hdf5_manager.get_preprocessed_data(TARGET_NAME, FILE_NAME)

if time_data is None or flux_data is None:
    print("无法从HDF5文件获取数据，程序退出")
    print(f"请确保 {TARGET_NAME}/{FILE_NAME}/preprocessed 路径下存在 time 和 flux 数据集")
    exit()

print(f"成功获取数据：时间点数量 = {len(time_data)}, 通量数据数量 = {len(flux_data)}")

#降噪处理，使用高斯卷积进行降噪处理
def noise_reduction(flux, window_size, sigma):
    """
    使用高斯卷积进行降噪处理
    :param flux: 输入的光通量数据
    :param window_size: 高斯窗口大小
    :param sigma: 高斯函数的标准差
    :return: 降噪后的光通量数据
    """
    if window_size <= 0 or not isinstance(window_size, int):
        raise ValueError("window_size必须为大于0的整数")
    if sigma <= 0:
        raise ValueError("sigma必须为大于0的数")
    if len(flux) < window_size:
        return flux.copy()  # 如果数据点不足，直接返回原数据
    
    # 创建高斯卷积核
    x = np.arange(window_size) - window_size // 2  # 生成从-(window_size//2)到(window_size//2)的数组
    gaussian_kernel = np.exp(-x**2 / (2 * sigma**2))
    gaussian_kernel = gaussian_kernel / np.sum(gaussian_kernel)  # 归一化卷积核
    
    # 使用高斯卷积进行平滑处理
    return np.convolve(flux, gaussian_kernel, mode='same')

def get_convolution_configs(config_manager):
    """
    从配置文件或用户输入获取卷积核配置列表
    
    参数:
        config_manager: 配置管理器实例
    
    返回:
        list: [(window_size1, sigma1), (window_size2, sigma2), ...]
    """
    # 尝试从配置文件读取卷积核配置
    try:
        # 从配置文件读取默认卷积核配置
        default_configs = config_manager.get('processing.noise_reduction.convolution_configs')
        convolution_configs = []
        
        # 检查配置是否有效
        if default_configs and isinstance(default_configs, list):
            for config in default_configs:
                if isinstance(config, dict) and 'window_size' in config and 'sigma' in config:
                    window_size = config['window_size']
                    sigma = config['sigma']
                    if window_size > 0 and sigma > 0:
                        convolution_configs.append((window_size, sigma))
        
        # 如果配置文件中有有效的配置，使用这些配置
        if convolution_configs:
            print("\n从配置文件读取到以下卷积核配置:")
            for i, (window_size, sigma) in enumerate(convolution_configs):
                print(f"  {i+1}. window_size={window_size}, sigma={sigma}")
            
            # 询问用户是否使用这些配置，如果使用
            use_config = input("\n是否使用这些配置？(y/n): ").strip().lower()
            if use_config == 'y':
                return convolution_configs
    except Exception as e:
        print(f"从配置文件读取卷积核配置时出错: {e}")
    
    # 如果配置文件中没有有效配置或用户选择不使用，询问用户输入
    convolution_configs = []
    print("\n请输入卷积核大小(window_size)和sigma参数，每行输入一对，按回车确认")
    print("例如: 5 1.0")
    print("输入空行结束输入")
    
    while True:
        try:
            # 获取用户输入
            line = input("请输入 window_size sigma: ").strip()
            if not line:
                break
            
            # 解析输入
            parts = line.split()
            if len(parts) != 2:
                raise ValueError("输入格式错误，请输入两个数值，用空格分隔")
            
            window_size = int(parts[0])
            sigma = float(parts[1])
            
            # 验证参数有效性
            if window_size < 1 or sigma <= 0:
                raise ValueError("window_size必须大于0，sigma必须大于0")
            
            convolution_configs.append((window_size, sigma))
        except ValueError as e:
            print(f"输入错误: {e}，请重新输入")
    
    # 如果没有输入，使用默认值
    if not convolution_configs:
        print("未输入任何配置，使用默认值: window_size=5, sigma=1.0")
        convolution_configs = [(5, 1.0)]
    
    return convolution_configs

# 获取卷积核配置
convolution_configs = get_convolution_configs(config_manager)

# # 限制最大显示3个图像
# convolution_configs = convolution_configs[:3]

# 对每个卷积核配置处理并存储数据
for i, (window_size, sigma) in enumerate(convolution_configs):
    # 应用降噪处理
    print(f"\n应用降噪处理: 窗口大小={window_size}, sigma={sigma}")
    flux_denoised = noise_reduction(flux_data.copy(), window_size, sigma)
    
    # 由于降噪只改变flux数值，时间数据保持不变
    # 我们需要一个假的periodogram数据来满足store_processed_data方法的参数要求
    # 创建一个简单的空periodogram数据（2D数组）
    periodogram = np.array([[0.0, 0.0]])  # 简单的空periodogram
    
    try:
        # 使用hdf5_manager的store_processed_data方法存储降噪后的数据
        # 这会将denoised_flux存储到 TARGET_NAME/FILE_NAME/processed 路径下
        hdf5_manager.store_processed_data(
            target_name=TARGET_NAME,
            file_name=FILE_NAME,
            denoised_flux=flux_denoised,
            periodogram=periodogram
        )
        
        # 记录处理参数到denoised_flux数据集的属性中
        with h5py.File(hdf5_path, 'a') as f:
            processed_group = f[f'{TARGET_NAME}/{FILE_NAME}/processed']
            if 'denoised_flux' in processed_group:
                denoised_ds = processed_group['denoised_flux']
                denoised_ds.attrs['processing_method'] = 'gaussian_convolution'
                denoised_ds.attrs['window_size'] = window_size
                denoised_ds.attrs['sigma'] = sigma
                denoised_ds.attrs['processing_date'] = np.bytes_(np.datetime64('now').astype(str).encode('utf-8'))
        
        print(f"成功存储降噪后的数据到: {TARGET_NAME}/{FILE_NAME}/processed/denoised_flux")
        print(f"处理参数: 窗口大小={window_size}, sigma={sigma}")
    except Exception as e:
        print(f"存储降噪数据时出错: {e}")

print("\n所有降噪处理完成，数据已存储到HDF5文件中的相应路径")
