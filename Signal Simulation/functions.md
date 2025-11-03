#这是实现模拟光变曲线的函数参考文档

import numpy as np
from base_lightcurve import generate_basic_light_curve
from transit_depth_variation import add_transit_depth_variation
from transit_duration_variation import add_transit_duration_variation  
from transit_timing_variation import add_transit_timing_variation

def generate_realistic_light_curve(scenario='default'):
    """
    生成现实场景的光变曲线 - 综合各种效应
    
    数学原理:
    ---------
    现实光变曲线是多种物理效应的叠加:
    
    flux_final(t) = [基础光变曲线]
                    × [深度变化效应] 
                    × [TDV效应]
                    × [TTV效应]
                    + [测量噪声]
    
    每种效应都通过调整相应的物理参数来实现。
    
    参数说明:
    ---------
    scenario: 场景类型
        - 'default': 默认参数
        - 'active_star': 活跃恒星场景（强深度变化）
        - 'multi_planet': 多行星系统（强TTV）
        - 'eccentric_orbit': 偏心轨道（强TDV）
    
    返回:
    ------
    time: 时间数组
    complete_flux: 综合效应后的流量数组  
    base_flux: 基础流量数组（用于比较）
    """
    
    # 基础参数
    base_params = {
        'duration': 100,      # 总观测时间
        'dt': 0.1,           # 时间分辨率
        'period': 10,        # 轨道周期
        'transit_depth': 0.02, # 凌星深度
        'transit_duration': 1.0 # 凌星持续时间
    }
    
    # 根据场景调整参数
    scenario_params = {
        'default': {
            'depth_amp': 0.003, 'depth_freq': 0.08,  # 深度变化参数
            'tdv_amp': 0.15, 'tdv_freq': 0.4,       # TDV参数
            'ttv_amp': 0.2, 'ttv_freq': 0.06,       # TTV参数
            'noise_level': 0.001                    # 噪声水平
        },
        'active_star': {
            'depth_amp': 0.008, 'depth_freq': 0.12, # 强深度变化
            'tdv_amp': 0.1, 'tdv_freq': 0.3,
            'ttv_amp': 0.1, 'ttv_freq': 0.04, 
            'noise_level': 0.002
        },
        'multi_planet': {
            'depth_amp': 0.002, 'depth_freq': 0.05,
            'tdv_amp': 0.08, 'tdv_freq': 0.2,
            'ttv_amp': 0.5, 'ttv_freq': 0.08,       # 强TTV
            'noise_level': 0.001
        },
        'eccentric_orbit': {
            'depth_amp': 0.001, 'depth_freq': 0.03,
            'tdv_amp': 0.4, 'tdv_freq': 0.1,        # 强TDV
            'ttv_amp': 0.05, 'ttv_freq': 0.02,
            'noise_level': 0.0015
        }
    }
    
    params = scenario_params.get(scenario, scenario_params['default'])
    
    # 生成基础光变曲线
    time, base_flux = generate_basic_light_curve(**base_params)
    
    # 逐步添加各种效应
    current_flux = base_flux.copy()
    
    # 1. 添加凌星深度变化
    current_flux = add_transit_depth_variation(
        time, current_flux, 
        amplitude=params['depth_amp'], 
        frequency=params['depth_freq'],
        variation_type='all'
    )
    
    # 2. 添加凌星持续时间变化 (TDV)
    current_flux = add_transit_duration_variation(
        time, current_flux,
        amplitude=params['tdv_amp'],
        frequency=params['tdv_freq']
    )
    
    # 3. 添加凌星计时变化 (TTV)
    current_flux = add_transit_timing_variation(
        time, current_flux,
        amplitude=params['ttv_amp'],
        frequency=params['ttv_freq']
    )
    
    # 4. 添加测量噪声（高斯白噪声）
    measurement_noise = np.random.normal(0, params['noise_level'], len(current_flux))
    complete_flux = current_flux + measurement_noise
    
    return time, complete_flux, base_flux

def generate_individual_effects_comparison():
    """
    生成单一效应比较数据
    
    返回所有单一效应的光变曲线，用于分析每种效应的独立影响
    """
    time, base_flux = generate_basic_light_curve()
    
    # 生成各种单一效应
    effects = {
        'base': base_flux,
        'depth_only': add_transit_depth_variation(time, base_flux.copy()),
        'tdv_only': add_transit_duration_variation(time, base_flux.copy()), 
        'ttv_only': add_transit_timing_variation(time, base_flux.copy()),
        'noise_only': base_flux + np.random.normal(0, 0.001, len(base_flux))
    }
    
    return time, effects

# 测试代码
if __name__ == "__main__":
    print("生成综合光变曲线...")
    
    # 测试不同场景
    scenarios = ['default', 'active_star', 'multi_planet', 'eccentric_orbit']
    
    for scenario in scenarios:
        time, complete_flux, base_flux = generate_realistic_light_curve(scenario)
        print(f"{scenario}场景: 流量标准差 = {np.std(complete_flux):.6f}")
    
    # 测试单一效应
    time, effects = generate_individual_effects_comparison()
    print(f"生成 {len(effects)} 种单一效应数据")