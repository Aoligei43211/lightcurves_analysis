import h5py
import numpy as np

# 打开HDF5文件并检查结构
hdf5_path = "d:/program/Python/projects/astronomy/data/hatp7b_data.h5"
print(f"检查HDF5文件结构: {hdf5_path}")

try:
    with h5py.File(hdf5_path, 'r') as f:
        print("\nHDF5文件顶层结构:")
        print(list(f.keys()))
        
        # 检查HATP7b组
        if 'HATP7b' in f:
            print("\nHATP7b组内容:")
            print(list(f['HATP7b'].keys()))
            
            # 检查processed_combined组
            if 'processed_combined' in f['HATP7b']:
                print("\nprocessed_combined组内容:")
                print(list(f['HATP7b/processed_combined'].keys()))
                
                # 检查processed组
                if 'processed' in f['HATP7b/processed_combined']:
                    print("\nprocessed组内容:")
                    processed_group = f['HATP7b/processed_combined/processed']
                    print(list(processed_group.keys()))
                    
                    # 检查periodogram数据集
                    if 'periodogram' in processed_group:
                        print("\nperiodogram数据集信息:")
                        periodogram = processed_group['periodogram']
                        print(f"形状: {periodogram.shape}")
                        print(f"属性: {dict(periodogram.attrs)}")
                        print(f"前5行数据: {periodogram[:5]}")
                    
                    # 检查denoised_flux数据集
                    if 'denoised_flux' in processed_group:
                        print("\ndenoisied_flux数据集信息:")
                        denoised_flux = processed_group['denoised_flux']
                        print(f"形状: {denoised_flux.shape}")
                        print(f"属性: {dict(denoised_flux.attrs)}")
                        print(f"前5个数据点: {denoised_flux[:5]}")
        
        # 检查comprehensive组（如果存在）
        if 'HATP7b' in f and 'comprehensive' in f['HATP7b']:
            print("\ncomprehensive组内容:")
            print(list(f['HATP7b/comprehensive'].keys()))
            
            if 'analysis_results' in f['HATP7b/comprehensive']:
                print("\nanalysis_results组内容:")
                print(list(f['HATP7b/comprehensive/analysis_results'].keys()))
                
                if 'periodogram' in f['HATP7b/comprehensive/analysis_results']:
                    print("\ncomprehensive/analysis_results/periodogram数据集信息:")
                    periodogram = f['HATP7b/comprehensive/analysis_results/periodogram']
                    print(f"形状: {periodogram.shape}")
                    print(f"属性: {dict(periodogram.attrs)}")
                    
                if 'best_period' in f['HATP7b/comprehensive/analysis_results']:
                    print("\ncomprehensive/analysis_results/best_period数据集信息:")
                    best_period = f['HATP7b/comprehensive/analysis_results/best_period']
                    print(f"值: {best_period[0]}")
                    print(f"属性: {dict(best_period.attrs)}")
                    
    print("\nHDF5文件结构检查完成")
    
except Exception as e:
    print(f"\n检查HDF5文件结构时出错: {e}")
    import traceback
    traceback.print_exc()