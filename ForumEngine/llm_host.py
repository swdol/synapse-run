"""
论坛总教练模块
总教练是整个分析系统的统筹者和决策者，负责：
1. 理解用户的核心目标和优先级
2. 协调各Agent的研究方向和分工
3. 评估各Agent的分析质量并及时调整策略
4. 综合多方观点形成最优决策
5. 推动分析流程向目标高效推进
"""

from openai import OpenAI
import sys
import os
from typing import List, Dict, Any, Optional
from datetime import datetime
import re

# 添加项目根目录到Python路径以导入config
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import FORUM_HOST_API_KEY, FORUM_HOST_BASE_URL, FORUM_HOST_MODEL_NAME

# 添加utils目录到Python路径
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
utils_dir = os.path.join(root_dir, 'utils')
if utils_dir not in sys.path:
    sys.path.append(utils_dir)

from retry_helper import with_graceful_retry, SEARCH_API_RETRY_CONFIG


class ForumHost:
    """
    论坛总教练类
    总教练是整个分析系统的大脑和指挥中心，具备以下核心能力：

    1. **战略统筹**：理解用户的最终目标，制定整体分析策略
    2. **团队协调**：评估各Agent的专长，合理分配研究任务
    3. **质量把控**：判断分析的深度和准确性，识别信息盲区
    4. **决策果断**：根据进展及时调整方向，避免无效探索
    5. **经验丰富**：基于历史数据和领域知识指导分析流程
    """

    def __init__(self, api_key: str = None, base_url: Optional[str] = None, model_name: Optional[str] = None):
        """
        初始化论坛总教练

        Args:
            api_key: 硅基流动API密钥，如果不提供则从配置文件读取
            base_url: 接口基础地址，默认使用配置文件提供的SiliconFlow地址
            model_name: 使用的LLM模型名称
        """
        self.api_key = api_key or FORUM_HOST_API_KEY

        if not self.api_key:
            raise ValueError("未找到硅基流动API密钥，请在config.py中设置FORUM_HOST_API_KEY")

        self.base_url = base_url or FORUM_HOST_BASE_URL

        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.base_url
        )
        self.model = model_name or FORUM_HOST_MODEL_NAME  # Use configured model

        # Track previous summaries to avoid duplicates
        self.previous_summaries = []
    
    def generate_host_speech(self, forum_logs: List[str]) -> Optional[str]:
        """
        生成总教练发言 - 统筹全局、决策调整、引导方向

        总教练的核心职责：
        1. 评估各Agent的分析质量和信息完整性
        2. 识别当前分析的盲区和需要深挖的方向
        3. 根据用户目标调整各Agent的工作重点
        4. 综合多方观点形成决策建议
        5. 明确指出下一步行动方向

        Args:
            forum_logs: 论坛日志内容列表

        Returns:
            总教练发言内容，如果生成失败返回None
        """
        try:
            # 解析论坛日志，提取有效内容
            parsed_content = self._parse_forum_logs(forum_logs)
            
            if not parsed_content['agent_speeches']:
                print("ForumHost: 没有找到有效的agent发言")
                return None
            
            # 构建prompt
            system_prompt = self._build_system_prompt()
            user_prompt = self._build_user_prompt(parsed_content)
            
            # 调用API生成发言
            response = self._call_qwen_api(system_prompt, user_prompt)
            
            if response["success"]:
                speech = response["content"]
                # 清理和格式化发言
                speech = self._format_host_speech(speech)
                return speech
            else:
                print(f"ForumHost: API调用失败 - {response.get('error', '未知错误')}")
                return None
                
        except Exception as e:
            print(f"ForumHost: 生成发言时出错 - {str(e)}")
            return None
    
    def _parse_forum_logs(self, forum_logs: List[str]) -> Dict[str, Any]:
        """
        解析论坛日志，提取agent发言
        
        Returns:
            包含agent发言的字典
        """
        parsed = {
            'agent_speeches': []
        }
        
        for line in forum_logs:
            if not line.strip():
                continue
            
            # 解析时间戳和发言者
            match = re.match(r'\[(\d{2}:\d{2}:\d{2})\]\s*\[(\w+)\]\s*(.+)', line)
            if match:
                timestamp, speaker, content = match.groups()
                
                # 跳过系统消息和HOST自己的发言
                if speaker in ['SYSTEM', 'HOST']:
                    continue
                
                # 记录agent发言
                if speaker in ['INSIGHT', 'MEDIA', 'QUERY']:
                    # 处理转义的换行符
                    content = content.replace('\\n', '\n')
                    
                    parsed['agent_speeches'].append({
                        'timestamp': timestamp,
                        'speaker': speaker,
                        'content': content
                    })
        
        return parsed
    
    
    def _build_system_prompt(self) -> str:
        """构建总教练系统prompt"""
        return """你是一个多Agent跑步训练分析系统的**总教练**。作为系统的大脑和决策中心，你的角色远超普通主持人：

## 核心定位
你是**经验丰富的总教练**，负责统筹全局、协调团队、做出关键决策。你不仅要总结信息，更要**主动引导方向、评估质量、果断调整策略**。

## 五大核心职责

### 1. 深度理解用户目标（倾听）
- **识别核心需求**：从用户问题中提取真正的训练目标和痛点
- **评估优先级**：判断哪些信息对用户最关键，哪些可以暂缓
- **明确边界**：确定分析的深度和广度，避免偏离主线

### 2. 评估Agent工作质量（把控）
- **分析完整性**：各Agent的信息是否充分？有无遗漏关键维度？
  - INSIGHT的数据是否覆盖足够样本？统计是否严谨？
  - MEDIA的情报是否具体可操作？有无关键信息缺失？
  - QUERY的理论是否深入本质？是否引用权威研究？学术框架是否完整？
- **数据可靠性**：引用的数据源是否权威？结论是否有证据支撑？
- **专业深度**：分析是否触及本质？还是停留在表面？
- **互补性检查**：不同Agent的信息是相互印证还是存在矛盾？

### 3. 协调研究方向（统筹）
- **分工优化**：根据各Agent专长合理分配任务
  - **INSIGHT(运动科学家)**：挖掘训练数据库，提供生理数据、配速心率分析、训练负荷统计
  - **MEDIA(后勤与情报官)**：收集比赛报名、天气预报、装备价格、路线坡度等实用情报
  - **QUERY(理论专家)**：搜索中长跑训练理论、运动医学研究、训练流派对比，提供学术性理论支撑
- **避免重复**：识别各Agent的重叠部分，引导差异化探索
- **补充盲区**：发现信息缺口，明确指派特定Agent深挖
  - 缺训练数据→INSIGHT补充
  - 缺实用情报→MEDIA补充
  - 缺理论基础→QUERY补充

### 4. 综合决策（果断）
- **多维对比**：整合科学数据(INSIGHT)、实用情报(MEDIA)、训练理论(QUERY)，找出最优方案
- **冲突解决**：当不同来源的信息矛盾时，基于证据强度做出判断
  - 例：数据显示心率偏高 vs 理论建议提升乳酸阈值强度 → 综合评估做决策
- **风险评估**：评估训练方案的适用性、安全性、可行性
- **个性化建议**：根据不同水平跑者提供差异化方案

### 5. 推进分析流程（引导）
- **明确下一步**：具体指出各Agent下一轮应该关注什么
  - "INSIGHT需补充最近30天的长距离训练数据"
  - "MEDIA需查询比赛当天的天气预报和赛道坡度"
  - "QUERY需深入研究Daniels VDOT在800米训练中的应用理论"
- **设定目标**：为下一阶段分析设定清晰的验证问题
- **调整策略**：如果当前方向效果不佳，果断切换思路
- **收敛决策**：在信息足够时及时总结，避免无效探索

## 团队成员介绍
- **INSIGHT(运动科学家)**：严谨理性，只相信数据。专长：训练数据库挖掘、生理指标量化分析、统计建模
- **MEDIA(后勤与情报官)**：注重实用，关注细节。专长：比赛情报收集、装备价格对比、天气路线查询
- **QUERY(理论专家)**：博学多才，引经据典。专长：中长跑训练理论体系、运动医学论文、训练流派对比（Lydiard/Daniels/Canova）、专项训练方法理论基础（亚索800、速耐、节奏跑）

## 发言要求
1. **决策导向**（800-1200字）：不是简单总结，而是做出明确的方向性判断
2. **质量评估**：明确指出各Agent分析的优点和不足
   - INSIGHT的数据是否充分？结论是否严谨？
   - MEDIA的情报是否实用？信息是否完整？
   - QUERY的理论是否深入？是否引用权威研究？学术性是否足够？
3. **具体指令**：下一步要求必须具体，精准分工
4. **优先级排序**：明确哪些问题最紧急，哪些可以后续探索
5. **证据支撑**：所有判断基于Agent提供的数据，避免主观臆断

## 决策风格
- **经验丰富**：结合历史案例和领域知识做判断
- **果断明确**：不模棱两可，给出清晰的行动指令
- **科学严谨**：重视数据证据(INSIGHT)，重视实用性(MEDIA)，重视理论深度(QUERY)
- **全局视野**：始终关注用户的最终目标，不陷入细节

记住：你是**总教练**，不是记录员。你的价值在于**战略判断、质量把控、方向引导、专家协调**。"""
    
    def _build_user_prompt(self, parsed_content: Dict[str, Any]) -> str:
        """构建用户prompt"""
        # 获取最近的发言
        recent_speeches = parsed_content['agent_speeches']

        # 构建发言摘要，不截断内容
        speeches_text = "\n\n".join([
            f"[{s['timestamp']}] {s['speaker']}:\n{s['content']}"
            for s in recent_speeches
        ])

        prompt = f"""最近的Agent分析记录：
{speeches_text}

请你作为**总教练**，基于以上三位专家的分析进行统筹决策。请按以下结构组织你的发言：

**一、理解用户核心目标**
- 从用户问题中识别真正的训练目标和痛点
- 判断当前最重要的优先级（提速?备赛?避免伤病?）

**二、评估各Agent工作质量**
- **INSIGHT(运动科学家)**的数据分析：
  - 样本量是否充足？统计是否严谨？结论是否基于证据？
- **MEDIA(后勤与情报官)**的实用情报：
  - 信息是否具体可操作？是否缺少关键细节？
- **QUERY(理论专家)**的学术研究：
  - 理论是否深入本质？是否引用权威文献？训练流派对比是否完整？理论框架是否系统？

**三、综合决策与方向调整**
- 整合三位专家的观点：
  - 科学数据(INSIGHT) + 实用情报(MEDIA) + 训练理论(QUERY) = 综合方案
- 指出信息矛盾（如有）：
  - 例："数据显示心率偏高，但理论建议提升乳酸阈值强度" → 你的判断是什么？
- 识别信息盲区：
  - 哪些关键信息还缺失？需要哪个Agent补充？

**四、明确下一步行动指令**
- 给INSIGHT的具体任务：（例："补充最近30天长距离训练数据"）
- 给MEDIA的具体任务：（例："查询比赛当天天气和赛道坡度"）
- 给QUERY的具体任务：（例："深入研究Lydiard马拉松基础期理论和Canova特异性耐力的学术对比"）
- 优先级排序：哪些问题最紧急？

请发表总教练发言（800-1200字），做出明确的决策和具体的指令，不要简单总结，要体现你的战略判断和方向引导能力。"""

        return prompt
    
    @with_graceful_retry(SEARCH_API_RETRY_CONFIG, default_return={"success": False, "error": "API服务暂时不可用"})
    def _call_qwen_api(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """调用Qwen API"""
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.6,
                top_p=0.9,
            )

            if response.choices:
                content = response.choices[0].message.content
                return {"success": True, "content": content}
            else:
                return {"success": False, "error": "API返回格式异常"}
        except Exception as e:
            return {"success": False, "error": f"API调用异常: {str(e)}"}
    
    def _format_host_speech(self, speech: str) -> str:
        """格式化主持人发言"""
        # 移除多余的空行
        speech = re.sub(r'\n{3,}', '\n\n', speech)
        
        # 移除可能的引号
        speech = speech.strip('"\'""‘’')
        
        return speech.strip()


# 创建全局实例
_host_instance = None

def get_forum_host() -> ForumHost:
    """获取全局论坛主持人实例"""
    global _host_instance
    if _host_instance is None:
        _host_instance = ForumHost()
    return _host_instance

def generate_host_speech(forum_logs: List[str]) -> Optional[str]:
    """生成主持人发言的便捷函数"""
    return get_forum_host().generate_host_speech(forum_logs)
