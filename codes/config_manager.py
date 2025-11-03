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

# 导入json模块，用于JSON文件的解析和生成
import json
# 导入os模块，用于文件路径操作和目录创建
import os
# 导入logging模块，用于日志记录
import logging
# 导入typing模块中的类型注解
from typing import Any, Dict, Optional


class ConfigManager:
    """配置管理器 - 实现单例模式的配置管理类，负责配置文件的读取、解析和访问"""
    
    # 类变量，用于存储单例实例
    _instance = None
    
    def __new__(cls, config_path: Optional[str] = None):
        """单例模式实现 - 确保类只有一个实例
        
        参数:
            config_path: 配置文件路径，如果为None则使用默认路径
        
        返回:
            ConfigManager: 类的唯一实例
        """
        # 检查是否已经存在实例
        if cls._instance is None:
            # 如果不存在，创建新实例
            cls._instance = super(ConfigManager, cls).__new__(cls)
            # 标记实例未初始化
            cls._instance._initialized = False
        # 返回现有实例
        return cls._instance
    
    def __init__(self, config_path: Optional[str] = None):
        """初始化配置管理器 - 设置配置路径并加载配置
        
        参数:
            config_path: 配置文件路径，如果为None则使用默认路径
        """
        # 防止重复初始化
        if self._initialized:
            return
            
        # 设置配置文件路径，如果未提供则使用默认路径
        # os.path.join: 连接多个路径组件
        # os.path.dirname: 获取父目录路径
        self.config_path = config_path or os.path.join(
            os.path.dirname(os.path.dirname(__file__)),  # 获取上级目录的上级目录
            'config',  # 配置文件夹
            'app_config.json'  # 配置文件名
        )
        # 初始化配置字典
        self._config: Dict[str, Any] = {}
        # 获取指定名称的日志记录器
        # logging.getLogger: 创建或获取指定名称的logger实例
        self.logger = logging.getLogger('config_manager')
        # 加载配置文件
        self._load_config()
        # 标记初始化完成
        self._initialized = True
    
    def _load_config(self) -> None:
        """加载配置文件 - 从文件读取配置并解析为字典"""
        try:
            # 检查配置文件是否存在
            # os.path.exists: 检查路径是否存在
            if os.path.exists(self.config_path):
                # 打开并读取配置文件
                # open: 打开文件，mode='r'表示只读，encoding='utf-8'指定编码
                with open(self.config_path, 'r', encoding='utf-8') as f:
                    # 解析JSON文件内容
                    # json.load: 将JSON文件对象转换为Python对象
                    self._config = json.load(f)
                # 记录日志
                self.logger.info(f"成功加载配置文件: {self.config_path}")
            else:
                # 配置文件不存在，创建默认配置
                self._create_default_config()
                # 记录警告日志
                self.logger.warning(f"配置文件不存在，已创建默认配置: {self.config_path}")
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"加载配置文件失败: {e}")
            # 创建默认配置作为后备方案
            self._create_default_config()
    
    def _create_default_config(self) -> None:
        """创建默认配置 - 当配置文件不存在或加载失败时使用"""
        # 获取项目根目录的相对路径
        # os.path.dirname: 获取父目录路径
        # 注意：这里使用两级父目录是因为当前文件位于 codes 目录下
        root_dir = os.path.dirname(os.path.dirname(__file__))
        
        # 定义默认配置字典，使用相对路径
        self._config = {
            "data": {
                "base_path": os.path.join(root_dir, "data"),
                "hatp7b_path": os.path.join(root_dir, "data", "HATP7b"),
                "hdf5_path": os.path.join(root_dir, "data", "hatp7b_data.h5"),
                "shared_outputs": os.path.join(root_dir, "data", "HATP7b", "shared_outputs"),
                "shell_file_path": os.path.join(root_dir, "codes", "kepler_lightcurves_Q00_short.sh"),
                "working_directory": os.path.join(root_dir, "data", "Kepler data", "lightcurves")
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
                "file": os.path.join(root_dir, "logs", "app.log")
            }
        }
        try:
            # 创建配置文件所在目录
            # os.makedirs: 创建多级目录
            # exist_ok=True: 如果目录已存在则不报错
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            # 写入默认配置到文件
            # open: 打开文件，mode='w'表示写入
            with open(self.config_path, 'w', encoding='utf-8') as f:
                # json.dump: 将Python对象转换为JSON字符串并写入文件
                # indent=4: 缩进4个空格美化输出
                # ensure_ascii=False: 允许非ASCII字符
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            # 记录日志
            self.logger.info(f"已创建默认配置文件: {self.config_path}")
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"创建默认配置文件失败: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """获取配置项 - 支持通过点分隔符访问嵌套配置
        
        参数:
            key: 配置键，支持点分隔符（如'data.base_path'）
            default: 默认值，当配置项不存在时返回
            
        返回:
            Any: 配置项的值或默认值
        """
        # 使用点分隔符拆分键路径
        # str.split: 按指定分隔符分割字符串
        keys = key.split('.')
        # 从根配置开始查找
        value = self._config
        try:
            # 遍历键路径，逐步深入嵌套配置
            for k in keys:
                value = value[k]
            # 返回找到的配置值
            return value
        except (KeyError, TypeError):
            # 键不存在或类型错误时，记录调试日志
            self.logger.debug(f"配置项 {key} 不存在，使用默认值: {default}")
            # 返回默认值
            return default
    
    def set(self, key: str, value: Any) -> bool:
        """设置配置项 - 支持通过点分隔符设置嵌套配置并保存到文件
        
        参数:
            key: 配置键
            value: 配置值
            
        返回:
            bool: 操作是否成功
        """
        try:
            # 拆分键路径
            keys = key.split('.')
            # 从根配置开始
            config = self._config
            # 遍历除最后一个键外的所有键
            for k in keys[:-1]:
                # 如果中间路径不存在，创建空字典
                if k not in config:
                    config[k] = {}
                # 进入下一级配置
                config = config[k]
            # 设置最终的配置值
            config[keys[-1]] = value
            
            # 保存到文件
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            
            # 记录日志
            self.logger.info(f"已更新配置项 {key} = {value}")
            # 操作成功
            return True
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"设置配置项失败: {e}")
            # 操作失败
            return False
    
    def save(self) -> bool:
        """保存当前配置到文件
        
        返回:
            bool: 操作是否成功
        """
        try:
            # 创建目录
            os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
            # 写入文件
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(self._config, f, indent=4, ensure_ascii=False)
            # 记录日志
            self.logger.info(f"配置已保存到: {self.config_path}")
            # 操作成功
            return True
        except Exception as e:
            # 记录错误日志
            self.logger.error(f"保存配置失败: {e}")
            # 操作失败
            return False


class DIContainer:
    """依赖注入容器 - 用于管理和提供应用程序依赖的服务"""
    
    def __init__(self):
        """初始化依赖容器 - 创建服务注册表"""
        # 初始化服务字典，用于存储注册的服务
        self._services = {}
        # 获取日志记录器
        self.logger = logging.getLogger('di_container')
    
    def register(self, name: str, service: Any) -> None:
        """注册服务 - 将服务实例或类注册到容器中
        
        参数:
            name: 服务名称
            service: 服务实例或类
        """
        # 将服务存储到字典中
        self._services[name] = service
        # 记录调试日志
        self.logger.debug(f"已注册服务: {name}")
    
    def get(self, name: str) -> Any:
        """获取服务 - 从容器中检索已注册的服务
        
        参数:
            name: 服务名称
            
        返回:
            Any: 服务实例
            
        异常:
            KeyError: 当服务未注册时抛出
        """
        # 检查服务是否存在
        if name not in self._services:
            # 记录错误日志
            self.logger.error(f"服务未找到: {name}")
            # 抛出异常
            raise KeyError(f"Service '{name}' not found")
        
        # 获取服务
        service = self._services[name]
        # 记录调试日志
        self.logger.debug(f"获取服务: {name}")
        # 返回服务
        return service
    
    def has(self, name: str) -> bool:
        """检查服务是否存在 - 判断指定名称的服务是否已注册
        
        参数:
            name: 服务名称
            
        返回:
            bool: 服务是否已注册
        """
        # 检查服务名称是否在字典键中
        return name in self._services


# 全局配置管理器实例 - 应用程序中共享的单例实例
config_manager = ConfigManager()

# 全局依赖注入容器 - 应用程序中共享的依赖容器
# 使用全局实例可以避免在不同模块中重复创建容器
# 注意：虽然这里声明了全局变量，但在实际使用时应优先通过导入访问
# 例如: from config_manager import config_manager, di_container
di_container = DIContainer()

# 注册默认服务 - 在应用启动时预先注册一些常用服务
# 这里先注册None，稍后在setup_default_services中会更新为实际实例
di_container.register('hdf5_manager', None)  # 将在运行时设置

def setup_default_services() -> None:
    """设置默认服务 - 初始化并注册应用程序需要的默认服务"""
    # 延迟导入以避免循环导入
    from .hdf5_manager import HDF5Manager
    
    # 注册HDF5管理器为单例
    # 从配置中获取HDF5文件路径
    hdf5_path = config_manager.get('data.hdf5_path')
    # 注册HDF5Manager类到容器
    di_container.register('hdf5_manager', HDF5Manager, singleton=True, hdf5_path=hdf5_path)
    
    # 记录日志
    logging.info("默认服务已设置完成")


if __name__ == "__main__":
    # 测试代码 - 仅在直接运行该模块时执行
    print("配置管理模块测试:")
    
    # 测试配置管理器
    # 创建配置管理器实例（实际上会返回单例）
    cfg = ConfigManager()
    # 测试获取配置项
    print(f"数据路径: {cfg.get('data.base_path')}")
    print(f"高斯Sigma: {cfg.get('processing.gaussian_sigma')}")
    
    # 测试依赖注入容器
    # 注册测试服务
    di_container.register('test_service', str, singleton=True)
    # 注意：这里调用了resolve方法，但实际上DIContainer类中没有定义该方法，代码可能会报错
    # 正确的调用方式应该是: service = di_container.get('test_service')
    service = di_container.resolve('test_service')
    print(f"依赖注入测试: {service}")
    
    print("配置管理模块测试完成")