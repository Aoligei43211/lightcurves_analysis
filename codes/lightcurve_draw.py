'''交互式光变曲线绘制器
实现功能：
    1. 从HDF5文件获取处理后的数据并绘制光变曲线
    2. 支持时间折叠功能，将时间数据以指定周期进行折叠
    3. 提供交互式体验，包括鼠标悬停查看数据点详情和鼠标滚轮缩放功能
    4. 显示折叠后的时间和对应的原始时间信息
实现过程细节及原理：
    一、数据获取与设置
        1. 设置中文字体支持，确保中文显示正常
        2. 启用Matplotlib交互功能
        3. 从HDF5文件中获取处理后的数据
        4. 检查数据是否有效，无效则退出程序
    二、时间折叠处理
        5. 从HDF5文件读取计算出的周期值
        6. 询问用户是否进行时间折叠
        7. 对原始时间数据进行取模操作，实现时间折叠
        8. 获取折叠后时间的排序索引
        9. 按照排序索引重新排列折叠后的时间和对应的通量数据
    三、创建交互式绘图
        10. 创建绘图窗口并绘制数据点
        11. 设置标题、坐标轴标签和网格线
        12. 创建交互式文本标签，用于显示数据点详情
    四、实现交互功能
        13. 实现鼠标悬停事件处理函数，显示数据点的详细信息
        14. 实现鼠标滚轮缩放事件处理函数，支持放大和缩小图表
        15. 连接事件处理函数到绘图窗口
        16. 显示绘图窗口
使用说明：
    - 程序会自动从HDF5文件加载数据
    - 程序会询问是否进行时间折叠
    - 鼠标悬停在数据点上可以查看详细信息
    - 使用鼠标滚轮可以缩放图表
依赖包：
    - matplotlib
    - numpy
    - h5py
    - config_manager（配置管理模块）
'''

from matplotlib import pyplot as plt
import numpy as np
import h5py
import os
import argparse
from config_manager import ConfigManager

# **设置中文字体支持**
plt.rcParams["font.family"] = ["Microsoft YaHei"]  # 设置全局字体为微软雅黑，支持中文显示
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 启用Matplotlib交互功能支持
plt.rcParams["figure.autolayout"] = True  # 自动调整布局，避免标签被截断

# 初始化配置管理器
config_manager = ConfigManager()
hdf5_relative_path = config_manager.get('data.hdf5_path')
# 构建绝对路径
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
hdf5_path = os.path.join(project_root, hdf5_relative_path.lstrip('./'))
target_name = config_manager.get('data.hdf5_targets.default_target')
file_name = config_manager.get('data.hdf5_targets.default_file')  # 使用默认的批处理文件名

# 从HDF5文件获取数据
print("正在从HDF5文件获取数据...")
print(f"HDF5文件路径: {hdf5_path}")
print(f"目标组路径: {target_name}/{file_name}")

try:
    # 构建目标组路径
    group_path = f'{target_name}/{file_name}'
    
    with h5py.File(hdf5_path, 'r') as f:
        # 检查目标组是否存在
        if group_path not in f:
            raise ValueError(f"目标组 {group_path} 在HDF5文件中不存在")
        
        # 从同一个组中读取time和flux数据
        # 尝试读取预处理的time数据
        if 'preprocessed/time' in f[group_path]:
            time_data = f[f'{group_path}/preprocessed/time'][:]
        else:
            # 如果没有预处理的time，则尝试读取processed下的time
            if 'processed/processed_time' in f[group_path]:
                time_data = f[f'{group_path}/processed/processed_time'][:]
            else:
                raise ValueError(f"在组 {group_path} 中未找到time数据")
        
        # 尝试读取处理后的flux数据
        if 'processed/denoised_flux' in f[group_path]:
            flux_data = f[f'{group_path}/processed/denoised_flux'][:]
        else:
            # 如果没有denoised_flux，则尝试读取flux_data
            if 'processed/processed_flux' in f[group_path]:
                flux_data = f[f'{group_path}/processed/processed_flux'][:]
            else:
                raise ValueError(f"在组 {group_path} 中未找到flux数据")
        
        # 尝试从同一个组中读取period值（从periodogram的属性中）
        period_value = None
        if 'processed/periodogram' in f[group_path]:
            period_ds = f[f'{group_path}/processed/periodogram']
            if 'best_period' in period_ds.attrs:
                period_value = period_ds.attrs['best_period']
                print(f"成功读取计算出的周期值: {period_value:.10f}")
        
        # 临时测试：如果没有找到周期值，设置一个默认值用于测试
        if period_value is None:
            period_value = 2.20473  # 为了测试交互功能，临时设置一个周期值
            print(f"测试模式：设置默认周期值: {period_value:.10f}")
        
    print(f"成功获取数据：时间点数量 = {len(time_data)}, 通量数据数量 = {len(flux_data)}")
    
    # 对数据进行按时间排序
    sort_indices = np.argsort(time_data)
    time_sorted = time_data[sort_indices]
    flux_sorted = flux_data[sort_indices]
    
except Exception as e:
    print(f"从HDF5文件读取数据时出错: {e}")
    exit()

# 检查数据是否有效
if time_sorted is None or flux_sorted is None or len(time_sorted) == 0 or len(flux_sorted) == 0:
    print("无法获取有效数据，程序退出")
    exit()

# 添加命令行参数解析
parser = argparse.ArgumentParser(description='交互式光变曲线绘制器')
parser.add_argument('--fold', action='store_true', help='自动进行周期折叠，无需用户确认')
parser.add_argument('--no-fold', action='store_true', help='自动不进行周期折叠，无需用户确认')
args = parser.parse_args()

# 询问用户是否进行时间折叠
fold_data = False
period = None

# 优先使用命令行参数
if args.fold:
    if period_value is not None:
        fold_data = True
        period = period_value
        print(f"通过命令行参数指定：使用周期值 {period_value:.6f} 天进行时间折叠")
    else:
        print("通过命令行参数指定进行折叠，但未找到计算出的周期值")
elif args.no_fold:
    print("通过命令行参数指定：不进行时间折叠")
else:
    # 没有命令行参数时，尝试交互式输入
    try:
        if period_value is not None:
            user_input = input(f"已从HDF5文件读取计算出的周期值: {period_value:.6f} 天。是否进行时间折叠？(y/n): ").strip().lower()
            if user_input in ('y', 'yes'):
                fold_data = True
                period = period_value
            else:
                print("不进行时间折叠，将直接绘制原始时间序列。")
        else:
            print("未找到计算出的周期值，将直接绘制原始时间序列。")
    except (EOFError, KeyboardInterrupt):
        # 处理非交互式环境或用户中断
        print("\n在非交互式环境中运行，默认不进行时间折叠")

# 执行时间折叠（如果用户选择的话）
if fold_data and period is not None:
    print(f"正在使用周期 {period} 天进行时间折叠...")
    # 执行时间折叠操作
    folded_time = np.mod(time_sorted, period)
    folded_indices = np.argsort(folded_time)
    
    # 按照排序索引重新排列折叠后的时间和对应的通量数据
    x_data = folded_time[folded_indices]
    y_data = flux_sorted[folded_indices]
    
    # 保存原始索引用于显示原始时间
    original_indices = folded_indices
else:
    # 不进行折叠，使用原始数据
    x_data = time_sorted
    y_data = flux_sorted
    original_indices = np.arange(len(time_sorted))

# 创建交互式绘图
fig, ax = plt.subplots(figsize=(13, 7))
line, = ax.plot(x_data, y_data, 'b.', markersize=1)  # 绘制数据点

# 设置标题和标签
if fold_data and period is not None:
    ax.set_title(f"HATP7b 的光变曲线（周期折叠后，周期={period:.6f}天）")
    ax.set_xlabel(f"时间（以 {period:.6f} 天为周期取模后的值）")
else:
    ax.set_title("HATP7b 的光变曲线（原始时间序列）")
    ax.set_xlabel("原始时间")

ax.set_ylabel("光通量")
ax.grid(True, alpha=0.3)

# 添加交互文本标签
annot = ax.annotate('', xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.7),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
annot.set_visible(False)

# 鼠标移动事件处理函数
def update_annot(ind):
    # 直接从事件和数据中获取信息
    index = ind["ind"][0]  # 获取索引
    x = x_data[index]  # 获取x值
    y = y_data[index]  # 获取对应的y值
    annot.xy = (x, y)  # 设置注释位置
    
    # 格式化显示信息
    original_index = original_indices[index]  # 找到原始数据中的索引
    original_time = time_sorted[original_index]  # 获取原始时间值
    
    if fold_data and period is not None:
        text = f"折叠后时间: {x:.6f}\n原始时间: {original_time:.6f}\n通量: {y:.6f}"
    else:
        text = f"时间: {x:.6f}\n通量: {y:.6f}"
    
    annot.set_text(text)
    annot.get_bbox_patch().set_alpha(0.7)

# 鼠标移动事件回调
def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        # 使用数据数组直接判断最近点
        distances = np.sqrt((x_data - event.xdata)**2 + (y_data - event.ydata)**2)
        min_dist_index = np.argmin(distances)
        
        # 设置一个阈值，只有当距离足够小时才显示注释
        if distances[min_dist_index] < 0.1:  # 阈值可以根据数据尺度调整
            ind = {"ind": [min_dist_index]}
            update_annot(ind)
            annot.set_visible(True)
            fig.canvas.draw_idle()
        else:
            if vis:
                annot.set_visible(False)
                fig.canvas.draw_idle()

# 鼠标滚轮缩放事件处理函数
def on_scroll(event):
    # 获取当前x和y轴的限制
    cur_xlim = ax.get_xlim()
    cur_ylim = ax.get_ylim()
    
    # 计算当前视图的中心点
    x_center = (cur_xlim[0] + cur_xlim[1]) / 2
    y_center = (cur_ylim[0] + cur_ylim[1]) / 2
    
    # 计算缩放因子
    scale_factor = 1.1
    if event.button == 'up':
        # 滚轮向上，放大图表
        scale_x = 1 / scale_factor
        scale_y = 1 / scale_factor
    else:
        # 滚轮向下，缩小图表
        scale_x = scale_factor
        scale_y = scale_factor
    
    # 计算新的轴限制
    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_x
    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_y
    
    ax.set_xlim([x_center - new_width/2, x_center + new_width/2])
    ax.set_ylim([y_center - new_height/2, y_center + new_height/2])
    
    # 重新绘制画布
    fig.canvas.draw_idle()

# 连接事件
fig.canvas.mpl_connect("motion_notify_event", hover)
fig.canvas.mpl_connect("scroll_event", on_scroll)

print(f"绘图已创建。{'使用周期 ' + str(period) + ' 天进行了时间折叠' if fold_data and period is not None else '未进行时间折叠'}")
print("请将鼠标悬停在数据点上查看详细信息，使用鼠标滚轮进行缩放。")
plt.show()