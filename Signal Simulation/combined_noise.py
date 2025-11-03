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


def add_transit_timing_variation(time, flux, period=10, 
                                ttv_amplitude=0.1, ttv_frequency=0.01):
    """
    添加凌星时间变化(TTV)噪声
    
    数学原理:
    ---------
    TTV模拟凌星发生时间的周期性偏移:
    
    Δt(n) = A × sin(2πf×t)
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组  
    period: 基础轨道周期
    ttv_amplitude: TTV振幅
    ttv_frequency: TTV频率
    
    返回:
    ------
    ttv_flux: 添加TTV后的流量数组
    """
    try:
        # 参数验证
        if ttv_amplitude < 0:
            raise ValueError("TTV振幅必须为非负数")
        if ttv_frequency < 0:
            raise ValueError("TTV频率必须为非负数")
        
        # 复制基础流量，避免修改原数据
        ttv_flux = np.ones_like(flux)
        
        # 计算每个时间点的TTV偏移
        for i, t in enumerate(time):
            # 计算当前TTV偏移
            ttv_offset = ttv_amplitude * np.sin(2 * np.pi * ttv_frequency * t)
            
            # 计算原始相位（无TTV）
            original_phase = (t % period) / period
            
            # 计算带TTV的相位
            ttv_phase = ((t + ttv_offset) % period) / period
            
            # 找出凌星期间的流量下降
            transit_mask = (flux < 0.99)  # 流量下降的区域
            
            if transit_mask[i]:
                # 如果原时间在凌星内，检查带TTV偏移后是否仍在凌星内
                base_transit_depth = 1.0 - flux[i]  # 获取原始深度
                
                # 重新计算流量
                transit_duration = np.sum(transit_mask) * (time[1] - time[0])
                transit_width = transit_duration / period
                
                if ttv_phase < transit_width:
                    # 带TTV后仍在凌星内
                    ttv_flux[i] = 1.0 - base_transit_depth
                else:
                    # 带TTV后不在凌星内
                    ttv_flux[i] = 1.0
            else:
                # 检查原时间不在凌星内，但带TTV后是否进入凌星内
                transit_duration = np.sum(transit_mask) * (time[1] - time[0])
                transit_width = transit_duration / period
                
                if ttv_phase < transit_width:
                    # 带TTV后进入凌星内
                    # 计算平均深度
                    average_depth = 1.0 - np.mean(flux[transit_mask])
                    ttv_flux[i] = 1.0 - average_depth
                else:
                    # 保持原值
                    ttv_flux[i] = 1.0
        
        return ttv_flux
    except Exception as e:
        print(f"添加TTV时出错: {e}")
        raise


def add_transit_duration_variation(time, flux, base_duration=1.0, 
                                  tdv_amplitude=0.1, tdv_frequency=0.05):
    """
    添加凌星持续时间变化(TDV)噪声
    
    数学原理:
    ---------
    TDV模拟凌星持续时间的周期性变化:
    
    D(t) = D₀ + A × sin(2πf×t)
    
    参数说明:
    ---------
    time: 时间数组
    flux: 流量数组  
    base_duration: 基础凌星持续时间
    tdv_amplitude: TDV振幅
    tdv_frequency: TDV频率
    
    返回:
    ------
    tdv_flux: 添加TDV后的流量数组
    """
    try:
        # 参数验证
        if tdv_amplitude < 0:
            raise ValueError("TDV振幅必须为非负数")
        if tdv_frequency < 0:
            raise ValueError("TDV频率必须为非负数")
        
        # 复制基础流量，避免修改原数据
        tdv_flux = np.ones_like(flux)
        
        # 检测原始凌星区域
        base_transit_mask = (flux < 0.99)
        if not np.any(base_transit_mask):
            raise ValueError("输入的光变曲线中未检测到凌星")
        
        # 计算基础深度和周期
        base_depth = 1.0 - np.mean(flux[base_transit_mask])
        period = time[-1] / np.sum(base_transit_mask) * np.sum(flux < 0.99)
        
        # 处理每个凌星事件
        transit_events = []
        in_transit = False
        current_transit = []
        
        for i, in_base_transit in enumerate(base_transit_mask):
            if in_base_transit and not in_transit:
                in_transit = True
                current_transit = [i]
            elif in_transit and not in_base_transit:
                in_transit = False
                current_transit.append(i-1)
                transit_events.append(current_transit)
        
        if in_transit and current_transit:
            current_transit.append(len(time)-1)
            transit_events.append(current_transit)
        
        # 对每个凌星事件应用TDV
        for start_idx, end_idx in transit_events:
            # 计算事件中心点时间
            center_time = time[(start_idx + end_idx) // 2]
            
            # 计算当前持续时间变化
            duration_variation = tdv_amplitude * np.sin(2 * np.pi * tdv_frequency * center_time)
            new_duration = base_duration + duration_variation
            
            # 确保持续时间为正数
            new_duration = max(0.1, new_duration)
            
            # 计算持续时间比率
            duration_ratio = new_duration / base_duration
            
            # 计算扩展的开始和结束索引
            original_length = end_idx - start_idx + 1
            new_length = int(original_length * duration_ratio)
            
            # 确保新长度至少为1
            new_length = max(1, new_length)
            
            # 计算新的开始和结束索引（保持中心不变）
            new_start = max(0, (start_idx + end_idx) // 2 - new_length // 2)
            new_end = min(len(time) - 1, new_start + new_length - 1)
            
            # 更新流量值
            tdv_flux[new_start:new_end+1] = 1.0 - base_depth
        
        return tdv_flux
    except Exception as e:
        print(f"添加TDV时出错: {e}")
        raise


def add_transit_depth_variation(time, flux, base_depth=0.02, 
                               frequencies=None, amplitudes=None,
                               variation_type='all'):
    """
    添加凌星深度变化噪声 - 支持多频率叠加
    
    数学原理:
    ---------
    深度变化模拟凌星深度的周期性变化:
    
    δ(t) = δ₀ + Σ(A_i × sin(2πf_i × t))
    
    参数说明:
    ---------
    time: 时间数组
    flux: 流量数组  
    base_depth: 基础凌星深度
    frequencies: 频率列表
    amplitudes: 振幅列表
    variation_type: 'all' 或 'transit'
    
    返回:
    ------
    varied_flux: 添加深度变化后的流量数组
    """
    try:
        # 参数验证
        if frequencies is None:
            frequencies = [0.1]
        if amplitudes is None:
            amplitudes = [0.005]
        
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
        transit_mask = (flux < 0.99)
        
        if variation_type == 'all':
            # 生成多频率深度变化信号
            depth_variation = np.zeros_like(time)
            for freq, amp in zip(frequencies, amplitudes):
                depth_variation += amp * np.sin(2 * np.pi * freq * time)
            
            # 应用变化的深度
            for i in np.where(transit_mask)[0]:
                current_depth = base_depth + depth_variation[i]
                current_depth = max(0.001, min(0.5, current_depth))
                varied_flux[i] = 1.0 - current_depth
                
        elif variation_type == 'transit':
            transit_indices = np.where(transit_mask)[0]
            
            if len(transit_indices) > 0:
                depth_variation = np.zeros_like(time)
                for freq, amp in zip(frequencies, amplitudes):
                    depth_variation += amp * np.sin(2 * np.pi * freq * time)
                
                local_depth_variation = depth_variation[transit_indices]
                
                for i, idx in enumerate(transit_indices):
                    current_depth = base_depth + local_depth_variation[i]
                    current_depth = max(0.001, min(0.5, current_depth))
                    varied_flux[idx] = 1.0 - current_depth
        
        return varied_flux
    except Exception as e:
        print(f"添加深度变化时出错: {e}")
        raise


def combine_noises(time, base_flux, ttv_params=None, tdv_params=None, depth_params=None):
    """
    组合多种噪声类型
    
    参数:
    ------
    time: 时间数组
    base_flux: 基础流量数组
    ttv_params: TTV参数字典，如果为None则不添加TTV
    tdv_params: TDV参数字典，如果为None则不添加TDV
    depth_params: 深度变化参数字典，如果为None则不添加深度变化
    
    返回:
    ------
    combined_flux: 组合噪声后的流量数组
    applied_noises: 应用的噪声类型列表
    """
    try:
        applied_noises = []
        
        # 初始化为基础流量
        combined_flux = base_flux.copy()
        
        # 添加TTV
        if ttv_params is not None and ttv_params.get('enabled', True):
            combined_flux = add_transit_timing_variation(
                time, combined_flux,
                period=ttv_params.get('period', 10),
                ttv_amplitude=ttv_params.get('amplitude', 0.1),
                ttv_frequency=ttv_params.get('frequency', 0.01)
            )
            applied_noises.append('ttv')
        
        # 添加TDV
        if tdv_params is not None and tdv_params.get('enabled', True):
            combined_flux = add_transit_duration_variation(
                time, combined_flux,
                base_duration=tdv_params.get('base_duration', 1.0),
                tdv_amplitude=tdv_params.get('amplitude', 0.1),
                tdv_frequency=tdv_params.get('frequency', 0.05)
            )
            applied_noises.append('tdv')
        
        # 添加深度变化
        if depth_params is not None and depth_params.get('enabled', True):
            combined_flux = add_transit_depth_variation(
                time, combined_flux,
                base_depth=depth_params.get('base_depth', 0.02),
                frequencies=depth_params.get('frequencies', [0.1]),
                amplitudes=depth_params.get('amplitudes', [0.005]),
                variation_type=depth_params.get('variation_type', 'all')
            )
            applied_noises.append('depth_variation')
        
        return combined_flux, applied_noises
    except Exception as e:
        print(f"组合噪声时出错: {e}")
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
            group.attrs['generator'] = 'combined_noise.py'
            group.attrs['noise_types'] = json.dumps(params.get('applied_noises', []))
            
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
                    'ttv_params': config.get('ttv_params', {}),
                    'tdv_params': config.get('tdv_params', {}),
                    'depth_params': config.get('depth_variation_params', {}),
                    'output_path': config['output']['file_path'],
                    'group_name': config['output']['combined_group']
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
            'ttv_params': {
                'enabled': True,
                'amplitude': 0.1,
                'frequency': 0.01
            },
            'tdv_params': {
                'enabled': True,
                'amplitude': 0.1,
                'frequency': 0.05
            },
            'depth_params': {
                'enabled': True,
                'frequencies': [0.1],
                'amplitudes': [0.005],
                'variation_type': 'all'
            },
            'output_path': default_output,
            'group_name': 'combined_noise'
        }
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        raise


def generate_combined_noise_signal(config_path=None):
    """
    生成组合多种噪声的信号并保存
    
    参数:
    ------
    config_path: 配置文件路径
    
    返回:
    ------
    time: 时间数组
    base_flux: 基础流量数组
    combined_flux: 组合噪声后的流量数组
    applied_noises: 应用的噪声类型列表
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
        ttv_params = config.get('ttv_params', None)
        tdv_params = config.get('tdv_params', None)
        depth_params = config.get('depth_params', None)
        output_path = config.get('output_path', 'simulated_signals.h5')
        group_name = config.get('group_name', 'combined_noise')
        
        # 生成基础光变曲线
        time, base_flux = generate_basic_light_curve(**base_params)
        
        # 组合噪声
        combined_flux, applied_noises = combine_noises(
            time, base_flux,
            ttv_params=ttv_params,
            tdv_params=tdv_params,
            depth_params=depth_params
        )
        
        # 合并所有参数用于保存
        all_params = {
            **base_params,
            'ttv_params': ttv_params,
            'tdv_params': tdv_params,
            'depth_params': depth_params,
            'applied_noises': applied_noises,
            'noise_type': 'combined'
        }
        
        # 保存到HDF5
        save_to_hdf5(time, combined_flux, all_params, output_path, group_name)
        
        return time, base_flux, combined_flux, applied_noises
    except Exception as e:
        print(f"生成组合噪声信号时出错: {e}")
        raise


if __name__ == "__main__":
    # 测试生成组合噪声信号
    try:
        time, base_flux, combined_flux, applied_noises = generate_combined_noise_signal()
        
        # 简单验证
        print(f"生成 {len(time)} 个数据点")
        print(f"应用的噪声类型: {', '.join(applied_noises)}")
        print(f"基础流量标准差: {np.std(base_flux):.6f}")
        print(f"组合噪声流量标准差: {np.std(combined_flux):.6f}")
        print(f"基础流量最小值: {np.min(base_flux):.6f}")
        print(f"组合噪声流量最小值: {np.min(combined_flux):.6f}")
        print(f"基础流量最大值: {np.max(base_flux):.6f}")
        print(f"组合噪声流量最大值: {np.max(combined_flux):.6f}")
        print("组合噪声信号生成完成")
    except Exception as e:
        print(f"测试失败: {e}")