'''天文观测数据处理模块

功能说明：
    1. 读取FITS文件中的天文观测数据
    2. 处理数据（时间排序等）
    3. 提供数据访问接口给其他模块

实现过程：
    - 扫描指定文件夹下的所有FITS文件
    - 提取每个文件中的时间和通量数据
    - 合并并排序数据
    
使用方法：
    - 调用get_sorted_data()函数获取处理后的数据
    
依赖包：
    - numpy: 用于数值计算
    - os: 用于文件和目录操作
    - glob: 用于文件路径模式匹配
    - astropy.io.fits: 用于读取FITS文件

参数说明：
    - folder: 存放FITS文件的文件夹路径
    - get_sorted_data()函数返回处理后的时间和通量数据数组

注意事项：
    - get_sorted_data()函数自动处理数据，不再进行空白区域移除
'''

import numpy as np  # 导入NumPy库，用于数值计算
import os  # 导入os库，用于文件和目录操作
from glob import glob  # 导入glob函数，用于文件路径模式匹配
from astropy.io import fits  # 导入astropy.io的fits模块，用于读取FITS文件
from config_manager import ConfigManager
from hdf5_manager import HDF5Manager

# 初始化配置管理器
config_manager = ConfigManager()

# 从配置管理器获取文件夹路径
folder = config_manager.get('data.hatp7b_path')

# 从配置管理器获取HDF5文件路径和目标配置
hdf5_target = config_manager.get('data.hdf5_targets.default_target')
hdf5_file_name = config_manager.get('data.hdf5_targets.default_file')

# 获取排序后的时间和通量数据的函数
# 此函数会处理数据但不再移除大片空白
# 返回值：处理后的时间和通量数据
def get_sorted_data():
    valid_files=[]
    # 递归查找目录及其子目录下所有 .fits 文件
    import glob2
    fits_files = glob2.glob(os.path.join(folder, '**', '*.fits'))  # 获取所有子目录中.fits文件的路径列表
    print(f"找到 {len(fits_files)} 个FITS文件")  # 打印找到的FITS文件数量

    #数据提取
    time_all_global=np.empty(0,float) #初始化数组time_all
    flux_all_global=np.empty(0,float)#np.empty()方法创建一个空数组，不分配内存，用于后续拼接
    for file_path in fits_files:  # 遍历每个FITS文件
        try:
            with fits.open(file_path) as hdul:  # 打开FITS文件,读取出HDUList对象
                data = hdul[1].data  # 获取第1个HDU(索引从0开始),读取数据
                time = data['TIME']  # 获取时间列数据，返回一个NumPy数组
                flux = data['PDCSAP_FLUX']  # 获取亮度列数据，返回一个NumPy数组
                
                # 数据清洗：移除NaN值
                valid_mask = ~np.isnan(time) & ~np.isnan(flux)  # 创建一个布尔掩码,用于筛选出有效数据(时间和亮度都不是NaN)，是NaN的话Np.isnan()返回True,经~取反操作后为False

                #移除空值
                if len(time)==0 or len(flux)== 0:
                    continue
                
                # 只拼接有效数据点，确保time_all_global和flux_fixed_all长度匹配
                time_valid = time[valid_mask]
                flux_valid = flux[valid_mask]
                
                #将各个文件的有效数据拼接起来
                time_all_global=np.concatenate([time_all_global,time_valid])
                flux_all_global=np.concatenate([flux_all_global,flux_valid])
                valid_files.append(file_path)
        except Exception as e:  # 捕获并处理可能发生的异常
            print(f"处理文件 {file_path} 时出错: {str(e)}")  # 打印错误信息

    if len(valid_files) == 0:
        print("未找到任何有效FITS文件")
        return None, None

    #时间排序
    tist=np.argsort(time_all_global)#排序后的时间序列的索引

    #调用校正函数，生成校正后的全局光通量
    flux_fixed_all = flux_correction(valid_files)
    #全局时间排序
    time_sorted = time_all_global[tist]
    flux_sorted = flux_fixed_all[tist]
    
    # HDF5 storage for preprocessed data
    hdf5_path = config_manager.get('data.hdf5_path')
    hdf5_manager = HDF5Manager(hdf5_path)
    
    # 确保HDF5文件结构存在
    hdf5_manager.create_file_structure(hdf5_target, hdf5_file_name)
    
    # 存储预处理数据到综合组
    storage_status = hdf5_manager.store_preprocessed_data(
        hdf5_target, 
        hdf5_file_name,
        time_sorted, 
        flux_sorted
    )
    
    if storage_status:
        print(f"预处理数据已成功存储到HDF5文件: {hdf5_path}")
        print(f"目标组: {hdf5_target}, 文件名: {hdf5_file_name}")
    else:
        print("数据存储失败")
    
    # 不再执行自动移除大片空白的操作
    
    return time_sorted, flux_sorted

#调整各个文件的flux值，使之大体持平，并应用3σ法则去除异常值
def flux_correction(m):#使用形参来统一遍历对象
    store=[]#初始化存储各个文件的中位数的数组，
    for file_path in m:  # 遍历每个FITS文件
        try:
            with fits.open(file_path) as hdul:
                data = hdul[1].data  
                flux = data['PDCSAP_FLUX']  
            valid_mask = ~np.isnan(flux)  
            flux =flux[valid_mask]  
            flux_m=np.median(flux)#求取这个文件的flux的中位值
            store.append(flux_m)#存储中位值
        except Exception as e:  # 捕获并处理可能发生的异常。sort
            print(f"处理文件 {file_path} 时出错: {str(e)}")  # 打印错误信息

    #计算整体flxu中位值
    flux_median_global=np.mean(store)#计算所有文件的flux的中位值的平均值，作为整体的flux的中位值
    flux_fixed_all=np.empty(0,float)#0表示初始数组为空，float表示数组元素类型为浮点数
    #调整点的竖轴位置
    for i,file_path in enumerate(m):  # 遍历每个FITS文件，i表示文件索引，file_path表示i对应的文件路径
        try:
            with fits.open(file_path) as hdul:
                data = hdul[1].data  
                flux = data['PDCSAP_FLUX']  
            valid_mask = ~np.isnan(flux)  
            flux = flux[valid_mask]  

            #核心调整步骤
            flux_fixed=flux-(store[i]-flux_median_global)
            
            # 应用3σ法则去除异常值
            mu = np.mean(flux_fixed)
            sigma = np.std(flux_fixed)
            lower_bound = mu - 3 * sigma
            upper_bound = mu + 3 * sigma
            outlier_mask = (flux_fixed >= lower_bound) & (flux_fixed <= upper_bound)
            
            # 过滤异常值
            flux_fixed_filtered = flux_fixed[outlier_mask]
            
            # 记录去除的异常值数量
            num_outliers = len(flux_fixed) - len(flux_fixed_filtered)
            if num_outliers > 0:
                print(f"从文件 {os.path.basename(file_path)} 中去除了 {num_outliers} 个异常值")
            
            flux_fixed_all=np.concatenate([flux_fixed_all, flux_fixed_filtered])#将所有文件的过滤后的flux_fixed拼接起来
                
        except Exception as e:  # 捕获并处理可能发生的异常
            print(f"处理文件 {file_path} 时出错: {str(e)}")  # 打印错误信息
            # 提供更健壮的异常处理
            if i < len(store):  # 确保索引有效
                flux_fixed = flux - (store[i] - flux_median_global)
                flux_fixed_all = np.concatenate([flux_fixed_all, flux_fixed])
            else:
                # 如果store中没有对应索引的数据，使用flux_median_global
                flux_fixed_all = np.concatenate([flux_fixed_all, flux - flux_median_global])
    
    # 验证数据分布合理性
    if len(flux_fixed_all) > 0:
        mu_final = np.mean(flux_fixed_all)
        sigma_final = np.std(flux_fixed_all)
        print(f"应用3σ法则后的数据统计：平均值={mu_final:.6f}, 标准差={sigma_final:.6f}, 数据点数量={len(flux_fixed_all)}")
    
    return flux_fixed_all

if __name__ == "__main__":
    get_sorted_data()
    

  
