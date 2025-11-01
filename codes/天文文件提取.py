import os
'''此脚本用于从shell文件中读取curl命令并执行天文数据文件的下载。

实现功能：
1. 从指定的shell文件中读取curl下载命令
2. 执行下载命令并支持重试机制
3. 自动检查curl命令是否可用
4. 提供详细的日志记录（同时输出到控制台和文件）
5. 支持配置参数集中管理

实现过程：
1. 配置下载参数：最大重试次数、重试延迟时间、超时时间、shell文件路径、工作目录
2. 配置日志系统：设置日志级别、格式、输出目标（文件和控制台）
3. 实现下载函数：读取shell文件中的curl命令，逐行处理并执行
4. 实现命令处理函数：清理命令行、拆分命令、替换不兼容选项、执行命令并处理异常
5. 添加重试机制：在命令执行失败时根据配置进行重试
6. 实现主函数：检查curl是否可用，然后调用下载函数执行下载

配置参数说明：
- MAX_RETRIES: 命令执行失败时的最大重试次数
- RETRY_DELAY: 两次重试之间的延迟时间（秒）
- TIMEOUT: 命令执行的超时时间（秒）
- SHELL_FILE: 包含curl命令的shell文件路径
- WORKING_DIRECTORY: 下载文件的保存目录

使用说明：
- 在使用前，请确保curl已安装并添加到系统PATH中
- 确保shell文件中的curl命令都以单行形式书写
- 需要修改下载配置时，直接调整文件顶部的配置参数区域即可

依赖包：
- subprocess: 用于执行外部命令
- shlex: 用于解析命令行字符串
- time: 用于设置重试延迟
- logging: 用于日志记录
'''

import os
import subprocess
import shlex
import time
import logging
from subprocess import CalledProcessError
from config_manager import ConfigManager

# 初始化配置管理器
config_manager = ConfigManager()

# 配置参数
MAX_RETRIES = 3
RETRY_DELAY = 5  # 重试延迟时间(秒)
TIMEOUT = 60  # 超时时间(秒)
SHELL_FILE = config_manager.get('data.shell_file_path')  
WORKING_DIRECTORY = config_manager.get('data.working_directory')#‘r’让转义字符不转义

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('download.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

def download_files_from_shell(shell_file_path):
    """
    从指定的shell文件中读取curl命令并下载文件
    :param shell_file_path: shell文件路径
    """
    # 检查shell文件是否存在
    if not os.path.exists(shell_file_path):
        logger.error(f"找不到shell文件 {shell_file_path}")
        return False

    # 读取 shell 文件中的所有 curl 命令
    try:
        with open(shell_file_path, encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line.startswith('curl'):
                    process_curl_command(line)
        return True
    except IOError as e:
        logger.error(f"读取shell文件失败: {e}")
        return False


def process_curl_command(line):
    """
    处理单条curl命令
    :param line: curl命令行
    """
    # 移除命令中的单引号
    cleaned_line = line.replace("'", "")
    # 将命令拆分为列表形式
    cmd_parts = shlex.split(cleaned_line)
    
    # 替换不兼容的--progress选项为--progress-bar
    if '--progress' in cmd_parts:
        cmd_parts = [arg.replace('--progress', '--progress-bar') for arg in cmd_parts]
    
    try:
        retries = 0
        while retries < MAX_RETRIES:
            try:
                result = subprocess.run(
                    cmd_parts,
                    capture_output=True,
                    text=True,
                    check=True,
                    timeout=TIMEOUT,
                    cwd=WORKING_DIRECTORY
                )
                logger.info(f"成功执行命令: {cleaned_line}")
                logger.debug(f"命令输出: {result.stdout}")
                break
            except subprocess.TimeoutExpired:
                retries += 1
                if retries < MAX_RETRIES:
                    logger.warning(f"下载超时，正在重试({retries}/{MAX_RETRIES})...")
                    time.sleep(RETRY_DELAY)
                else:
                    logger.error(f"已达到最大重试次数({MAX_RETRIES})，下载失败: {cleaned_line}")
                    raise
        else:
            raise Exception(f"已达到最大重试次数({MAX_RETRIES})，下载失败")
    except CalledProcessError as e:
        logger.error(f"命令执行失败: {cleaned_line}")
        logger.error(f"错误输出: {e.stderr}")
    except FileNotFoundError:
        logger.error("未找到curl命令。请确保curl已安装并在系统PATH中。")
        raise


# 主函数
def main():
    # 检查curl是否可用
    try:
        subprocess.run(['curl', '--version'], capture_output=True, text=True, check=True)
    except FileNotFoundError:
        logger.error("未找到curl命令。请确保curl已安装并在系统PATH中。")
        return

    # 执行下载
    download_files_from_shell(SHELL_FILE)


if __name__ == "__main__":
    main()


# 总结：已实现从shell文件读取curl命令并下载文件的功能
# 功能特点：
# - 自动检查curl是否安装及shell文件是否存在
# - 支持命令执行超时重试机制
# - 详细日志记录（同时输出到控制台和文件）
# - 配置参数集中管理，便于维护
# 注意：如需修改下载配置，请调整文件顶部的配置参数区域
# 注意：确保所有curl命令在shell文件中单行书写