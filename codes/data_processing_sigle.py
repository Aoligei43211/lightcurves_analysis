# 导入必要的库
import os
import numpy as np
import logging
from astropy.io import fits

# 导入自定义模块
from config_manager import ConfigManager
from hdf5_manager import HDF5Manager

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def main():
    """
    主函数，负责初始化配置管理器和调用数据处理函数。
    
    此函数执行以下步骤：
    1. 初始化配置管理器
    2. 获取HDF5相关配置
    3. 调用数据处理函数
    """
    # 初始化配置管理器
    config_manager = ConfigManager()
    
    # 从配置管理器获取HDF5文件路径和目标配置
    hdf5_path = config_manager.get('data.hdf5_path')
    hdf5_target = config_manager.get('data.hdf5_target')
    if hdf5_target is None:
        hdf5_target = 'processed_data'
    
    print(f"HDF5文件路径: {hdf5_path}")
    print(f"HDF5目标组: {hdf5_target}")

    # 获取排序后的时间和通量数据并存储到HDF5文件的函数
    # 此函数会处理数据并提供交互式降噪选项，然后将数据存储到HDF5文件
    def get_sorted_data():
        """
        获取单个FITS文件中排序后的时间和通量数据并存储到HDF5文件。
        
        此函数执行以下步骤：
        1. 从配置获取单个FITS文件路径
        2. 验证文件存在性
        3. 读取文件数据
        4. 移除空值和NaN值
        5. 按时间排序
        6. 存储到HDF5文件
        """
        # 从配置获取单个FITS文件路径
        fits_file_path = config_manager.get('data.fits_files.single_file_path')
        
        # 检查文件是否存在
        if not os.path.exists(fits_file_path):
            print(f"错误: 文件 {fits_file_path} 不存在")
            return
        
        # 获取文件名（不含扩展名）用于HDF5子文件组名称
        file_name = os.path.splitext(os.path.basename(fits_file_path))[0]
        print(f"处理文件: {os.path.basename(fits_file_path)}")
        
        # 读取FITS文件数据
        try:
            with fits.open(fits_file_path) as hdul:
                # 假设数据在第一个扩展中，并且列名为'TIME'和'PDCSAP_FLUX'
                time_data = hdul[1].data['TIME']
                flux_data = hdul[1].data['PDCSAP_FLUX']
        except Exception as e:
            print(f"读取FITS文件时出错: {e}")
            return
        
        # 移除空值和NaN值
        valid_mask = ~(np.isnan(time_data) | np.isnan(flux_data))
        time_data = time_data[valid_mask]
        flux_data = flux_data[valid_mask]
        
        # 按时间排序
        sorted_indices = np.argsort(time_data)
        time_data_sorted = time_data[sorted_indices]
        flux_data_sorted = flux_data[sorted_indices]
        
        # 初始化HDF5管理器并存储数据
        try:
            # 初始化HDF5管理器
            hdf5_manager = HDF5Manager(hdf5_path)
            
            # 创建子文件组结构
            hdf5_manager.create_file_structure(hdf5_target, file_name)
            
            # 存储排序后的数据到HDF5文件
            hdf5_manager.store_preprocessed_data(hdf5_target, file_name, time_data_sorted, flux_data_sorted)
            
            print(f"数据已成功存储到HDF5文件，子文件组: {file_name}")
            
        except Exception as e:
            print(f"存储数据到HDF5文件时出错: {e}")
            return
    
    # 执行数据处理
    get_sorted_data()


if __name__ == "__main__":
    main()
    

  
