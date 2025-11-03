"""HDF5数据存储管理模块

功能说明：
    1. 实现HDF5数据存储标准，支持多层次组结构
    2. 管理星体大组、子文件组和综合组的存储
    3. 提供数据压缩、校验和完整性验证
    4. 支持分析结果的智能缓存和复用

实现过程：
    - 使用h5py库实现HDF5读写操作
    - 创建标准化的组结构：attributes、preprocessed、processed等
    - 实现数据压缩和MD5校验和
    - 提供统一的接口用于存储和检索数据

使用方法：
    - 初始化HDF5Manager指定HDF5文件路径
    - 使用store_*方法存储不同类型的数据
    - 使用get_*方法检索存储的数据

依赖包：
    - h5py: HDF5文件操作
    - numpy: 数值计算
    - hashlib: MD5校验和计算
    - os: 文件路径操作
    - logging_config: 结构化日志系统
"""

# 导入h5py库，用于操作HDF5文件
# h5py.File: 创建或打开HDF5文件
# h5py.Group: HDF5组对象，类似于文件系统目录
# h5py.Dataset: HDF5数据集对象，存储实际数据
import h5py
# 导入numpy库，用于数值计算和数组操作
# np.array: 创建numpy数组
# np.shape: 获取数组形状
# np.tobytes: 将数组转换为字节数据
import numpy as np
# 导入hashlib库，用于计算MD5校验和
# hashlib.md5: 创建MD5哈希对象
import hashlib
# 导入os模块，用于文件路径操作
# os.path: 路径操作函数集合
import os
# 导入datetime模块，用于获取当前时间
# datetime.now: 获取当前日期和时间
# .isoformat(): 将日期时间转换为ISO格式字符串
from datetime import datetime
# 从logging_config模块导入get_logger函数
# get_logger: 获取或创建指定名称的logger实例
from logging_config import get_logger


class HDF5Manager:
    """HDF5数据存储管理器 - 提供天文数据的HDF5格式存储和检索功能"""
    
    def __init__(self, hdf5_path):
        """
        初始化HDF5管理器 - 设置文件路径和版本信息
        
        参数:
            hdf5_path: HDF5文件路径，用于存储天文观测数据
        """
        # 存储HDF5文件路径
        self.hdf5_path = hdf5_path
        # 设置数据格式版本
        self.format_version = "1.0"
        # 获取指定名称的logger实例
        # get_logger: 创建或获取名为'hdf5_manager'的日志记录器
        self.logger = get_logger('hdf5_manager')
        # 记录初始化日志
        self.logger.info(f"初始化HDF5管理器，文件路径: {hdf5_path}")
    
    def create_structure(self, target_name):
        """
        为指定目标创建标准HDF5结构 - 创建目标星体的顶级组
        
        参数:
            target_name: 目标名称（如HATP7b），表示观测目标的标识符
        """
        # 记录创建结构的日志
        self.logger.info(f"为目标 {target_name} 创建HDF5结构")
        # 打开HDF5文件（追加模式）
        # h5py.File: 打开指定路径的HDF5文件，'a'表示可读写模式
        with h5py.File(self.hdf5_path, 'a') as f:
            # 检查目标组是否已存在
            if target_name not in f:
                # 创建目标组
                # h5py.File.create_group: 创建一个新的HDF5组
                target_group = f.create_group(target_name)
                # 设置组属性：格式版本
                # h5py.Group.attrs: 访问组的属性字典
                target_group.attrs['format_version'] = self.format_version
                # 设置组属性：创建日期
                target_group.attrs['created_date'] = datetime.now().isoformat()
                # 记录调试日志
                self.logger.debug(f"已创建目标组: {target_name}")
            else:
                # 记录调试日志
                self.logger.debug(f"目标组已存在: {target_name}")
    
    def create_file_structure(self, target_name, file_name):
        """
        为单个文件创建子文件组结构 - 创建包含attributes、preprocessed和processed子组的完整结构
        
        参数:
            target_name: 目标名称，如'HATP7b'
            file_name: 文件名称（不含扩展名），表示观测数据文件
        """
        # 记录创建子文件结构的日志
        self.logger.info(f"为文件 {file_name} 创建子文件组结构")
        # 打开HDF5文件（追加模式）
        with h5py.File(self.hdf5_path, 'a') as f:
            # 如果目标组不存在，先创建目标组
            if target_name not in f:
                self.create_structure(target_name)
            
            # 获取目标组引用
            target_group = f[target_name]
            # 检查文件组是否已存在
            if file_name not in target_group:
                # 创建文件组
                file_group = target_group.create_group(file_name)
                
                # 创建属性组 - 存储元数据信息
                attrs_group = file_group.create_group('attributes')
                # 设置属性组属性：源文件名
                attrs_group.attrs['source_file'] = f'{file_name}.fits'
                # 设置属性组属性：处理日期
                attrs_group.attrs['processing_date'] = datetime.now().isoformat()
                # 设置属性组属性：算法参数（初始为空字典）
                attrs_group.attrs['algorithm_params'] = '{}'
                
                # 创建预处理数据组 - 存储原始预处理数据
                preprocessed_group = file_group.create_group('preprocessed')
                # 设置预处理组描述属性
                preprocessed_group.attrs['description'] = '预处理后的时间序列数据'
                
                # 创建处理数据组 - 存储分析处理后的结果
                processed_group = file_group.create_group('processed')
                # 设置处理组描述属性
                processed_group.attrs['description'] = '处理后的数据和分析结果'
                
                # 记录调试日志
                self.logger.debug(f"已为文件 {file_name} 创建完整的HDF5结构")
            else:
                # 记录调试日志
                self.logger.debug(f"文件组已存在: {file_name}")
    
    def create_comprehensive_structure(self, target_name):
        """
        创建综合组结构 - 用于存储多个观测文件合并后的综合分析结果
        
        参数:
            target_name: 目标名称，如'HATP7b'
        """
        # 记录创建综合组的日志
        self.logger.info(f"为目标 {target_name} 创建综合组结构")
        # 打开HDF5文件（追加模式）
        with h5py.File(self.hdf5_path, 'a') as f:
            # 如果目标组不存在，先创建目标组
            if target_name not in f:
                self.create_structure(target_name)
            
            # 获取目标组引用
            target_group = f[target_name]
            # 检查综合组是否已存在
            if 'comprehensive' not in target_group:
                # 创建综合组
                comp_group = target_group.create_group('comprehensive')
                # 设置综合组描述属性
                comp_group.attrs['description'] = '综合分析和聚合数据'
                # 设置综合组创建日期属性
                comp_group.attrs['created_date'] = datetime.now().isoformat()
                # 记录调试日志
                self.logger.debug(f"已创建综合组: comprehensive")
            else:
                # 记录调试日志
                self.logger.debug(f"综合组已存在: comprehensive")
    
    def store_preprocessed_data(self, target_name, file_name, time_data, flux_data):
        """
        存储预处理数据 - 保存时间序列和光通量数据，使用gzip压缩并计算MD5校验和
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            time_data: 时间数据数组，存储观测时间序列
            flux_data: 通量数据数组，存储观测光通量序列
            
        返回:
            bool: 存储是否成功
        """
        try:
            # 确保文件结构存在
            self.create_file_structure(target_name, file_name)
            
            # 打开HDF5文件（追加模式）
            with h5py.File(self.hdf5_path, 'a') as f:
                # 获取文件组引用
                file_group = f[f'{target_name}/{file_name}']
                # 获取预处理组引用
                preprocessed_group = file_group['preprocessed']
                
                # 存储时间数据
                # 如果时间数据集已存在，先删除
                if 'time' in preprocessed_group:
                    del preprocessed_group['time']
                # 创建时间数据集，使用gzip压缩
                # h5py.Group.create_dataset: 创建新的数据集
                # compression='gzip': 使用gzip算法压缩数据
                time_ds = preprocessed_group.create_dataset(
                    'time', 
                    data=time_data,
                    compression='gzip'
                )
                # 设置时间数据单位属性
                time_ds.attrs['unit'] = 'days'
                # 设置时间数据描述属性
                time_ds.attrs['description'] = '观测时间序列'
                # 计算并存储时间数据的MD5校验和
                time_ds.attrs['md5_checksum'] = self._calculate_md5(time_data)
                
                # 存储通量数据
                # 如果通量数据集已存在，先删除
                if 'flux' in preprocessed_group:
                    del preprocessed_group['flux']
                # 创建通量数据集，使用gzip压缩
                flux_ds = preprocessed_group.create_dataset(
                    'flux',
                    data=flux_data,
                    compression='gzip'
                )
                # 设置通量数据单位属性
                flux_ds.attrs['unit'] = 'e-/s'
                # 设置通量数据标准化标志属性
                flux_ds.attrs['normalized'] = True
                # 设置通量数据描述属性
                flux_ds.attrs['description'] = '预处理后的光通量序列'
                # 计算并存储通量数据的MD5校验和
                flux_ds.attrs['md5_checksum'] = self._calculate_md5(flux_data)
            
            # 存储成功
            return True
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"存储预处理数据失败: {str(e)}")
            # 存储失败
            return False
    
    def store_processed_data(self, target_name, file_name, denoised_flux, periodogram):
        """
        存储处理后的数据 - 保存降噪后的通量数据和周期图数据
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            denoised_flux: 降噪后的通量数据数组
            periodogram: 周期图数据数组
        """
        # 确保文件结构存在
        self.create_file_structure(target_name, file_name)
        
        # 打开HDF5文件（追加模式）
        with h5py.File(self.hdf5_path, 'a') as f:
            # 获取文件组引用
            file_group = f[f'{target_name}/{file_name}']
            # 获取处理组引用
            processed_group = file_group['processed']
            
            # 存储降噪数据
            # 如果降噪数据集已存在，先删除
            if 'denoised_flux' in processed_group:
                del processed_group['denoised_flux']
            # 创建降噪数据集，使用gzip压缩
            denoised_ds = processed_group.create_dataset(
                'denoised_flux',
                data=denoised_flux,
                compression='gzip'
            )
            # 设置降噪数据描述属性
            denoised_ds.attrs['description'] = '降噪后的光通量序列'
            # 计算并存储降噪数据的MD5校验和
            denoised_ds.attrs['md5_checksum'] = self._calculate_md5(denoised_flux)
            
            # 存储周期图数据
            # 如果周期图数据集已存在，先删除
            if 'periodogram' in processed_group:
                del processed_group['periodogram']
            # 创建周期图数据集，使用gzip压缩
            period_ds = processed_group.create_dataset(
                'periodogram',
                data=periodogram,
                compression='gzip'
            )
            # 设置周期图描述属性
            period_ds.attrs['description'] = '周期分析结果'
            # 计算并存储周期图的MD5校验和
            period_ds.attrs['md5_checksum'] = self._calculate_md5(periodogram)
    
    def store_comprehensive_data(self, target_name, combined_time, combined_flux, best_period, periodogram):
        """
        存储综合数据 - 保存多个观测合并后的综合分析结果
        
        参数:
            target_name: 目标名称
            combined_time: 合并后的时间数据数组
            combined_flux: 合并后的通量数据数组
            best_period: 最佳周期值
            periodogram: 综合周期图数据数组
        """
        # 确保综合组结构存在
        self.create_comprehensive_structure(target_name)
        
        # 打开HDF5文件（追加模式）
        with h5py.File(self.hdf5_path, 'a') as f:
            # 获取综合组引用
            comp_group = f[f'{target_name}/comprehensive']
            # 获取或创建合并数据组
            if 'combined_data' not in comp_group:
                combined_group = comp_group.create_group('combined_data')
            else:
                combined_group = comp_group['combined_data']
            # 获取或创建分析结果组
            if 'analysis_results' not in comp_group:
                analysis_group = comp_group.create_group('analysis_results')
            else:
                analysis_group = comp_group['analysis_results']
            
            # 存储合并数据
            # 如果时间数据集已存在，先删除
            if 'time' in combined_group:
                del combined_group['time']
            # 创建合并时间数据集，使用gzip压缩
            time_ds = combined_group.create_dataset(
                'time',
                data=combined_time,
                compression='gzip'
            )
            # 设置合并时间数据单位属性
            time_ds.attrs['unit'] = 'days'
            # 设置合并时间数据描述属性
            time_ds.attrs['description'] = '合并观测时间序列'
            
            # 如果通量数据集已存在，先删除
            if 'flux' in combined_group:
                del combined_group['flux']
            # 创建合并通量数据集，使用gzip压缩
            flux_ds = combined_group.create_dataset(
                'flux',
                data=combined_flux,
                compression='gzip'
            )
            # 设置合并通量数据单位属性
            flux_ds.attrs['unit'] = 'e-/s'
            # 设置合并通量数据标准化标志属性
            flux_ds.attrs['normalized'] = True
            # 设置合并通量数据描述属性
            flux_ds.attrs['description'] = '合并后的光通量序列'
            
            # 存储分析结果
            # 如果最佳周期数据集已存在，先删除
            if 'best_period' in analysis_group:
                del analysis_group['best_period']
            # 创建最佳周期数据集
            period_ds = analysis_group.create_dataset(
                'best_period',
                data=np.array([best_period])
            )
            # 设置最佳周期单位属性
            period_ds.attrs['unit'] = 'days'
            # 设置最佳周期描述属性
            period_ds.attrs['description'] = '最佳周期估计'
            
            # 如果周期图数据集已存在，先删除
            if 'periodogram' in analysis_group:
                del analysis_group['periodogram']
            # 创建综合周期图数据集，使用gzip压缩
            periodogram_ds = analysis_group.create_dataset(
                'periodogram',
                data=periodogram,
                compression='gzip'
            )
            # 设置综合周期图描述属性
            periodogram_ds.attrs['description'] = '综合周期分析结果'
    
    def get_preprocessed_data(self, target_name, file_name):
        """
        获取预处理数据 - 读取时间和通量数据并验证MD5校验和
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            
        返回:
            tuple: (time_data, flux_data) 或 (None, None)（如果数据不存在或校验失败）
        """
        try:
            # 打开HDF5文件（只读模式）
            # 'r'表示只读模式
            with h5py.File(self.hdf5_path, 'r') as f:
                # 获取预处理组引用
                preprocessed_group = f[f'{target_name}/{file_name}/preprocessed']
                # 读取时间数据
                # h5py.Dataset[:]: 读取整个数据集内容到内存
                time_data = preprocessed_group['time'][:]
                # 读取通量数据
                flux_data = preprocessed_group['flux'][:]
                
                # 验证数据完整性
                # 验证时间数据的MD5校验和
                # h5py.Dataset.attrs: 访问数据集的属性字典
                # self._verify_md5: 验证数据的MD5校验和是否匹配
                if self._verify_md5(time_data, preprocessed_group['time'].attrs['md5_checksum']) and \
                   self._verify_md5(flux_data, preprocessed_group['flux'].attrs['md5_checksum']):
                    # 校验通过，返回数据
                    return time_data, flux_data
                else:
                    # 校验失败，抛出异常
                    raise ValueError("数据完整性校验失败")
        except KeyError:
            # 数据集不存在，返回None
            return None, None

    def read_preprocessed_data(self, target_name, file_name, time_dataset='time', flux_dataset='flux'):
        """
        从HDF5文件读取预处理数据（兼容性方法）- 调用get_preprocessed_data方法的兼容包装器
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            time_dataset: 时间数据的数据集名称（保留参数，当前未使用）
            flux_dataset: 通量数据的数据集名称（保留参数，当前未使用）
            
        返回:
            tuple: (time_data, flux_data) 或 (None, None)（如果数据不存在）
        """
        # 直接调用get_preprocessed_data方法
        return self.get_preprocessed_data(target_name, file_name)
    
    def get_processed_data(self, target_name, file_name):
        """
        获取处理后的数据 - 读取降噪通量和周期图数据并验证MD5校验和
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            
        返回:
            tuple: (denoised_flux, periodogram) 或 (None, None)（如果数据不存在或校验失败）
        """
        try:
            # 打开HDF5文件（只读模式）
            with h5py.File(self.hdf5_path, 'r') as f:
                # 获取处理组引用
                processed_group = f[f'{target_name}/{file_name}/processed']
                # 读取降噪通量数据
                denoised_flux = processed_group['denoised_flux'][:]
                # 读取周期图数据
                periodogram = processed_group['periodogram'][:]
                
                # 验证数据完整性
                # 验证降噪通量数据的MD5校验和
                if self._verify_md5(denoised_flux, processed_group['denoised_flux'].attrs['md5_checksum']) and \
                   self._verify_md5(periodogram, processed_group['periodogram'].attrs['md5_checksum']):
                    # 校验通过，返回数据
                    return denoised_flux, periodogram
                else:
                    # 校验失败，抛出异常
                    raise ValueError("数据完整性校验失败")
        except KeyError:
            # 数据集不存在，返回None
            return None, None
    
    def get_comprehensive_data(self, target_name):
        """
        获取综合数据 - 读取合并后的时间、通量、最佳周期和周期图数据
        
        参数:
            target_name: 目标名称
            
        返回:
            tuple: (combined_time, combined_flux, best_period, periodogram) 或 (None, None, None, None)（如果数据不存在）
        """
        try:
            # 打开HDF5文件（只读模式）
            with h5py.File(self.hdf5_path, 'r') as f:
                # 获取综合组引用
                comp_group = f[f'{target_name}/comprehensive']
                # 获取合并数据组引用
                combined_group = comp_group['combined_data']
                # 获取分析结果组引用
                analysis_group = comp_group['analysis_results']
                
                # 读取合并时间数据
                combined_time = combined_group['time'][:]
                # 读取合并通量数据
                combined_flux = combined_group['flux'][:]
                # 读取最佳周期（取数组第一个元素）
                best_period = analysis_group['best_period'][0]
                # 读取综合周期图数据
                periodogram = analysis_group['periodogram'][:]
                
                # 返回综合数据
                return combined_time, combined_flux, best_period, periodogram
        except KeyError:
            # 数据集不存在，返回None
            return None, None, None, None
    
    def _calculate_md5(self, data):
        """
        计算数据的MD5校验和 - 用于数据完整性验证
        
        参数:
            data: numpy数组，待计算校验和的数据
            
        返回:
            str: 数据的MD5校验和字符串（十六进制格式）
        """
        # 将numpy数组转换为字节数据
        # numpy.ndarray.tobytes(): 将数组数据转换为连续的字节流
        # 创建MD5哈希对象
        # hashlib.md5(): 创建MD5哈希对象
        # .hexdigest(): 获取十六进制格式的哈希值字符串
        return hashlib.md5(data.tobytes()).hexdigest()
    
    def _verify_md5(self, data, expected_md5):
        """
        验证数据的MD5校验和 - 检查数据是否完整未损坏
        
        参数:
            data: numpy数组，待验证的数据
            expected_md5: str，预期的MD5校验和
            
        返回:
            bool: 数据校验和是否与预期匹配
        """
        # 计算实际数据的MD5校验和并与预期校验和比较
        return self._calculate_md5(data) == expected_md5
    
    def list_targets(self):
        """
        列出所有目标 - 获取HDF5文件中包含的所有观测目标名称
        
        返回:
            list: 目标名称列表
        """
        try:
            # 打开HDF5文件（只读模式）
            with h5py.File(self.hdf5_path, 'r') as f:
                # 获取顶级组的所有键（即目标名称）
                # h5py.File.keys(): 获取文件根目录下的所有对象名称
                # list(): 转换为Python列表
                return list(f.keys())
        except (OSError, FileNotFoundError):
            # 文件不存在或无法打开，返回空列表
            return []
    
    def list_files(self, target_name):
        """
        列出指定目标的所有文件 - 获取特定目标下的所有观测文件名称
        
        参数:
            target_name: 目标名称
            
        返回:
            list: 文件名称列表（不包括'comprehensive'组）
        """
        try:
            # 打开HDF5文件（只读模式）
            with h5py.File(self.hdf5_path, 'r') as f:
                # 检查目标是否存在
                if target_name in f:
                    # 获取目标组
                    target_group = f[target_name]
                    # 获取所有子对象名称，排除'comprehensive'组
                    # h5py.Group.keys(): 获取组中的所有对象名称
                    # 列表推导式: 过滤掉'comprehensive'名称
                    return [key for key in target_group.keys() if key != 'comprehensive']
                else:
                    # 目标不存在，返回空列表
                    return []
        except (OSError, FileNotFoundError):
            # 文件不存在或无法打开，返回空列表
            return []


if __name__ == "__main__":
    # 测试代码 - 仅在直接运行该模块时执行
    # 创建HDF5管理器实例，使用测试文件名
    manager = HDF5Manager("test.h5")
    # 创建测试目标结构
    manager.create_structure("HATP7b")
    # 打印测试完成信息
    print("HDF5Manager 测试完成")