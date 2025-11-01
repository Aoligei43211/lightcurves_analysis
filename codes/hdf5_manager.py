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

import h5py
import numpy as np
import hashlib
import os
from datetime import datetime
from logging_config import get_logger


class HDF5Manager:
    """HDF5数据存储管理器"""
    
    def __init__(self, hdf5_path):
        """
        初始化HDF5管理器
        
        参数:
            hdf5_path: HDF5文件路径
        """
        self.hdf5_path = hdf5_path
        self.format_version = "1.0"
        self.logger = get_logger('hdf5_manager')
        self.logger.info(f"初始化HDF5管理器，文件路径: {hdf5_path}")#
    
    def create_structure(self, target_name):
        """
        为指定目标创建标准HDF5结构
        
        参数:
            target_name: 目标名称（如HATP7b）
        """
        self.logger.info(f"为目标 {target_name} 创建HDF5结构")
        with h5py.File(self.hdf5_path, 'a') as f:
            if target_name not in f:
                target_group = f.create_group(target_name)
                target_group.attrs['format_version'] = self.format_version
                target_group.attrs['created_date'] = datetime.now().isoformat()
                self.logger.debug(f"已创建目标组: {target_name}")
            else:
                self.logger.debug(f"目标组已存在: {target_name}")
    
    def create_file_structure(self, target_name, file_name):
        """
        为单个文件创建子文件组结构
        
        参数:
            target_name: 目标名称
            file_name: 文件名称（不含扩展名）
        """
        self.logger.info(f"为文件 {file_name} 创建子文件组结构")
        with h5py.File(self.hdf5_path, 'a') as f:
            if target_name not in f:
                self.create_structure(target_name)
            
            target_group = f[target_name]
            if file_name not in target_group:
                file_group = target_group.create_group(file_name)
                
                # 创建属性组
                attrs_group = file_group.create_group('attributes')
                attrs_group.attrs['source_file'] = f'{file_name}.fits'
                attrs_group.attrs['processing_date'] = datetime.now().isoformat()
                attrs_group.attrs['algorithm_params'] = '{}'
                
                # 创建预处理数据组
                preprocessed_group = file_group.create_group('preprocessed')
                preprocessed_group.attrs['description'] = '预处理后的时间序列数据'
                
                # 创建处理数据组
                processed_group = file_group.create_group('processed')
                processed_group.attrs['description'] = '处理后的数据和分析结果'
                
                self.logger.debug(f"已为文件 {file_name} 创建完整的HDF5结构")
            else:
                self.logger.debug(f"文件组已存在: {file_name}")
    
    def create_comprehensive_structure(self, target_name):
        """
        创建综合组结构
        
        参数:
            target_name: 目标名称
        """
        self.logger.info(f"为目标 {target_name} 创建综合组结构")
        with h5py.File(self.hdf5_path, 'a') as f:
            if target_name not in f:
                self.create_structure(target_name)
            
            target_group = f[target_name]
            if 'comprehensive' not in target_group:
                comp_group = target_group.create_group('comprehensive')
                comp_group.attrs['description'] = '综合分析和聚合数据'
                comp_group.attrs['created_date'] = datetime.now().isoformat()
                self.logger.debug(f"已创建综合组: comprehensive")
            else:
                self.logger.debug(f"综合组已存在: comprehensive")
    
    def store_preprocessed_data(self, target_name, file_name, time_data, flux_data):
        """
        存储预处理数据
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            time_data: 时间数据数组
            flux_data: 通量数据数组
            
        返回:
            bool: 存储是否成功
        """
        try:
            self.create_file_structure(target_name, file_name)
            
            with h5py.File(self.hdf5_path, 'a') as f:
                file_group = f[f'{target_name}/{file_name}']
                preprocessed_group = file_group['preprocessed']
                
                # 存储时间数据
                if 'time' in preprocessed_group:
                    del preprocessed_group['time']
                time_ds = preprocessed_group.create_dataset(
                    'time', 
                    data=time_data,
                    compression='gzip'
                )
                time_ds.attrs['unit'] = 'days'
                time_ds.attrs['description'] = '观测时间序列'
                time_ds.attrs['md5_checksum'] = self._calculate_md5(time_data)
                
                # 存储通量数据
                if 'flux' in preprocessed_group:
                    del preprocessed_group['flux']
                flux_ds = preprocessed_group.create_dataset(
                    'flux',
                    data=flux_data,
                    compression='gzip'
                )
                flux_ds.attrs['unit'] = 'e-/s'
                flux_ds.attrs['normalized'] = True
                flux_ds.attrs['description'] = '预处理后的光通量序列'
                flux_ds.attrs['md5_checksum'] = self._calculate_md5(flux_data)
            
            return True
        except Exception as e:
            self.logger.error(f"存储预处理数据失败: {str(e)}")
            return False
    
    def store_processed_data(self, target_name, file_name, denoised_flux, periodogram):
        """
        存储处理后的数据
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            denoised_flux: 降噪后的通量数据
            periodogram: 周期图数据
        """
        self.create_file_structure(target_name, file_name)
        
        with h5py.File(self.hdf5_path, 'a') as f:
            file_group = f[f'{target_name}/{file_name}']
            processed_group = file_group['processed']
            
            # 存储降噪数据
            if 'denoised_flux' in processed_group:
                del processed_group['denoised_flux']
            denoised_ds = processed_group.create_dataset(
                'denoised_flux',
                data=denoised_flux,
                compression='gzip'
            )
            denoised_ds.attrs['description'] = '降噪后的光通量序列'
            denoised_ds.attrs['md5_checksum'] = self._calculate_md5(denoised_flux)
            
            # 存储周期图数据
            if 'periodogram' in processed_group:
                del processed_group['periodogram']
            period_ds = processed_group.create_dataset(
                'periodogram',
                data=periodogram,
                compression='gzip'
            )
            period_ds.attrs['description'] = '周期分析结果'
            period_ds.attrs['md5_checksum'] = self._calculate_md5(periodogram)
    
    def store_comprehensive_data(self, target_name, combined_time, combined_flux, best_period, periodogram):
        """
        存储综合数据
        
        参数:
            target_name: 目标名称
            combined_time: 合并后的时间数据
            combined_flux: 合并后的通量数据
            best_period: 最佳周期
            periodogram: 综合周期图
        """
        self.create_comprehensive_structure(target_name)
        
        with h5py.File(self.hdf5_path, 'a') as f:
            comp_group = f[f'{target_name}/comprehensive']
            combined_group = comp_group['combined_data']
            analysis_group = comp_group['analysis_results']
            
            # 存储合并数据
            if 'time' in combined_group:
                del combined_group['time']
            time_ds = combined_group.create_dataset(
                'time',
                data=combined_time,
                compression='gzip'
            )
            time_ds.attrs['unit'] = 'days'
            time_ds.attrs['description'] = '合并观测时间序列'
            
            if 'flux' in combined_group:
                del combined_group['flux']
            flux_ds = combined_group.create_dataset(
                'flux',
                data=combined_flux,
                compression='gzip'
            )
            flux_ds.attrs['unit'] = 'e-/s'
            flux_ds.attrs['normalized'] = True
            flux_ds.attrs['description'] = '合并后的光通量序列'
            
            # 存储分析结果
            if 'best_period' in analysis_group:
                del analysis_group['best_period']
            period_ds = analysis_group.create_dataset(
                'best_period',
                data=np.array([best_period])
            )
            period_ds.attrs['unit'] = 'days'
            period_ds.attrs['description'] = '最佳周期估计'
            
            if 'periodogram' in analysis_group:
                del analysis_group['periodogram']
            periodogram_ds = analysis_group.create_dataset(
                'periodogram',
                data=periodogram,
                compression='gzip'
            )
            periodogram_ds.attrs['description'] = '综合周期分析结果'
    
    def get_preprocessed_data(self, target_name, file_name):
        """
        获取预处理数据
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            
        返回:
            time_data, flux_data
        """
        try:
            with h5py.File(self.hdf5_path, 'r') as f:
                preprocessed_group = f[f'{target_name}/{file_name}/preprocessed']
                time_data = preprocessed_group['time'][:]
                flux_data = preprocessed_group['flux'][:]
                
                # 验证数据完整性
                if self._verify_md5(time_data, preprocessed_group['time'].attrs['md5_checksum']) and \
                   self._verify_md5(flux_data, preprocessed_group['flux'].attrs['md5_checksum']):
                    return time_data, flux_data
                else:
                    raise ValueError("数据完整性校验失败")
        except KeyError:
            return None, None

    def read_preprocessed_data(self, target_name, file_name, time_dataset='time', flux_dataset='flux'):
        """
        从HDF5文件读取预处理数据（兼容性方法）
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            time_dataset: 时间数据的数据集名称
            flux_dataset: 通量数据的数据集名称
            
        返回:
            time_data, flux_data
        """
        return self.get_preprocessed_data(target_name, file_name)
    
    def get_processed_data(self, target_name, file_name):
        """
        获取处理后的数据
        
        参数:
            target_name: 目标名称
            file_name: 文件名称
            
        返回:
            denoised_flux, periodogram
        """
        try:
            with h5py.File(self.hdf5_path, 'r') as f:
                processed_group = f[f'{target_name}/{file_name}/processed']
                denoised_flux = processed_group['denoised_flux'][:]
                periodogram = processed_group['periodogram'][:]
                
                if self._verify_md5(denoised_flux, processed_group['denoised_flux'].attrs['md5_checksum']) and \
                   self._verify_md5(periodogram, processed_group['periodogram'].attrs['md5_checksum']):
                    return denoised_flux, periodogram
                else:
                    raise ValueError("数据完整性校验失败")
        except KeyError:
            return None, None
    
    def get_comprehensive_data(self, target_name):
        """
        获取综合数据
        
        参数:
            target_name: 目标名称
            
        返回:
            combined_time, combined_flux, best_period, periodogram
        """
        try:
            with h5py.File(self.hdf5_path, 'r') as f:
                comp_group = f[f'{target_name}/comprehensive']
                combined_group = comp_group['combined_data']
                analysis_group = comp_group['analysis_results']
                
                combined_time = combined_group['time'][:]
                combined_flux = combined_group['flux'][:]
                best_period = analysis_group['best_period'][0]
                periodogram = analysis_group['periodogram'][:]
                
                return combined_time, combined_flux, best_period, periodogram
        except KeyError:
            return None, None, None, None
    
    def _calculate_md5(self, data):
        """计算数据的MD5校验和"""
        return hashlib.md5(data.tobytes()).hexdigest()
    
    def _verify_md5(self, data, expected_md5):
        """验证数据的MD5校验和"""
        return self._calculate_md5(data) == expected_md5
    
    def list_targets(self):
        """列出所有目标"""
        try:
            with h5py.File(self.hdf5_path, 'r') as f:
                return list(f.keys())
        except (OSError, FileNotFoundError):
            return []
    
    def list_files(self, target_name):
        """列出指定目标的所有文件"""
        try:
            with h5py.File(self.hdf5_path, 'r') as f:
                if target_name in f:
                    target_group = f[target_name]
                    return [key for key in target_group.keys() if key != 'comprehensive']
                else:
                    return []
        except (OSError, FileNotFoundError):
            return []


if __name__ == "__main__":
    # 测试代码
    manager = HDF5Manager("test.h5")
    manager.create_structure("HATP7b")
    print("HDF5Manager 测试完成")