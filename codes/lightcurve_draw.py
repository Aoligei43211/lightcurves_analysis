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
        5. 定义固定的折叠周期（当前为18天）
        6. 对原始时间数据进行取模操作，实现时间折叠
        7. 获取折叠后时间的排序索引
        8. 按照排序索引重新排列折叠后的时间和对应的通量数据
    三、创建交互式绘图
        9. 创建绘图窗口并绘制折叠后的数据点
        10. 设置标题、坐标轴标签和网格线
        11. 创建交互式文本标签，用于显示数据点详情
    四、实现交互功能
        12. 实现鼠标悬停事件处理函数，显示数据点的详细信息
        13. 实现鼠标滚轮缩放事件处理函数，支持放大和缩小图表
        14. 连接事件处理函数到绘图窗口
        15. 显示绘图窗口
使用说明：
    - 程序会自动从HDF5文件加载数据
    - 鼠标悬停在数据点上可以查看详细信息
    - 使用鼠标滚轮可以缩放图表
    - 折叠周期可在period变量中修改
依赖包：
    - matplotlib
    - numpy
    - config_manager（配置管理模块）
    - hdf5_manager（HDF5数据管理模块）
'''

from matplotlib import pyplot as plt
import numpy as np
from config_manager import ConfigManager
from hdf5_manager import HDF5Manager

# **设置中文字体支持**
plt.rcParams["font.family"] = ["Microsoft YaHei"]  # 设置全局字体为微软雅黑，支持中文显示
plt.rcParams["axes.unicode_minus"] = False  # 解决负号显示问题

# 启用Matplotlib交互功能支持
plt.rcParams["figure.autolayout"] = True  # 自动调整布局，避免标签被截断

# 初始化配置管理器和HDF5管理器
config_manager = ConfigManager()
hdf5_path = config_manager.get('data.hdf5_file_path')
target_name = config_manager.get('data.hdf5_targets.default_target')
file_name = config_manager.get('data.hdf5_targets.default_file')

# 从HDF5文件获取数据
print("正在从HDF5文件获取处理后的数据...")
hdf5_manager = HDF5Manager(hdf5_path)
time, flux = hdf5_manager.read_preprocessed_data(target_name, file_name)

if time is None or flux is None:
    print("无法从HDF5文件读取数据，程序退出")
    exit()

print(f"成功获取数据：时间点数量 = {len(time)}, 通量数据数量 = {len(flux)}")

#绘制光变曲线
# 1. 获取数据
print("正在获取处理后的数据...")
# 注意：get_sorted_data会自动处理数据或从文件加载处理后的数据
time_sorted, flux_sorted = get_sorted_data()

# 2. 检查数据是否有效
if time_sorted is None or flux_sorted is None:
    print("无法获取有效数据，程序退出")
    exit()

#时间折叠 - 实现正确的时间折叠功能
# 参数说明：
# - period: 折叠周期，这里使用2.2天作为示例值
# - 时间折叠会将所有时间点对周期取模，然后按照折叠后的时间重新排序
# - 同时需要保持时间和通量数据的对应关系

# 定义折叠周期
period =18

# 执行时间折叠操作
# 1. 对原始时间数据进行取模操作
folded_time = np.mod(time_sorted, period)
# 2. 获取折叠后时间的排序索引
folded_indices = np.argsort(folded_time)
# 3. 按照排序索引重新排列折叠后的时间和对应的通量数据
folded_time_sorted = folded_time[folded_indices]
flux_sorted_folded = flux_sorted[folded_indices]

# 3. 创建交互式绘图
fig, ax = plt.subplots(figsize=(13, 7))
line, = ax.plot(folded_time_sorted, flux_sorted_folded, 'b.', markersize=1)  # 使用折叠后的数据绘图
ax.set_title("HATP7b 的连续光变曲线（鼠标悬停查看数据，周期折叠后）")
ax.set_xlabel(f"时间（以 {period} 天为周期取模后的值）")
ax.set_ylabel("校正后的光通量")
ax.grid(True, alpha=0.3)

# 添加交互文本标签
annot = ax.annotate('', xy=(0, 0), xytext=(20, 20), textcoords="offset points",
                    bbox=dict(boxstyle="round,pad=0.5", fc="yellow", alpha=0.7),
                    arrowprops=dict(arrowstyle="->", connectionstyle="arc3,rad=0"))
annot.set_visible(False)

# 鼠标移动事件处理函数
def update_annot(ind):
    # 直接从事件和数据中获取信息，不依赖Line2D的get_paths方法
    index = ind["ind"][0]  # 获取索引
    x = folded_time_sorted[index]  # 获取折叠后的时间值
    y = flux_sorted_folded[index]  # 获取对应的通量值
    annot.xy = (x, y)  # 设置注释位置
    
    # 格式化显示信息，同时显示折叠后的时间和原始时间
    original_index = folded_indices[index]  # 找到原始数据中的索引
    original_time = time_sorted[original_index]  # 获取原始时间值
    text = f"折叠后时间: {x:.6f}\n原始时间: {original_time:.6f}\n通量: {y:.6f}"
    annot.set_text(text)
    annot.get_bbox_patch().set_alpha(0.7)

# 鼠标移动事件回调
def hover(event):
    vis = annot.get_visible()
    if event.inaxes == ax:
        # 使用数据数组直接判断最近点
        # 计算鼠标位置到所有数据点的距离
        distances = np.sqrt((folded_time_sorted - event.xdata)**2 + (flux_sorted_folded - event.ydata)** 2)
        min_dist_index = np.argmin(distances)
        
        # 设置一个阈值，只有当距离足够小时才显示注释
        if distances[min_dist_index] < 0.1:  # 阈值可以根据数据尺度调整
            # 创建一个假的索引字典，格式与line.contains()返回的一致
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
    
    # 计算当前视图的中心点（而不是鼠标位置）
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
    
    # 计算新的x轴限制
    new_width = (cur_xlim[1] - cur_xlim[0]) * scale_x
    new_height = (cur_ylim[1] - cur_ylim[0]) * scale_y
    
    # 使用当前视图中心点作为缩放中心
    new_x_center = x_center
    new_y_center = y_center
    
    # 设置新的轴限制
    ax.set_xlim([new_x_center - new_width/2, new_x_center + new_width/2])
    ax.set_ylim([new_y_center - new_height/2, new_y_center + new_height/2])
    
    # 重新绘制画布
    fig.canvas.draw_idle()

# 连接事件
fig.canvas.mpl_connect("motion_notify_event", hover)
fig.canvas.mpl_connect("scroll_event", on_scroll)

print(f"绘图已创建。使用周期 {period} 天进行了时间折叠。")
print("请将鼠标悬停在数据点上查看详细信息，使用鼠标滚轮进行缩放。")
plt.show()