# -*- coding: utf-8 -*-
"""
训练数据搜索工具工厂
根据配置动态创建对应数据源的搜索工具实例
"""

import sys
import os
from typing import Optional

from .base_search import BaseTrainingDataSearch
from .keep_search import KeepDataSearch
from .garmin_search import GarminDataSearch


class TrainingDataSearchFactory:
    """
    训练数据搜索工具工厂类

    根据config.py中的TRAINING_DATA_SOURCE配置,
    动态创建对应数据源的搜索工具实例
    """

    _SUPPORTED_SOURCES = {
        'keep': KeepDataSearch,
        'garmin': GarminDataSearch
    }

    @classmethod
    def create_search_tool(cls, data_source: Optional[str] = None) -> BaseTrainingDataSearch:
        """
        创建训练数据搜索工具实例

        Args:
            data_source: 数据源类型 ('keep' 或 'garmin')
                        如果为None,则从根目录config.py的TRAINING_DATA_SOURCE字段读取

        Returns:
            对应数据源的搜索工具实例

        Raises:
            ValueError: 数据源不支持或配置缺失时抛出异常
        """
        # 如果未指定数据源,从根目录config.py读取
        if data_source is None:
            data_source = cls._load_data_source_from_config()

        # 验证数据源
        if not data_source:
            raise ValueError(
                "数据源配置缺失! 请在config.py中设置TRAINING_DATA_SOURCE字段, "
                "支持的值: 'keep' 或 'garmin'"
            )

        data_source_lower = data_source.lower()
        if data_source_lower not in cls._SUPPORTED_SOURCES:
            raise ValueError(
                f"不支持的数据源: {data_source}\n"
                f"支持的数据源: {', '.join(cls._SUPPORTED_SOURCES.keys())}"
            )

        # 创建对应的工具实例
        tool_class = cls._SUPPORTED_SOURCES[data_source_lower]
        print(f"✅ 训练数据源: {data_source_lower.upper()}")
        print(f"✅ 工具类: {tool_class.__name__}")

        try:
            tool_instance = tool_class()
            print(f"✅ 支持的查询工具: {', '.join(tool_instance.get_supported_tools())}")
            return tool_instance
        except Exception as e:
            raise RuntimeError(
                f"创建{data_source}数据源工具失败: {str(e)}\n"
                f"请检查数据库配置是否正确"
            ) from e

    @classmethod
    def _load_data_source_from_config(cls) -> Optional[str]:
        """
        从根目录config.py读取TRAINING_DATA_SOURCE配置

        ✨ 热更新机制: 使用统一的ConfigReloader工具，确保获取最新配置值

        Returns:
            数据源类型字符串,如果读取失败则返回None
        """
        try:
            # 导入统一的配置热重载工具
            from utils.config_reloader import get_config_value, reload_config

            # 重载配置并获取数据源
            reload_config(verbose=True)
            data_source = get_config_value('TRAINING_DATA_SOURCE')

            if not data_source:
                print("⚠️  警告: config.py中未找到TRAINING_DATA_SOURCE配置")
                return None

            return data_source

        except ImportError as e:
            print(f"⚠️  警告: 无法导入config_reloader: {e}")
            print(f"   提示: 请确保utils/config_reloader.py文件存在")
            return None
        except Exception as e:
            print(f"⚠️  警告: 读取TRAINING_DATA_SOURCE配置失败: {e}")
            return None

    @classmethod
    def get_supported_sources(cls) -> list:
        """
        获取所有支持的数据源列表

        Returns:
            支持的数据源名称列表
        """
        return list(cls._SUPPORTED_SOURCES.keys())

    @classmethod
    def is_source_supported(cls, data_source: str) -> bool:
        """
        检查指定数据源是否支持

        Args:
            data_source: 数据源名称

        Returns:
            是否支持该数据源
        """
        return data_source.lower() in cls._SUPPORTED_SOURCES


def create_training_data_search(data_source: Optional[str] = None) -> BaseTrainingDataSearch:
    """
    便捷函数: 创建训练数据搜索工具实例

    Args:
        data_source: 数据源类型 ('keep' 或 'garmin')
                    如果为None,则从config.py自动读取

    Returns:
        对应数据源的搜索工具实例

    Examples:
        >>> # 自动从config.py读取数据源
        >>> search_tool = create_training_data_search()
        >>>
        >>> # 手动指定数据源
        >>> keep_tool = create_training_data_search('keep')
        >>> garmin_tool = create_training_data_search('garmin')
    """
    return TrainingDataSearchFactory.create_search_tool(data_source)


# ===== 向后兼容性支持 =====
# 为了保持与旧代码的兼容性,提供TrainingDataDB别名

class TrainingDataDB:
    """
    训练数据搜索工具 - 向后兼容性包装类

    自动根据config.py中的TRAINING_DATA_SOURCE创建对应的搜索工具
    提供与原有TrainingDataDB相同的接口

    注意: 这是为了保持向后兼容性而提供的包装类
         新代码建议直接使用create_training_data_search()或TrainingDataSearchFactory
    """

    def __init__(self, data_source: Optional[str] = None):
        """
        初始化训练数据搜索工具

        Args:
            data_source: 数据源类型,如果为None则从config.py自动读取
        """
        print("📦 初始化TrainingDataDB (向后兼容模式)")
        self._tool = create_training_data_search(data_source)

    def __getattr__(self, name):
        """
        将所有方法调用转发到实际的搜索工具实例

        这样可以透明地调用底层工具的所有方法
        """
        return getattr(self._tool, name)

    @property
    def data_source(self) -> str:
        """获取当前数据源类型"""
        return self._tool.data_source

    def get_supported_tools(self) -> list:
        """获取支持的工具列表"""
        return self._tool.get_supported_tools()
