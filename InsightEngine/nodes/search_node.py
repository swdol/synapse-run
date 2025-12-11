"""
搜索节点实现
负责生成搜索查询和反思查询
"""

import json
from typing import Dict, Any
from json.decoder import JSONDecodeError
from datetime import datetime

from .base_node import BaseNode
from ..prompts import SYSTEM_PROMPT_FIRST_SEARCH, SYSTEM_PROMPT_REFLECTION
from ..utils.text_processing import (
    remove_reasoning_from_output,
    clean_json_tags,
    extract_clean_response,
    fix_incomplete_json
)


class FirstSearchNode(BaseNode):
    """为段落生成首次搜索查询的节点"""
    
    def __init__(self, llm_client):
        """
        初始化首次搜索节点
        
        Args:
            llm_client: LLM客户端
        """
        super().__init__(llm_client, "FirstSearchNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                return "title" in data and "content" in data
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            return "title" in input_data and "content" in input_data
        return False
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, str]:
        """
        调用LLM生成搜索查询和理由
        
        Args:
            input_data: 包含title和content的字符串或字典
            **kwargs: 额外参数
            
        Returns:
            包含search_query和reasoning的字典
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("输入数据格式错误，需要包含title和content字段")
            
            # 准备输入数据
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)

            # 添加当前时间信息
            current_date = datetime.now().strftime("%Y-%m-%d")
            time_context = f"【当前日期: {current_date}】\n\n{message}"

            self.log_info("正在生成首次搜索查询")

            # 调用LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_FIRST_SEARCH, time_context)
            
            # 处理响应
            processed_response = self.process_output(response)
            
            self.log_info(f"生成搜索查询: {processed_response.get('search_query', 'N/A')}")
            return processed_response
            
        except Exception as e:
            self.log_error(f"生成首次搜索查询失败: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> Dict[str, str]:
        """
        处理LLM输出，提取搜索查询和推理
        
        Args:
            output: LLM原始输出
            
        Returns:
            包含search_query和reasoning的字典
        """
        try:
            # 清理响应文本
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # 记录清理后的输出用于调试
            self.log_info(f"清理后的输出: {cleaned_output}")
            
            # 解析JSON
            try:
                result = json.loads(cleaned_output)
                self.log_info("JSON解析成功")
            except JSONDecodeError as e:
                self.log_info(f"JSON解析失败: {str(e)}")
                # 使用更强大的提取方法
                result = extract_clean_response(cleaned_output)
                if "error" in result:
                    self.log_error("JSON解析失败，尝试修复...")
                    # 尝试修复JSON
                    fixed_json = fix_incomplete_json(cleaned_output)
                    if fixed_json:
                        try:
                            result = json.loads(fixed_json)
                            self.log_info("JSON修复成功")
                        except JSONDecodeError:
                            self.log_error("JSON修复失败")
                            # 返回默认查询
                            return self._get_default_search_query()
                    else:
                        self.log_error("无法修复JSON，使用默认查询")
                        return self._get_default_search_query()
            
            # 检测LLM是否输出了嵌套的parameters结构 (非标准格式)
            if "parameters" in result and isinstance(result["parameters"], dict):
                self.log_info("检测到嵌套parameters结构，正在展开...")
                # 将parameters字典的内容展开到顶层
                params = result["parameters"]
                result.update(params)
                # 兼容tool字段 (有些LLM可能输出"tool"而不是"search_tool")
                if "tool" in result and "search_tool" not in result:
                    result["search_tool"] = result["tool"]

            # 验证和清理结果
            search_query = result.get("search_query", "")
            reasoning = result.get("reasoning", "")
            search_tool = result.get("search_tool") or result.get("tool")

            # 如果LLM只输出了工具和参数，没有search_query/reasoning (降级处理)
            if not search_query and search_tool:
                self.log_warning(f"LLM只输出了工具 '{search_tool}' 和参数，缺少search_query/reasoning字段")
                # 从工具名生成默认查询描述
                tool_name_map = {
                    "search_recent_trainings": "最近训练数据查询",
                    "search_by_date_range": "日期范围训练查询",
                    "search_by_distance_range": "距离范围训练查询",
                    "search_by_heart_rate": "心率范围训练查询",
                    "search_by_training_load": "训练负荷范围查询",
                    "search_by_power_zone": "功率区间训练查询",
                    "get_training_stats": "训练统计数据查询",
                    "get_training_effect_analysis": "训练效果分析查询"
                }
                search_query = tool_name_map.get(search_tool, f"{search_tool}查询")
                reasoning = f"基于{search_tool}工具进行数据查询"
                self.log_info(f"自动生成查询描述: {search_query}")

            if not search_query:
                self.log_warning("未找到搜索查询且无法自动生成，使用默认查询")
                return self._get_default_search_query()

            # 提取所有可能的工具参数
            response = {
                "search_query": search_query,
                "reasoning": reasoning,
                "search_tool": result.get("search_tool", "search_recent_trainings"),
                "days": result.get("days"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "min_distance_km": result.get("min_distance_km"),
                "max_distance_km": result.get("max_distance_km"),
                "min_avg_hr": result.get("min_avg_hr"),
                "max_avg_hr": result.get("max_avg_hr"),
                "limit": result.get("limit")
            }

            return response
            
        except Exception as e:
            self.log_error(f"处理输出失败: {str(e)}")
            # 返回默认查询
            return self._get_default_search_query()
    
    def _get_default_search_query(self) -> Dict[str, str]:
        """
        获取默认搜索查询
        
        Returns:
            默认的搜索查询字典
        """
        return {
            "search_query": "相关主题研究",
            "reasoning": "由于解析失败，使用默认搜索查询"
        }


class ReflectionNode(BaseNode):
    """反思段落并生成新搜索查询的节点"""
    
    def __init__(self, llm_client):
        """
        初始化反思节点
        
        Args:
            llm_client: LLM客户端
        """
        super().__init__(llm_client, "ReflectionNode")
    
    def validate_input(self, input_data: Any) -> bool:
        """验证输入数据"""
        if isinstance(input_data, str):
            try:
                data = json.loads(input_data)
                required_fields = ["title", "content", "paragraph_latest_state"]
                return all(field in data for field in required_fields)
            except JSONDecodeError:
                return False
        elif isinstance(input_data, dict):
            required_fields = ["title", "content", "paragraph_latest_state"]
            return all(field in input_data for field in required_fields)
        return False
    
    def run(self, input_data: Any, **kwargs) -> Dict[str, str]:
        """
        调用LLM反思并生成搜索查询
        
        Args:
            input_data: 包含title、content和paragraph_latest_state的字符串或字典
            **kwargs: 额外参数
            
        Returns:
            包含search_query和reasoning的字典
        """
        try:
            if not self.validate_input(input_data):
                raise ValueError("输入数据格式错误，需要包含title、content和paragraph_latest_state字段")
            
            # 准备输入数据
            if isinstance(input_data, str):
                message = input_data
            else:
                message = json.dumps(input_data, ensure_ascii=False)

            # 添加当前时间信息
            current_date = datetime.now().strftime("%Y-%m-%d")
            time_context = f"【当前日期: {current_date}】\n\n{message}"

            self.log_info("正在进行反思并生成新搜索查询")

            # 调用LLM
            response = self.llm_client.invoke(SYSTEM_PROMPT_REFLECTION, time_context)
            
            # 处理响应
            processed_response = self.process_output(response)
            
            self.log_info(f"反思生成搜索查询: {processed_response.get('search_query', 'N/A')}")
            return processed_response
            
        except Exception as e:
            self.log_error(f"反思生成搜索查询失败: {str(e)}")
            raise e
    
    def process_output(self, output: str) -> Dict[str, str]:
        """
        处理LLM输出，提取搜索查询和推理
        
        Args:
            output: LLM原始输出
            
        Returns:
            包含search_query和reasoning的字典
        """
        try:
            # 清理响应文本
            cleaned_output = remove_reasoning_from_output(output)
            cleaned_output = clean_json_tags(cleaned_output)
            
            # 记录清理后的输出用于调试
            self.log_info(f"清理后的输出: {cleaned_output}")
            
            # 解析JSON
            try:
                result = json.loads(cleaned_output)
                self.log_info("JSON解析成功")
            except JSONDecodeError as e:
                self.log_info(f"JSON解析失败: {str(e)}")
                # 使用更强大的提取方法
                result = extract_clean_response(cleaned_output)
                if "error" in result:
                    self.log_error("JSON解析失败，尝试修复...")
                    # 尝试修复JSON
                    fixed_json = fix_incomplete_json(cleaned_output)
                    if fixed_json:
                        try:
                            result = json.loads(fixed_json)
                            self.log_info("JSON修复成功")
                        except JSONDecodeError:
                            self.log_error("JSON修复失败")
                            # 返回默认查询
                            return self._get_default_reflection_query()
                    else:
                        self.log_error("无法修复JSON，使用默认查询")
                        return self._get_default_reflection_query()
            
            # 检测LLM是否输出了嵌套的parameters结构 (非标准格式)
            if "parameters" in result and isinstance(result["parameters"], dict):
                self.log_info("检测到嵌套parameters结构，正在展开...")
                # 将parameters字典的内容展开到顶层
                params = result["parameters"]
                result.update(params)
                # 兼容tool字段 (有些LLM可能输出"tool"而不是"search_tool")
                if "tool" in result and "search_tool" not in result:
                    result["search_tool"] = result["tool"]

            # 验证和清理结果
            search_query = result.get("search_query", "")
            reasoning = result.get("reasoning", "")
            search_tool = result.get("search_tool") or result.get("tool")

            # 如果LLM只输出了工具和参数，没有search_query/reasoning (降级处理)
            if not search_query and search_tool:
                self.log_warning(f"LLM只输出了工具 '{search_tool}' 和参数，缺少search_query/reasoning字段")
                # 从工具名生成默认查询描述
                tool_name_map = {
                    "search_recent_trainings": "最近训练数据查询",
                    "search_by_date_range": "日期范围训练查询",
                    "search_by_distance_range": "距离范围训练查询",
                    "search_by_heart_rate": "心率范围训练查询",
                    "search_by_training_load": "训练负荷范围查询",
                    "search_by_power_zone": "功率区间训练查询",
                    "get_training_stats": "训练统计数据查询",
                    "get_training_effect_analysis": "训练效果分析查询"
                }
                search_query = tool_name_map.get(search_tool, f"{search_tool}查询")
                reasoning = f"基于{search_tool}工具进行数据查询"
                self.log_info(f"自动生成查询描述: {search_query}")

            if not search_query:
                self.log_warning("未找到搜索查询且无法自动生成，使用默认查询")
                return self._get_default_reflection_query()

            # 提取所有可能的工具参数
            response = {
                "search_query": search_query,
                "reasoning": reasoning,
                "search_tool": result.get("search_tool", "search_recent_trainings"),
                "days": result.get("days"),
                "start_date": result.get("start_date"),
                "end_date": result.get("end_date"),
                "min_distance_km": result.get("min_distance_km"),
                "max_distance_km": result.get("max_distance_km"),
                "min_avg_hr": result.get("min_avg_hr"),
                "max_avg_hr": result.get("max_avg_hr"),
                "limit": result.get("limit")
            }

            return response
            
        except Exception as e:
            self.log_error(f"处理输出失败: {str(e)}")
            # 返回默认查询
            return self._get_default_reflection_query()
    
    def _get_default_reflection_query(self) -> Dict[str, str]:
        """
        获取默认反思搜索查询
        
        Returns:
            默认的反思搜索查询字典
        """
        return {
            "search_query": "深度研究补充信息",
            "reasoning": "由于解析失败，使用默认反思搜索查询"
        }
