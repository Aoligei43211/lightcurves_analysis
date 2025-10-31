"""
天文光变曲线分析使用示例

本脚本演示了如何使用仓库中的模块进行完整的数据分析流程：
1. 读取FITS文件数据
2. 处理和清洗数据
3. 计算最佳周期
4. 绘制光变曲线

使用方法：
    python example_usage.py
"""
import numpy as np
import matplotlib.pyplot as plt
import os

# 导入本仓库的模块
try:
    from data_processing_sigle import get_sorted_data
    from lightcurve_period import period_culculator
except ImportError as e:
    print(f"导入模块时出错: {e}")
    print("请确保在正确的目录下运行，或调整Python路径")
    exit(1)

def plot_lightcurve(time, flux, title="光变曲线"):
    """
    绘制光变曲线
    
    参数：
        time: 时间数组
        flux: 通量数组
        title: 图表标题
    """
    plt.figure(figsize=(12, 6))
    plt.scatter(time, flux, s=1, alpha=0.7)
    plt.xlabel('时间 (BJD - 2454833.0)')
    plt.ylabel('归一化通量')
    plt.title(title)
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def plot_phase_folded(time, flux, period, title="折叠相位曲线"):
    """
    绘制折叠后的相位曲线
    
    参数：
        time: 时间数组
        flux: 通量数组
        period: 周期值
        title: 图表标题
    """
    # 计算相位
    phase = (time % period) / period
    
    # 排序相位和对应的通量
    sorted_indices = np.argsort(phase)
    phase_sorted = phase[sorted_indices]
    flux_sorted = flux[sorted_indices]
    
    # 绘制折叠曲线
    plt.figure(figsize=(10, 6))
    plt.scatter(phase_sorted, flux_sorted, s=1, alpha=0.7)
    plt.xlabel('相位')
    plt.ylabel('归一化通量')
    plt.title(f"{title} (周期 = {period:.6f} 天)")
    plt.grid(True, alpha=0.3)
    plt.tight_layout()
    plt.show()

def main():
    """
    主函数，展示完整的数据分析流程
    """
    print("=== 天文光变曲线分析示例 ===")
    
    # 1. 读取数据
    print("\n1. 读取FITS文件数据...")
    time, flux = get_sorted_data()
    
    if time is None or flux is None:
        print("无法读取数据，程序终止")
        return
    
    print(f"成功读取 {len(time)} 个数据点")
    
    # 2. 绘制原始光变曲线
    print("\n2. 绘制原始光变曲线...")
    plot_lightcurve(time, flux, "原始光变曲线")
    
    # 3. 计算最佳周期
    print("\n3. 计算光变曲线最佳周期...")
    best_period = period_culculator(time, flux, max_iterations=3, window_size=5)
    
    # 4. 绘制折叠相位曲线
    print("\n4. 绘制折叠相位曲线...")
    plot_phase_folded(time, flux, best_period, "最佳周期折叠相位曲线")
    
    print("\n分析完成！")
    print(f"最终确定的最佳周期为: {best_period:.8f} 天")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n程序被用户中断")
    except Exception as e:
        print(f"运行出错: {e}")
