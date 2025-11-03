"""结构化日志系统配置模块

功能说明：
    1. 提供统一的日志配置和管理
    2. 支持多级别日志记录和输出
    3. 集成到所有模块中实现结构化日志
    4. 支持文件和控制台双重输出

实现过程：
    - 创建日志配置类
    - 设置日志格式和处理器
    - 提供全局日志初始化接口
    - 支持动态日志级别调整

使用方法：
    - 在模块中导入并使用get_logger
    - 在程序启动时调用setup_logging
    - 通过配置管理器调整日志级别

依赖包：
    - logging: Python标准日志库
    - os: 文件路径操作
    - datetime: 时间处理
"""

import logging
import os
from datetime import datetime
from typing import Optional


class LoggingConfig:
    """日志配置类"""
    
    def __init__(self):
        # 延迟导入config_manager以避免循环导入
        from config_manager import config_manager
        self.config_manager = config_manager
        
        # 从配置获取日志参数
        self.log_level = self.config_manager.get('logging.level')
        self.log_format = self.config_manager.get('logging.format')
        self.date_format = self.config_manager.get('logging.date_format')
        self.log_dir = self.config_manager.get('logging.directory')
        self.max_file_size = self.config_manager.get('logging.max_file_size')
        self.backup_count = self.config_manager.get('logging.backup_count')
        
        # 确保日志目录存在
        os.makedirs(self.log_dir, exist_ok=True)
    
    def get_log_level(self) -> int:
        """
        获取日志级别
        
        返回:
            日志级别数值
        """
        level_mapping = {
            'DEBUG': logging.DEBUG,
            'INFO': logging.INFO,
            'WARNING': logging.WARNING,
            'ERROR': logging.ERROR,
            'CRITICAL': logging.CRITICAL
        }
        return level_mapping.get(self.log_level.upper(), logging.INFO)
    
    def setup_logging(self, 
                     module_name: Optional[str] = None,
                     log_file: Optional[str] = None) -> logging.Logger:
        """
        设置日志记录器
        
        参数:
            module_name: 模块名称
            log_file: 日志文件路径
            
        返回:
            配置好的日志记录器
        """
        # 创建记录器
        logger_name = module_name or 'astronomy'
        logger = logging.getLogger(logger_name)
        logger.setLevel(self.get_log_level())
        
        # 清除现有处理器，避免重复
        logger.handlers.clear()
        
        # 创建格式化器
        formatter = logging.Formatter(self.log_format, self.date_format)
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self.get_log_level())
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)
        
        # 文件处理器
        if log_file:
            file_path = os.path.join(self.log_dir, log_file)
        else:
            # 默认日志文件名
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            file_path = os.path.join(self.log_dir, f'astronomy_{timestamp}.log')
        
        file_handler = logging.FileHandler(file_path, encoding='utf-8')
        file_handler.setLevel(self.get_log_level())
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        
        # 避免日志传播到根记录器
        logger.propagate = False
        
        return logger
    
    def update_log_level(self, new_level: str) -> bool:
        """
        动态更新日志级别
        
        参数:
            new_level: 新的日志级别
            
        返回:
            更新是否成功
        """
        valid_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        if new_level.upper() not in valid_levels:
            return False
        
        self.log_level = new_level.upper()
        
        # 更新配置管理器中的值
        self.config_manager.set('logging.level', new_level.upper())
        
        # 更新所有现有记录器的级别
        for logger_name in logging.Logger.manager.loggerDict:
            logger = logging.getLogger(logger_name)
            logger.setLevel(self.get_log_level())
            
            # 更新所有处理器的级别
            for handler in logger.handlers:
                handler.setLevel(self.get_log_level())
        
        return True


# 全局日志配置实例
logging_config = LoggingConfig()


def get_logger(module_name: Optional[str] = None) -> logging.Logger:
    """
    获取配置好的日志记录器
    
    参数:
        module_name: 模块名称
        
    返回:
        配置好的日志记录器
    """
    return logging_config.setup_logging(module_name)


def setup_global_logging() -> None:
    """
    设置全局日志配置
    """
    # 设置根日志记录器
    root_logger = logging.getLogger()
    root_logger.setLevel(logging_config.get_log_level())
    
    # 清除现有处理器
    root_logger.handlers.clear()
    
    # 创建格式化器
    formatter = logging.Formatter(
        logging_config.log_format, 
        logging_config.date_format
    )
    
    # 控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging_config.get_log_level())
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)
    
    # 文件处理器
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = f'astronomy_global_{timestamp}.log'
    file_path = os.path.join(logging_config.log_dir, log_file)
    
    file_handler = logging.FileHandler(file_path, encoding='utf-8')
    file_handler.setLevel(logging_config.get_log_level())
    file_handler.setFormatter(formatter)
    root_logger.addHandler(file_handler)
    
    print(f"全局日志系统已初始化，日志文件: {file_path}")


def log_function_call(func):
    """
    函数调用日志装饰器
    
    参数:
        func: 被装饰的函数
        
    返回:
        包装后的函数
    """
    def wrapper(*args, **kwargs):
        logger = get_logger(func.__module__)
        
        # 记录函数调用
        logger.debug(f"调用函数: {func.__name__}, 参数: args={args}, kwargs={kwargs}")
        
        try:
            result = func(*args, **kwargs)
            logger.debug(f"函数 {func.__name__} 执行成功，返回值: {result}")
            return result
        except Exception as e:
            logger.error(f"函数 {func.__name__} 执行失败: {e}", exc_info=True)
            raise
    
    return wrapper


def log_class_methods(cls):
    """
    类方法日志装饰器
    
    参数:
        cls: 被装饰的类
        
    返回:
        包装后的类
    """
    for attr_name, attr_value in cls.__dict__.items():
        if callable(attr_value) and not attr_name.startswith('_'):
            setattr(cls, attr_name, log_function_call(attr_value))
    return cls


if __name__ == "__main__":
    # 测试代码
    setup_global_logging()
    
    # 测试不同模块的日志记录
    data_logger = get_logger('data_layer')
    processing_logger = get_logger('processing_core')
    visualization_logger = get_logger('visualization_app')
    
    # 测试日志级别
    data_logger.debug("这是调试信息")
    data_logger.info("这是信息消息")
    data_logger.warning("这是警告信息")
    data_logger.error("这是错误信息")
    
    processing_logger.info("处理层日志测试")
    visualization_logger.info("可视化层日志测试")
    
    # 测试动态更新日志级别
    logging_config.update_log_level('DEBUG')
    data_logger.debug("调试级别已启用，这条消息应该可见")
    
    print("日志系统测试完成")