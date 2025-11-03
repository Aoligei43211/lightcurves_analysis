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


def add_transit_duration_variation(time, flux, base_period=10, base_duration=1.0,
                                 amplitude=0.1, frequency=0.3):
    """
    添加凌星持续时间变化 (TDV) - 数学逻辑说明
    
    数学原理:
    ---------
    TDV模拟凌星宽度的周期性变化，反映轨道倾角变化或轨道偏心率变化:
    
    D(t) = D₀ + A × sin(2πf × t)
    
    参数说明:
    ---------
    time: 时间数组
    flux: 基础流量数组（用于确定基础参数）
    base_period: 基础轨道周期
    base_duration: 基础凌星持续时间
    amplitude: 持续时间变化振幅
    frequency: 变化频率
    
    返回:
    ------
    varied_flux: 添加持续时间变化后的流量数组
    """
    try:
        # 参数验证
        if amplitude < 0:
            raise ValueError("TDV振幅必须为非负数")
        if frequency < 0:
            raise ValueError("TDV频率必须为非负数")
        
        # 创建新的流量数组，全为1（无凌星状态）
        varied_flux = np.ones_like(flux)
        
        # 从基础流量推断凌星深度
        transit_depth = 1.0 - np.min(flux)
        
        # 生成持续时间变化信号
        duration_variation = amplitude * np.sin(2 * np.pi * frequency * time)
        
        # 遍历每个时间点，重新计算凌星状态
        for i, t in enumerate(time):
            # 计算当前持续时间（基础值 + 正弦变化）
            current_duration = base_duration + duration_variation[i]
            # 确保持续时间不为负
            current_duration = max(0.1, current_duration)
            
            # 计算当前相位
            phase = (t % base_period) / base_period
            
            # 检查是否在凌星期间（使用变化的持续时间）
            if phase < current_duration/base_period:
                # 在凌星期间，应用固定的凌星深度
                varied_flux[i] = 1 - transit_depth
        
        return varied_flux
    except Exception as e:
        print(f"添加TDV时出错: {e}")
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
            group.attrs['generator'] = 'tdv_only.py'
            group.attrs['base_period'] = params.get('period', 10)
            group.attrs['base_depth'] = params.get('transit_depth', 0.02)
            group.attrs['base_duration'] = params.get('transit_duration', 1.0)
            group.attrs['tdv_amplitude'] = params.get('tdv_amplitude', 0.1)
            group.attrs['tdv_frequency'] = params.get('tdv_frequency', 0.3)
            
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
                    'tdv_params': config.get('tdv_params', {}),
                    'output_path': config['output']['file_path'],
                    'group_name': config['output']['tdv_group']
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
            'tdv_params': {
                'amplitude': 0.1,
                'frequency': 0.05
            },
            'output_path': default_output,
            'group_name': 'tdv_only'
        }
    except json.JSONDecodeError as e:
        print(f"配置文件格式错误: {e}")
        raise


def generate_tdv_signal(config_path=None):
    """
    生成带TDV噪声的信号并保存
    
    参数:
    ------
    config_path: 配置文件路径
    
    返回:
    ------
    time: 时间数组
    flux: 基础流量数组
    tdv_flux: TDV噪声信号数组
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
        tdv_params = config.get('tdv_params', {})
        output_path = config.get('output_path', 'simulated_signals.h5')
        group_name = config.get('group_name', 'tdv_only')
        
        # 生成基础光变曲线
        time, base_flux = generate_basic_light_curve(**base_params)
        
        # 添加TDV
        tdv_flux = add_transit_duration_variation(
            time, base_flux,
            base_period=base_params.get('period', 10),
            base_duration=base_params.get('transit_duration', 1.0),
            amplitude=tdv_params.get('amplitude', 0.1),
            frequency=tdv_params.get('frequency', 0.3)
        )
        
        # 合并所有参数用于保存
        all_params = {
            **base_params,
            **tdv_params,
            'noise_type': 'tdv_only'
        }
        
        # 保存到HDF5
        save_to_hdf5(time, tdv_flux, all_params, output_path, group_name)
        
        return time, base_flux, tdv_flux
    except Exception as e:
        print(f"生成TDV信号时出错: {e}")
        raise


if __name__ == "__main__":
    # 测试生成TDV信号
    try:
        time, base_flux, tdv_flux = generate_tdv_signal()
        
        # 简单验证
        print(f"生成 {len(time)} 个数据点")
        print(f"基础流量最小值: {np.min(base_flux):.6f}")
        print(f"TDV流量最小值: {np.min(tdv_flux):.6f}")
        print(f"基础流量凌星点数: {np.sum(base_flux < 0.99)}")
        print(f"TDV后凌星点数: {np.sum(tdv_flux < 0.99)}")
        print("TDV信号生成完成")
    except Exception as e:
        print(f"测试失败: {e}")