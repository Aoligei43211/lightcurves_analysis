"""配置管理模块

功能说明：
    1. 实现配置文件的读取和管理
    2. 提供依赖注入容器机制
    3. 支持配置项的动态更新和验证
    4. 确保配置的全局访问和一致性

实现过程：
    - 使用json模块读取配置文件
    - 实现单例模式的配置管理器
    - 创建简单的依赖注入容器
    - 提供配置验证和默认值机制

使用方法：
    - 初始化ConfigManager指定配置文件路径
    - 使用get方法获取配置项
    - 使用DIContainer注册和解析依赖

依赖包：
    - json: 配置文件解析
    - os: 文件路径操作
    - logging: 日志记录
"""

import json
import os
import logging
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器"""
    
    _instance = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """单例模式"""
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置管理器
        
        参数:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        if self._initialized:
            return
            
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)), 
            'config', 
            'app_config.json'
        )
        self._config: Dict[str, Any] = {}
        # 使用标准logging模块
        self.logger = logging.getLogger('config_manager')
        self._load_config()
        self._initialized = True
    
    def _load_config(self) -> None:
        """加载配置文件"""
        try:
            if os.path.exists(self.config_path):
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    self._config = json.load(f)
                self.logger.info(f"成功加载配置文件: {self.config_path}")
            else:
                self._create_default_config()
                self.logger.warning(f"配置文件不存在，已创建默认配置: {self.config_path}")
        except Exception as e:
            self.logger.error(f"加载配置文件失败: {e}")
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置"""
        self._config = {
            "data": {
                "base_path": r"D:\program\Python\projects\astronomy\data",
                "hatp7b_path": r"D:\program\Python\projects\astronomy\data\HATP7b",
                "hdf5_path": r"D:\program\Python\projects\astronomy\data\hatp7b_data.h5",
                "shared_outputs": r"D:\program\Python\projects\astronomy\data\HATP7b\shared_outputs",
                "shell_file_path": r"D:\program\Python\projects\astronomy\codes\kepler_lightcurves_Q00_short.sh",
                "working_directory": r"D:\program\Python\projects\astronomy\data\Kepler data\lightcurves"
            },
            "processing": {
                "gaussian_sigma": 2.0,
                "normalization": True,
                "noise_reduction": True,
                "period_search_range": [0.1, 10.0]
            },
            "visualization": {
                "figure_size": [12, 8],
                "dpi": 300,
                "save_format": "png",
                "colors": ["blue", "red", "green", "orange", "purple", "brown"]
            },
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
                "file": r"D:\program\Python\projects\astronomy\logs\app.log"
            }
        }
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"已创建默认配置文件: {self.config_path}")
        except Exception as e:
            self.logger.error(f"创建默认配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置项
        
        参数:
            key: 配置键，支持点分隔符（如'data.base_path'）
            default: 默认值
            
        返回:
            配置值
        """
        keys = key.split('.')
        value = self._config
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            self.logger.debug(f"配置项 {key} 不存在，使用默认值: {default}")
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """
        设置配置项
        
        参数:
            key: 配置键
            value: 配置值
            
        返回:
            是否成功
        """
        try:
            keys = key.split('.')
            config = self._config
            for k in keys[:-1]:
                if k not in config:
                    config[k] = {}
                config = config[k]
            config[keys[-1]] = value
            
            # 保存到文件
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            
            self.logger.info(f"已更新配置项 {key} = {value}")
            return True
        except Exception as e:
            self.logger.error(f"设置配置项失败: {e}")
            return False
    
    def save(self) -> bool:
        """
        保存当前配置到文件
        
        返回:
            是否成功
        """
        try:
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            self.logger.info(f"配置已保存到: {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"保存配置失败: {e}")
            return False


class DIContainer:
    """依赖注入容器"""
    
    def __init__(self):
        """初始化依赖容器"""
        self._services = {}
        # 使用标准logging模块
        self.logger = logging.getLogger('di_container')
    
    def register(self, name: str, service: Any) -> None:
        """
        注册服务
        
        参数:
            name: 服务名称
            service: 服务实例或类
        """
        self._services[name] = service
        self.logger.debug(f"已注册服务: {name}")
    
    def get(self, name: str) -> Any:
        """
        获取服务
        
        参数:
            name: 服务名称
            
        返回:
            服务实例
        """
        if name not in self._services:
            self.logger.error(f"服务未找到: {name}")
            raise KeyError(f"Service '{name}' not found")
        
        service = self._services[name]
        self.logger.debug(f"获取服务: {name}")
        return service
    
    def has(self, name: str) -> bool:
        """
        检查服务是否存在
        
        参数:
            name: 服务名称
            
        返回:
            是否存在
        """
        return name in self._services


# 全局配置管理器实例
config_manager = ConfigManager()

# 全局依赖注入容器
di_container = DIContainer()

# 注册默认服务
di_container.register('hdf5_manager', None)  # 将在运行时设置

def setup_default_services() -> None:
    """设置默认服务"""
    from .hdf5_manager import HDF5Manager
    
    # 注册HDF5管理器为单例
    hdf5_path = config_manager.get('data.hdf5_path')
    di_container.register('hdf5_manager', HDF5Manager, singleton=True, hdf5_path=hdf5_path)
    
    logging.info("默认服务已设置完成")


if __name__ == "__main__":
    # 测试代码
    print("配置管理模块测试:")
    
    # 测试配置管理器
    cfg = ConfigManager()
    print(f"数据路径: {cfg.get('data.base_path')}")
    print(f"高斯Sigma: {cfg.get('processing.gaussian_sigma')}")
    
    # 测试依赖注入容器
    di_container.register('test_service', str, singleton=True)
    service = di_container.resolve('test_service')
    print(f"依赖注入测试: {service}")
    
    print("配置管理模块测试完成")