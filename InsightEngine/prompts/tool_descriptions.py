# -*- coding: utf-8 -*-
"""
训练数据工具描述模板系统
根据数据源动态生成工具描述,支持Keep、Garmin等多种数据源
"""

from typing import Dict, List


# ===== 通用工具描述(所有数据源都支持) =====

COMMON_TOOLS_DESCRIPTION = """
你可以使用以下5种专业的训练数据库查询工具来挖掘真实的训练记录:

1. **search_recent_trainings** - 🔥 查询最近N天训练记录 (推荐用于"最近"、"近期"查询)
   - 适用于:了解最近的训练状态、识别训练规律、分析短期进步
   - 特点:基于当前时间自动计算,无需指定具体日期,避免时间幻觉
   - 参数:days(必需,最近N天)、limit(可选,默认50)
   - **优先级: 当需求包含"最近X天/周/月"时,必须优先使用此工具!**

2. **search_by_date_range** - 按日期范围查询训练记录
   - 适用于:特定历史时期的训练分析、周期性训练效果评估、训练计划回顾
   - 特点:精确的时间范围控制,适合分析历史训练演变
   - 参数:start_date(必需,YYYY-MM-DD)、end_date(必需,YYYY-MM-DD)、limit(可选,默认100)
   - **⚠️ 注意: 仅用于查询明确指定的历史日期范围,不要用于"最近X天"这类相对时间查询!**

3. **get_training_stats** - 获取训练统计数据
   - 适用于:整体训练效果评估、宏观数据统计、训练量汇总
   - 特点:自动计算总距离、平均配速、总时长等关键指标
   - 参数:start_date(可选,YYYY-MM-DD)、end_date(可选,YYYY-MM-DD)

4. **search_by_distance_range** - 按距离范围查询
   - 适用于:长距离训练分析、特定距离训练统计、LSD训练记录
   - 特点:精确筛选特定距离区间的训练
   - 参数:min_distance_km(必需,最小公里数)、max_distance_km(可选,最大公里数)、limit(可选,默认50)

5. **search_by_heart_rate** - 按心率区间查询
   - 适用于:心率训练分析、有氧/无氧训练分布、训练强度评估
   - 特点:基于心率数据筛选,分析训练强度
   - 参数:min_avg_hr(必需,最小平均心率)、max_avg_hr(可选,最大平均心率)、limit(可选,默认50)
"""


# ===== Garmin专属扩展工具描述 =====

GARMIN_EXTENDED_TOOLS_DESCRIPTION = """
**Garmin数据源专属扩展工具**:

6. **search_by_training_load** - 按Garmin训练负荷查询
   - 适用于:训练负荷趋势分析、过度训练检测、训练强度评估
   - 特点:基于Garmin科学算法的训练负荷指标(Training Load)
   - 参数:min_load(必需,最小负荷值)、max_load(可选,最大负荷值)、limit(可选,默认50)
   - **解读**: Training Load < 75(低强度)、75-150(中等强度)、150-300(高强度)、>300(极高强度)

7. **search_by_power_zone** - 按功率区间查询
   - 适用于:功率训练分析、跑步效率评估、配速-功率关系研究
   - 特点:基于Garmin Running Power指标,更科学地量化跑步强度
   - 参数:min_avg_power(必需,最小平均功率/瓦)、max_avg_power(可选,最大平均功率/瓦)、limit(可选,默认50)
   - **解读**: 功率指标综合了速度、坡度、风阻、体重等因素,比配速更准确反映运动强度

8. **get_training_effect_analysis** - 获取Garmin训练效果分析
   - 适用于:训练效果评估、有氧/无氧能力分析、训练计划优化
   - 特点:基于Garmin Firstbeat算法,量化训练对有氧/无氧能力的影响
   - 参数:start_date(可选,YYYY-MM-DD)、end_date(可选,YYYY-MM-DD)
   - **返回指标**:
     * avg_aerobic_effect: 平均有氧训练效果(0-5分)
     * avg_anaerobic_effect: 平均无氧训练效果(0-5分)
     * avg_training_load: 平均训练负荷
     * maintaining_count/improving_count/highly_improving_count: 维持/提升/高度提升效果的训练次数
     * total_moderate_minutes/total_vigorous_minutes: 中等/剧烈强度时长
   - **解读**:
     * Training Effect < 2.0(维持), 2.0-2.9(提升), 3.0-3.9(高度提升), ≥4.0(过度训练)
     * 建议: 80%训练保持在2.0-2.9(提升),20%可达到3.0+(高强度)
"""


# ===== 通用参数配置要求(所有数据源) =====

COMMON_PARAM_REQUIREMENTS = """
4. **🚨 必需参数强制约束 (违反将导致查询失败) 🚨**:
   - **search_recent_trainings**:
     * ✅ 必需参数: days (整数,表示"最近N天")
     * ❌ 禁止: 调用此工具时不提供days参数
     * 示例: `"days": 30` (最近30天)

   - **search_by_date_range**:
     * ✅ 必需参数: start_date (字符串,格式YYYY-MM-DD), end_date (字符串,格式YYYY-MM-DD)
     * ❌ 禁止: 缺少start_date或end_date任一参数
     * 示例: `"start_date": "2025-01-01", "end_date": "2025-01-31"`

   - **search_by_distance_range**:
     * ✅ 必需参数: min_distance_km (数值,单位公里)
     * ⚠️ 可选参数: max_distance_km (数值,单位公里)
     * 示例: `"min_distance_km": 10, "max_distance_km": 21`

   - **search_by_heart_rate**:
     * ✅ 必需参数: min_avg_hr (整数,最小平均心率bpm)
     * ⚠️ 可选参数: max_avg_hr (整数,最大平均心率bpm)
     * 示例: `"min_avg_hr": 140, "max_avg_hr": 170`

   - **get_training_stats**:
     * ⚠️ 全部可选: start_date, end_date (默认查询全部历史数据)
     * 示例: `"start_date": "2025-01-01", "end_date": "2025-01-31"`

   - **通用可选参数**: limit (整数,默认50条,建议范围10-200)
"""


# ===== Garmin专属参数配置要求 =====

GARMIN_PARAM_REQUIREMENTS = """
   - **search_by_training_load** (Garmin专属):
     * ✅ 必需参数: min_load (整数,最小训练负荷)
     * ⚠️ 可选参数: max_load (整数,最大训练负荷)
     * 示例: `"min_load": 150, "max_load": 300"`

   - **search_by_power_zone** (Garmin专属):
     * ✅ 必需参数: min_avg_power (整数,最小平均功率/瓦)
     * ⚠️ 可选参数: max_avg_power (整数,最大平均功率/瓦)
     * 示例: `"min_avg_power": 200, "max_avg_power": 250"`

   - **get_training_effect_analysis** (Garmin专属):
     * ⚠️ 全部可选: start_date, end_date (默认查询全部历史数据)
     * 示例: `"start_date": "2025-01-01", "end_date": "2025-01-31"`
"""


# ===== 通用查询优化示例(所有数据源) =====

COMMON_QUERY_EXAMPLES = """
**查询优化示例**:
- ✅ 正确: 如果需要补充最近2个月趋势 → search_recent_trainings, days=60
- ❌ 错误: 如果需要补充最近2个月趋势 → search_by_date_range, start_date="[过去日期]", end_date="[今天]" (不要用date_range查"最近"!)
- ✅ 正确: 如果需要补充2025年1-3月的历史数据 → search_by_date_range, start_date="2025-01-01", end_date="2025-03-31"
- ✅ 正确: 如果需要长距离训练数据 → search_by_distance_range, min_distance_km=15
- ✅ 正确: 如果需要强度分析 → search_by_heart_rate, min_avg_hr=150, max_avg_hr=170
"""


# ===== Garmin专属查询优化示例 =====

GARMIN_QUERY_EXAMPLES = """
**Garmin专属查询示例**:
- ✅ 正确: 如果需要高负荷训练分析 → search_by_training_load, min_load=150, max_load=300
- ✅ 正确: 如果需要功率区间分析 → search_by_power_zone, min_avg_power=200, max_avg_power=250
- ✅ 正确: 如果需要训练效果统计 → get_training_effect_analysis, start_date="2025-01-01", end_date="2025-01-31"
"""


# ===== Keep专属数据特征说明 =====

KEEP_DATA_FEATURES_DESCRIPTION = """
**Keep数据源特征说明**:
- **核心指标**: 距离、配速、时长、心率(平均/最大)、卡路里
- **心率数据**: 提供逐秒心率序列数据(heart_rate_data),可用于心率漂移分析
- **数据来源**: Keep APP训练��录
- **数据特点**: 适合基础训练分析,心率数据较为详细
"""


KEEP_REPORT_MODULES_SUGGESTION = """
**建议分析模块(Keep数据源)**:
- ✅ 训练负荷量化 (频次、里程、周平均)
- ✅ 配速表现评估 (配速趋势、区间分布)
- ✅ 心率强度监测 (平均心率、心率区间)
- ✅ 长距离耐力评估 (长距离训练统计)
- ✅ 训练节奏分析 (频次稳定性、恢复间隔)
"""


# ===== Garmin专属数据特征说明 =====

GARMIN_DATA_FEATURES_DESCRIPTION = """
**Garmin数据源特征说明**:
- **核心指标**: 基础指标(距离、配速、时长、心率等) + Garmin专业算法指标
- **高级指标**:
  * **训练效果**: Aerobic/Anaerobic Training Effect (0-5分制)
  * **训练负荷**: Training Load (综合强度和时长的负荷指标)
  * **跑步动力学**: 步频(cadence)、步幅(stride_length)、垂直振幅(vertical_oscillation)、触地时间(ground_contact_time)
  * **功率指标**: Running Power、Normalized Power、功率区间分布
  * **心率区间**: 5个心率区间的精确时长分布
  * **身体状态**: Body Battery变化量、预估汗液流失量
- **数据来源**: Garmin设备(Forerunner/Fenix等专业运动手表)
- **数据特点**: 专业级运动数据,适合深度科学化训练分析
- **科学优势**: 基于Firstbeat运动生理学算法,提供训练效果量化评估
"""


GARMIN_REPORT_MODULES_SUGGESTION = """
**建议分析模块(Garmin数据源,可选择3-5个)**:

**基础模块** (适用于所有用户):
- ✅ 训练负荷量化 (频次、里程、周平均)
- ✅ 配速表现评估 (配速趋势、区间分布)
- ✅ 心率强度监测 (平均心率、心率区间分布)

**Garmin专属高级模块** (基于Firstbeat算法):
- 🔥 **训练效果分析** (Aerobic/Anaerobic TE评分、训练效果分布、强度建议)
- 🔥 **训练负荷监控** (Training Load趋势、急性/慢性负荷比、过度训练预警)
- 🔥 **跑步经济性评估** (步频-配速关系、步幅效率、垂直振幅-触地时间分析)
- 🔥 **功率训练分析** (平均功率趋势、功率区间分布、功率-配速耦合性)
- 🔥 **心率精细分析** (5区间时长分布、心率-配速效率、心率漂移量化)

**建议组合**:
- 进阶跑者: 训练负荷量化 + 训练效果分析 + 跑步经济性评估
- 科学训练者: 训练负荷监控 + 功率训练分析 + 心率精细分析
- 马拉松备赛: 配速表现评估 + 训练效果分析 + 训练负荷监控
"""


# ===== 数据源配置映射 =====

DATA_SOURCE_CONFIGS: Dict[str, Dict[str, str]] = {
    'keep': {
        'tools_description': COMMON_TOOLS_DESCRIPTION,
        'data_features': KEEP_DATA_FEATURES_DESCRIPTION,
        'report_modules': KEEP_REPORT_MODULES_SUGGESTION,
        'extended_tools': '',  # Keep没有扩展工具
        'available_metrics': '距离、配速、时长、心率、卡路里',
        'advanced_capabilities': ''
    },
    'garmin': {
        'tools_description': COMMON_TOOLS_DESCRIPTION + GARMIN_EXTENDED_TOOLS_DESCRIPTION,
        'data_features': GARMIN_DATA_FEATURES_DESCRIPTION,
        'report_modules': GARMIN_REPORT_MODULES_SUGGESTION,
        'extended_tools': GARMIN_EXTENDED_TOOLS_DESCRIPTION,
        'available_metrics': '距离、配速、时长、心率、训练负荷、训练效果、功率、步频、步幅、垂直振幅、触地时间、心率区间分布',
        'advanced_capabilities': '✅ 训练效果量化 ✅ 训练���荷监控 ✅ 跑步动力学分析 ✅ 功率训练支持'
    }
}


# ===== 工具描述生成函数 =====

def get_tools_description(data_source: str) -> str:
    """
    获取指定数据源的工具描述

    Args:
        data_source: 数据源类型 ('keep' 或 'garmin')

    Returns:
        完整的工具描述文本
    """
    data_source_lower = data_source.lower()

    if data_source_lower not in DATA_SOURCE_CONFIGS:
        raise ValueError(
            f"不支持的数据源: {data_source}\n"
            f"支持的数据源: {', '.join(DATA_SOURCE_CONFIGS.keys())}"
        )

    config = DATA_SOURCE_CONFIGS[data_source_lower]
    return config['tools_description']


def get_data_features_description(data_source: str) -> str:
    """
    获取指定数据源的数据特征说明

    Args:
        data_source: 数据源类型 ('keep' 或 'garmin')

    Returns:
        数据特征说明文本
    """
    data_source_lower = data_source.lower()

    if data_source_lower not in DATA_SOURCE_CONFIGS:
        raise ValueError(f"不支持的数据源: {data_source}")

    config = DATA_SOURCE_CONFIGS[data_source_lower]
    return config['data_features']


def get_available_metrics(data_source: str) -> str:
    """
    获取指定数据源的可用指标列表

    Args:
        data_source: 数据源类型

    Returns:
        可用指标列表文本
    """
    data_source_lower = data_source.lower()

    if data_source_lower not in DATA_SOURCE_CONFIGS:
        raise ValueError(f"不支持的数据源: {data_source}")

    config = DATA_SOURCE_CONFIGS[data_source_lower]
    return config['available_metrics']


def get_advanced_capabilities(data_source: str) -> str:
    """
    获取指定数据源的高级功能说明

    Args:
        data_source: 数据源类型

    Returns:
        高级功能说明文本(如果有)
    """
    data_source_lower = data_source.lower()

    if data_source_lower not in DATA_SOURCE_CONFIGS:
        raise ValueError(f"不支持的数据源: {data_source}")

    config = DATA_SOURCE_CONFIGS[data_source_lower]
    return config['advanced_capabilities']


def get_supported_data_sources() -> List[str]:
    """
    获取所有支持的数据源列表

    Returns:
        数据源名称列表
    """
    return list(DATA_SOURCE_CONFIGS.keys())


def get_report_modules_suggestion(data_source: str) -> str:
    """
    获取指定数据源的报告模块建议

    Args:
        data_source: 数据源类型

    Returns:
        报告模块建议文本
    """
    data_source_lower = data_source.lower()

    if data_source_lower not in DATA_SOURCE_CONFIGS:
        raise ValueError(f"不支持的数据源: {data_source}")

    config = DATA_SOURCE_CONFIGS[data_source_lower]
    return config['report_modules']


# ===== 示例:打印不同数据源的工具描述 =====

if __name__ == "__main__":
    print("=" * 80)
    print("Keep数据源工具描述:")
    print("=" * 80)
    print(get_tools_description('keep'))
    print("\n" + "=" * 80)
    print("Keep数据源特征:")
    print("=" * 80)
    print(get_data_features_description('keep'))

    print("\n\n" + "=" * 80)
    print("Garmin数据源工具描述:")
    print("=" * 80)
    print(get_tools_description('garmin'))
    print("\n" + "=" * 80)
    print("Garmin数据源特征:")
    print("=" * 80)
    print(get_data_features_description('garmin'))
    print("\n" + "=" * 80)
    print("Garmin高级功能:")
    print("=" * 80)
    print(get_advanced_capabilities('garmin'))
