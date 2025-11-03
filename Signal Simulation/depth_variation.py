import numpy as np
import h5py
import json
import os
from datetime import datetime


def generate_basic_light_curve(duration=100, dt=0.1, period=10, 
                              transit_depth=0.02, transit_duration=1.0):
    """
    生成基础光变曲线
    
    参数:
    ------
    duration: 总观测时间
    dt: 时间步长
    period: 行星轨道周期
    transit_depth: 凌星深度
    transit_duration: 凌星持续时间
    
    返回:
    ------
    time: 时间数组
    flux: 流量数组
    """
    try:
        # 参数验证
        if duration <= 0 or dt <= 0 or period <= 0 or transit_duration <= 0:
            raise ValueError("所有时间参数必须为正数")
        if transit_depth <= 0 or transit_depth >= 1:
            raise ValueError("凌星深度必须在(0, 1)范围内")
        if transit_duration > period:
            raise ValueError("凌星持续时间不能大于轨道周期")
        
        # 生成时间序列
        time = np.arange(0, duration, dt)
        
        # 初始化流量为1（无凌星时的归一化流量）
        flux = np.ones_like(time)
        
        # 遍历每个时间点计算流量
        for i, t in enumerate(time):
            # 计算当前相位: (时间 模 周期) / 周期
            phase = (t % period) / period
            
            # 检查是否在凌星期间
            if phase < transit_duration/period:
                # 在凌星期间，流量下降
                flux[i] = 1 - transit_depth
        
        return time, flux
    except Exception as e:
        print(f"生成基础光变曲线时出错: {e}")
        raise


def add_transit_depth_variation(time, flux, base_depth=0.02, 
                               frequencies=None, amplitudes=None,
                               variation_type='all'):
    """
    添加凌星深度变化 - 支持多频率叠加
    
    数学原理:
    ---------
    深度变化模拟凌星深度的周期性变化，反映行星半径变化或恒星活动:
    
    δ(t) = δ₀ + Σ(A_i × sin(2πf_i × t))
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组  
    base_depth: 基础凌星深度
    frequencies: 频率列表（支持多频率叠加）
    amplitudes: 振幅列表（与频率一一对应）
    variation_type: 'all' 或 'transit'
    
    返回:
    ------
    varied_flux: 添加深度变化后的流量数组
    """
    try:
        # 参数验证
        if frequencies is None:
            frequencies = [0.1]  # 默认频率
        if amplitudes is None:
            amplitudes = [0.005]  # 默认振幅
        
        if len(frequencies) != len(amplitudes):
            raise ValueError("频率列表和振幅列表长度必须相同")
        
        for amp in amplitudes:
            if amp < 0:
                raise ValueError("振幅必须为非负数")
        for freq in frequencies:
            if freq < 0:
                raise ValueError("频率必须为非负数")
        
        # 复制基础流量，避免修改原数据
        varied_flux = flux.copy()
        
        # 检测凌星区域
        transit_mask = (flux < 0.99)  # 流量下降的区域认为是凌星
        
        if variation_type == 'all':
            # 生成多频率深度变化信号
            depth_variation = np.zeros_like(time)
            for freq, amp in zip(frequencies, amplitudes):
                depth_variation += amp * np.sin(2 * np.pi * freq * time)
            
            # 对每个凌星点应用变化的深度
            for i in np.where(transit_mask)[0]:
                # 计算当前凌星深度
                current_depth = base_depth + depth_variation[i]
                # 确保深度在合理范围内
                current_depth = max(0.001, min(0.5, current_depth))
                # 更新流量值
                varied_flux[i] = 1.0 - current_depth
                
        elif variation_type == 'transit':
            # 仅凌星期间深度变化
            transit_indices = np.where(transit_mask)[0]  # 找到所有凌星点的索引
            
            if len(transit_indices) > 0:
                # 生成多频率深度变化信号
                depth_variation = np.zeros_like(time)
                for freq, amp in zip(frequencies, amplitudes):
                    depth_variation += amp * np.sin(2 * np.pi * freq * time)
                
                # 提取凌星期间的深度变化
                local_depth_variation = depth_variation[transit_indices]
                
                # 应用变化的深度
                for i, idx in enumerate(transit_indices):
                    current_depth = base_depth + local_depth_variation[i]
                    current_depth = max(0.001, min(0.5, current_depth))
                    varied_flux[idx] = 1.0 - current_depth
        
        return varied_flux
    except Exception as e:
        print(f"添加深度变化时出错: {e}")
        raise


def save_to_hdf5(time, flux, params, file_path, group_name):
    """
    将模拟数据保存到HDF5文件
    
    参数:
    ------
    time: 时间数组
    flux: 流量数组
    params: 生成参数字典
    file_path: HDF5文件路径
    group_name: 组名
    """
    try:
        # 确保文件路径不为空
        if not file_path:
            raise ValueError("文件路径不能为空")
            
        # 确保目录存在
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        
        # 打开文件（使用append模式）
        with h5py.File(file_path, 'a') as f:
            # 如果组已存在，先删除
            if group_name in f:
                del f[group_name]
            
            # 创建新组
            group = f.create_group(group_name)
            
            # 存储数据
            group.create_dataset('time', data=time)
            group.create_dataset('flux', data=flux)
            
            # 存储元数据
            group.attrs['timestamp'] = datetime.now().isoformat()
            group.attrs['generator'] = 'depth_variation.py'
            group.attrs['base_period'] = params.get('period', 10)
            group.attrs['base_depth'] = params.get('transit_depth', 0.02)
            group.attrs['base_duration'] = params.get('transit_duration', 1.0)
            
            # 特殊处理频率和振幅列表
            frequencies = params.get('frequencies', [0.1])
            amplitudes = params.get('amplitudes', [0.005])
            
            # 将频率和振幅存储为字符串（便于HDF5属性存储）
            group.attrs['frequencies'] = json.dumps(frequencies)
            group.attrs['amplitudes'] = json.dumps(amplitudes)
            group.attrs['variation_type'] = params.get('variation_type', 'all')
            
            # 存储完整参数（JSON格式）
            group.attrs['parameters'] = json.dumps(params)
        
        print(f"数据成功保存到 {file_path} 的 {group_name} 组")
    except Exception as e:
        print(f"保存数据到HDF5文件时出错: {e}")
        raise


def load_config(config_path):
    """
    加载配置文件
    
    参数:
    ------
    config_path: 配置文件路径
    
    返回:
    ------
    配置字典
    """
    try:
        with open(config_path, 'r', encoding='utf-8') as f:
            config = json.load(f)
            # 兼容新的配置文件格式
            if 'output' in config and 'file_path' in config['output']:
                return {
                    'base_params': config.get('base_params', {}),
                    'depth_variation_params': config.get('depth_variation_params', {}),
                    'output_path': config['output']['file_path'],
                    'group_name': config['output']['depth_group']
                }
            return config
    except FileNotFoundError:
        print(f"配置文件未找到: {config_path}")
        # 返回默认配置 - 使用当前目录作为输出路径
        current_dir = os.path.dirname(os.path.abspath(__file__))
        default_output = os.path.join(current_dir, 'simulated_signals.h5')
        return {
            'base_params': {
                'duration': 100,
                'dt': 0.1,
                'period': 10,
                'transit_depth': 0.02,
                'transit_duration': 1.0
            },
            'depth_variation_params': {
                'frequencies': [0.1],  # 默认单频率
                'amplitudes': [0.005],
                'variation_type': 'all'
            },
            'output_path': default_output,
            'group_name': 'depth_variation'
        }
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        raise


def generate_depth_variation_signal(config_path=None):
    """
    生成带凌星深度变化噪声的信号并保存
    
    参数:
    ------
    config_path: 配置文件路径
    
    返回:
    ------
    time: 时间数组
    flux: 基础流量数组
    depth_varied_flux: 深度变化噪声信号数组
    """
    try:
        # 加载配置
        if config_path:
            config = load_config(config_path)
        else:
            # 使用默认配置路径
            default_config = 'd:\\program\\Python\\projects\\astronomy\\config\\signal_simulation_config.json'
            config = load_config(default_config)
        
        # 获取参数
        base_params = config.get('base_params', {})
        depth_params = config.get('depth_variation_params', {})
        output_path = config.get('output_path', 'simulated_signals.h5')
        group_name = config.get('group_name', 'depth_variation')
        
        # 生成基础光变曲线
        time, base_flux = generate_basic_light_curve(**base_params)
        
        # 添加深度变化
        depth_varied_flux = add_transit_depth_variation(
            time, base_flux,
            base_depth=base_params.get('transit_depth', 0.02),
            frequencies=depth_params.get('frequencies', [0.1]),
            amplitudes=depth_params.get('amplitudes', [0.005]),
            variation_type=depth_params.get('variation_type', 'all')
        )
        
        # 合并所有参数用于保存
        all_params = {
            **base_params,
            **depth_params,
            'noise_type': 'depth_variation'
        }
        
        # 保存到HDF5
        save_to_hdf5(time, depth_varied_flux, all_params, output_path, group_name)
        
        return time, base_flux, depth_varied_flux
    except Exception as e:
        print(f"生成深度变化信号时出错: {e}")
        raise


if __name__ == "__main__":
    # 测试生成深度变化信号
    try:
        time, base_flux, depth_flux = generate_depth_variation_signal()
        
        # 简单验证
        print(f"生成 {len(time)} 个数据点")
        print(f"基础流量标准差: {np.std(base_flux):.6f}")
        print(f"深度变化流量标准差: {np.std(depth_flux):.6f}")
        print(f"基础流量最小值: {np.min(base_flux):.6f}")
        print(f"深度变化流量最小值: {np.min(depth_flux):.6f}")
        print(f"基础流量最大值: {np.max(base_flux):.6f}")
        print(f"深度变化流量最大值: {np.max(depth_flux):.6f}")
        print("深度变化信号生成完成")
    except Exception as e:
        print(f"测试失败: {e}")