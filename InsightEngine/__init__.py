"""
Sports Scientist Agent (运动科学家Agent)
基于训练数据库的科学分析AI代理
人设:理性、严谨、只相信数据,略显极客
核心能力:量化分析心率、配速、距离、时长等基础生理指标
"""

from .agent import SportsScientistAgent, create_agent
from .utils.config import Config, load_config

__version__ = "2.0.0"
__author__ = "Sports Scientist Agent Team"

__all__ = ["SportsScientistAgent", "create_agent", "Config", "load_config"]
