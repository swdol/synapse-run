"""
中长跑理论搜索工具 (Tavily)

版本: 2.0
最后更新: 2025-12-06

简化版本,专注于中长跑运动科学理论搜索,无需考虑时间范围等复杂参数。

提供单一核心工具:
- deep_search_news: 对中长跑理论主题进行最全面的深度分析
"""

import os
import sys
from typing import List, Dict, Any, Optional

# 添加utils目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(os.path.dirname(current_dir))
utils_dir = os.path.join(root_dir, 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

from retry_helper import with_graceful_retry, SEARCH_API_RETRY_CONFIG
from dataclasses import dataclass, field

# 运行前请确保已安装Tavily库: pip install tavily-python
try:
    from tavily import TavilyClient
except ImportError:
    raise ImportError("Tavily库未安装,请运行 `pip install tavily-python` 进行安装。")

# --- 1. 数据结构定义 ---

@dataclass
class SearchResult:
    """网页搜索结果数据类"""
    title: str
    url: str
    content: str
    score: Optional[float] = None
    raw_content: Optional[str] = None
    published_date: Optional[str] = None

@dataclass
class ImageResult:
    """图片搜索结果数据类"""
    url: str
    description: Optional[str] = None

@dataclass
class TavilyResponse:
    """封装Tavily API的完整返回结果"""
    query: str
    answer: Optional[str] = None
    results: List[SearchResult] = field(default_factory=list)
    images: List[ImageResult] = field(default_factory=list)
    response_time: Optional[float] = None


# --- 2. 核心客户端与搜索工具 ---

class TavilyNewsAgency:
    """
    中长跑理论搜索客户端
    提供单一的深度搜索工具,专注于理论研究
    """

    def __init__(self, api_key: Optional[str] = None):
        """
        初始化客户端
        Args:
            api_key: Tavily API密钥,若不提供则从环境变量 TAVILY_API_KEY 读取
        """
        if api_key is None:
            api_key = os.getenv("TAVILY_API_KEY")
            if not api_key:
                raise ValueError("Tavily API Key未找到!请设置TAVILY_API_KEY环境变量或在初始化时提供")
        self._client = TavilyClient(api_key=api_key)

    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return=TavilyResponse(query="搜索失败"))
    def _search_internal(self, **kwargs) -> TavilyResponse:
        """内部通用的搜索执行器"""
        try:
            kwargs['topic'] = 'general'
            api_params = {k: v for k, v in kwargs.items() if v is not None}
            response_dict = self._client.search(**api_params)

            search_results = [
                SearchResult(
                    title=item.get('title'),
                    url=item.get('url'),
                    content=item.get('content'),
                    score=item.get('score'),
                    raw_content=item.get('raw_content'),
                    published_date=item.get('published_date')
                ) for item in response_dict.get('results', [])
            ]

            image_results = [ImageResult(url=item.get('url'), description=item.get('description')) for item in response_dict.get('images', [])]

            return TavilyResponse(
                query=response_dict.get('query'), answer=response_dict.get('answer'),
                results=search_results, images=image_results,
                response_time=response_dict.get('response_time')
            )
        except Exception as e:
            print(f"搜索时发生错误: {str(e)}")
            raise e  # 让重试机制捕获并处理

    # --- Agent 可用的工具方法 ---

    def deep_search_news(self, query: str) -> TavilyResponse:
        """
        【工具】深度理论搜索: 对中长跑理论主题进行最全面、最深入的搜索

        返回AI生成的详细摘要答案和最多20条最相关的搜索结果。
        适用于需要全面了解中长跑训练理论、运动科学原理的场景。

        Args:
            query: 搜索查询,建议使用中长跑专业术语

        Returns:
            TavilyResponse对象,包含搜索结果和AI摘要
        """
        print(f"--- TOOL: 深度理论搜索 (query: {query}) ---")
        return self._search_internal(
            query=query, search_depth="advanced", max_results=20, include_answer="advanced"
        )


# --- 3. 测试与使用示例 ---

def print_response_summary(response: TavilyResponse):
    """简化的打印函数,用于展示测试结果"""
    if not response or not response.query:
        print("未能获取有效响应。")
        return

    print(f"\n查询: '{response.query}' | 耗时: {response.response_time}s")
    if response.answer:
        print(f"AI摘要: {response.answer[:120]}...")
    print(f"找到 {len(response.results)} 条网页, {len(response.images)} 张图片。")
    if response.results:
        first_result = response.results[0]
        date_info = f"(发布于: {first_result.published_date})" if first_result.published_date else ""
        print(f"第一条结果: {first_result.title} {date_info}")
    print("-" * 60)


if __name__ == "__main__":
    # 在运行前,请确保您已设置 TAVILY_API_KEY 环境变量

    try:
        # 初始化客户端
        agency = TavilyNewsAgency()

        # 测试:深度搜索中长跑理论
        response = agency.deep_search_news(query="马拉松训练Lydiard体系理论")
        print_response_summary(response)

    except ValueError as e:
        print(f"初始化失败: {e}")
        print("请确保 TAVILY_API_KEY 环境变量已正确设置。")
    except Exception as e:
        print(f"测试过程中发生未知错误: {e}")
