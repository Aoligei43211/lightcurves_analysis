from astropy.io import fits
'''FITS文件头信息读取器
实现功能：
    1. 遍历指定文件夹中的所有FITS文件
    2. 详细打印每个FITS文件的头文件信息
    3. 展示每个HDU(Header Data Unit)的关键字、注释和数据结构信息
    4. 处理异常情况，确保程序稳定运行
实现过程细节：
    1. 检查指定文件夹是否存在
    2. 使用glob模块获取所有.fits扩展名的文件
    3. 对每个FITS文件，使用astropy.io.fits模块打开并读取
    4. 遍历每个HDU，提取并格式化显示关键字、值和注释
    5. 单独处理COMMENT和HISTORY类型的关键字
    6. 显示数据HDU的基本信息，包括数据类型、形状和列信息
    7. 实现错误处理机制，确保单个文件错误不影响整体处理流程
使用说明：
    - 默认文件夹路径可在default_folder变量中设置
    - 可以直接调用print_fits_headers函数并传入自定义文件夹路径
依赖包：
    - astropy.io.fits
    - os
    - glob
'''

from astropy.io import fits
import os
from glob import glob
from config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 从配置管理器获取文件夹路径
default_folder = config_manager.get('data.hatp7b_path') 

def print_fits_headers(folder_path):
    """
    从指定文件夹读取所有FITS文件，并详细打印每个文件的头文件信息
    
    参数:
        folder_path: 包含FITS文件的文件夹路径
    """
    try:
        # 确保文件夹存在
        if not os.path.exists(folder_path):
            print(f"错误: 文件夹不存在 - {folder_path}")
            return
            
        # 获取文件夹中所有FITS文件
        fits_files = glob(os.path.join(folder_path, '*.fits'))
        
        if not fits_files:
            print(f"错误: 在 {folder_path} 中未找到FITS文件")
            return
            
        print(f"找到 {len(fits_files)} 个FITS文件\n")
        
        # 处理每个FITS文件
        for file_path in fits_files:
            try:
                print("="*80)
                print(f"处理文件: {os.path.basename(file_path)}")
                print("="*80)
                
                # 打开FITS文件并读取头文件
                with fits.open(file_path) as hdul:
                    print(f"FITS文件包含 {len(hdul)} 个HDU(Header Data Unit):")
                    
                    # 遍历每个HDU并打印其头文件信息
                    for i, hdu in enumerate(hdul):
                        print(f"\nHDU #{i}: {hdu.__class__.__name__}")
                        print("-"*60)
                        
                        # 获取并打印头文件信息
                        header = hdu.header
                        
                        # 计算关键字最大长度，用于对齐输出
                        max_key_len = 0
                        for key in header.keys():
                            if key != 'COMMENT' and key != 'HISTORY':
                                max_key_len = max(max_key_len, len(key))
                        
                        # 打印标准关键字
                        for key in header.keys():
                            # 跳过COMMENT和HISTORY，它们通常有多个条目
                            if key == 'COMMENT' or key == 'HISTORY':
                                continue
                            
                            try:
                                value = header[key]
                                comment = header.comments[key]
                                # 格式化输出，使对齐更美观
                                print(f"{{key:<{max_key_len}}} = {{value}}  / {{comment}}")
                            except Exception as e:
                                print(f"  错误读取关键字 {key}: {str(e)}")
                        
                        # 单独处理COMMENT和HISTORY
                        if 'COMMENT' in header:
                            print("\nCOMMENTS:")
                            for comment in header['COMMENT']:
                                print(f"  {comment}")
                        
                        if 'HISTORY' in header:
                            print("\nHISTORY:")
                            for history in header['HISTORY']:
                                print(f"  {history}")
                        
                        # 如果是数据HDU，显示数据的基本信息
                        if hasattr(hdu, 'data') and hdu.data is not None:
                            print(f"\n数据信息:")
                            print(f"  数据类型: {hdu.data.dtype}")
                            print(f"  数据形状: {hdu.data.shape}")
                            
                            # 如果数据有列结构，显示列信息
                            if hasattr(hdu.data, 'columns'):
                                print(f"  列数量: {len(hdu.data.columns)}")
                                print("  列名: {}".format(", ".join(hdu.data.columns.names)))
                        
            except Exception as e:
                print(f"处理文件 {file_path} 时出错: {str(e)}")
                import traceback
                traceback.print_exc()
        
        print(f"\n所有 {len(fits_files)} 个FITS文件处理完成。")
    except Exception as e:
        print(f"程序执行错误: {str(e)}")
        import traceback
        traceback.print_exc()

# 执行函数
if __name__ == "__main__":
    # 可以选择让用户输入文件夹路径，或使用默认路径
    print("FITS文件头信息查看器")
    print("="*50)
    print(f"将使用默认文件夹: {default_folder}")
    print("如果需要指定其他文件夹，请修改代码中的default_folder变量")
    print("="*50)
    
    print_fits_headers(default_folder)