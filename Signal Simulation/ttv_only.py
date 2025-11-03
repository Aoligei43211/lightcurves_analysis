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


def add_transit_timing_variation(time, flux, base_period=10, base_duration=1.0,
                                amplitude=0.2, frequency=0.05):
    """
    添加凌星计时变化 (TTV) - 数学逻辑说明
    
    数学原理:
    ---------
    TTV模拟凌星中心时间的周期性偏移，反映轨道摄动或额外行星影响:
    
    Δt = A × sin(2πf × t)
    t_actual = t_nominal + Δt
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组
    base_period: 基础轨道周期
    base_duration: 基础凌星持续时间  
    amplitude: TTV振幅
    frequency: TTV频率
    
    返回:
    ------
    varied_flux: 添加TTV后的流量数组
    """
    try:
        # 参数验证
        if amplitude < 0:
            raise ValueError("TTV振幅必须为非负数")
        if frequency < 0:
            raise ValueError("TTV频率必须为非负数")
        
        # 创建新的流量数组，全为1
        varied_flux = np.ones_like(flux)
        
        # 从基础流量推断凌星深度
        transit_depth = 1.0 - np.min(flux)
        
        # 生成TTV信号（时间偏移）
        ttv_shift = amplitude * np.sin(2 * np.pi * frequency * time)
        
        # 遍历每个时间点，应用时间偏移
        for i, t in enumerate(time):
            # 调整时间：实际时间 = 理论时间 + TTV偏移
            adjusted_t = t + ttv_shift[i]
            
            # 使用调整后的时间计算相位
            phase = (adjusted_t % base_period) / base_period
            
            # 检查是否在凌星期间
            if phase < base_duration/base_period:
                # 在凌星期间，应用固定的凌星深度
                varied_flux[i] = 1 - transit_depth
        
        return varied_flux
    except Exception as e:
        print(f"添加TTV时出错: {e}")
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
            group.attrs['generator'] = 'ttv_only.py'
            group.attrs['base_period'] = params.get('period', 10)
            group.attrs['base_depth'] = params.get('transit_depth', 0.02)
            group.attrs['base_duration'] = params.get('transit_duration', 1.0)
            group.attrs['ttv_amplitude'] = params.get('ttv_amplitude', 0.2)
            group.attrs['ttv_frequency'] = params.get('ttv_frequency', 0.05)
            
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
                    'output_path': config['output']['file_path'],
                    'group_name': config['output']['ttv_group']
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
                'amplitude': 0.1,
                'frequency': 0.01
            },
            'output_path': default_output,
            'group_name': 'ttv_only'
        }
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        raise


def generate_ttv_signal(config_path=None):
    """
    生成带TTV噪声的信号并保存
    
    参数:
    ------
    config_path: 配置文件路径
    
    返回:
    ------
    time: 时间数组
    flux: 基础流量数组
    ttv_flux: TTV噪声信号数组
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
        ttv_params = config.get('ttv_params', {})
        output_path = config.get('output_path', 'simulated_signals.h5')
        group_name = config.get('group_name', 'ttv_only')
        
        # 生成基础光变曲线
        time, base_flux = generate_basic_light_curve(**base_params)
        
        # 添加TTV
        ttv_flux = add_transit_timing_variation(
            time, base_flux,
            base_period=base_params.get('period', 10),
            base_duration=base_params.get('transit_duration', 1.0),
            amplitude=ttv_params.get('amplitude', 0.2),
            frequency=ttv_params.get('frequency', 0.05)
        )
        
        # 合并所有参数用于保存
        all_params = {
            **base_params,
            **ttv_params,
            'noise_type': 'ttv_only'
        }
        
        # 保存到HDF5
        save_to_hdf5(time, ttv_flux, all_params, output_path, group_name)
        
        return time, base_flux, ttv_flux
    except Exception as e:
        print(f"生成TTV信号时出错: {e}")
        raise


if __name__ == "__main__":
    # 测试生成TTV信号
    try:
        time, base_flux, ttv_flux = generate_ttv_signal()
        
        # 简单验证
        print(f"生成 {len(time)} 个数据点")
        print(f"基础流量最小值: {np.min(base_flux):.6f}")
        print(f"TTV流量最小值: {np.min(ttv_flux):.6f}")
        print("TTV信号生成完成")
    except Exception as e:
        print(f"测试失败: {e}")