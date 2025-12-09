#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
训练数据导入脚本 - 使用SQLAlchemy ORM安全导入
从Excel/CSV文件导入训练记录到MySQL数据库

使用方法:
1. 确保数据库已创建training_records_keep和training_records_garmin表
2. 配置config.py中的数据库连接参数
3. 运行:
   - Keep数据: python scripts/import_training_data.py --source keep --file data/406099.xlsx
   - Garmin数据: python scripts/import_training_data.py --source garmin --file data/garmin_activities.csv

功能:
- 使用SQLAlchemy ORM避免SQL注入风险
- 支持Keep和Garmin两种数据源
- 自动解析Excel和CSV文件
- 数据清洗(处理NaN值、时间格式转换)
- 批量导入到数据库
- 支持覆盖写入模式(TRUNCATE TABLE)
"""

import os
import sys
import pandas as pd
import argparse
from datetime import datetime
from pathlib import Path
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# 添加项目根目录到Python路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 导入必需模块
import config
from models.training_record import TrainingRecordKeep, TrainingRecordGarmin, Base
from sqlalchemy import create_engine


class TrainingDataImporter:
    """训练数据导入器 - 使用SQLAlchemy ORM"""

    def __init__(self, data_file: str, data_source: str = 'keep', db_engine=None):
        """
        初始化导入器

        Args:
            data_file: 数据文件路径 (Excel或CSV)
            data_source: 数据源类型 ('keep' 或 'garmin')
            db_engine: SQLAlchemy引擎,如果为None则直接从config构建
        """
        self.data_file = data_file
        self.data_source = data_source.lower()

        if self.data_source not in ['keep', 'garmin']:
            raise ValueError(f"不支持的数据源: {data_source}, 请使用 'keep' 或 'garmin'")

        if db_engine:
            self.engine = db_engine
        else:
            # 直接从config构建引擎,避免importlib.reload的不确定性
            connection_string = (
                f'mysql+pymysql://{config.DB_USER}:{config.DB_PASSWORD}'
                f'@{config.DB_HOST}:{config.DB_PORT}/{config.DB_NAME}'
                f'?charset={config.DB_CHARSET}'
            )
            self.engine = create_engine(
                connection_string,
                pool_pre_ping=True,
                pool_recycle=3600,
                echo=False
            )

        self.SessionLocal = sessionmaker(bind=self.engine, autoflush=False, autocommit=False)

    def load_data(self) -> pd.DataFrame:
        """加载数据文件 (Excel或CSV)"""
        print(f"[1/4] 加载数据文件: {self.data_file}")
        if not os.path.exists(self.data_file):
            raise FileNotFoundError(f"数据文件不存在: {self.data_file}")

        # 根据文件扩展名选择加载方式
        file_ext = Path(self.data_file).suffix.lower()
        if file_ext in ['.xlsx', '.xls']:
            df = pd.read_excel(self.data_file)
        elif file_ext == '.csv':
            df = pd.read_csv(self.data_file)
        else:
            raise ValueError(f"不支持的文件格式: {file_ext}, 请使用 .xlsx, .xls 或 .csv 文件")

        print(f"   原始列: {df.columns.tolist()}")
        print(f"   加载 {len(df)} 条记录")

        # Keep数据特殊处理: 删除运动轨迹列
        if self.data_source == 'keep' and '运动轨迹' in df.columns:
            df = df.drop(columns=['运动轨迹'])
            print("   已删除'运动轨迹'列")

        return df

    def clean_data(self, df: pd.DataFrame) -> pd.DataFrame:
        """数据清洗"""
        print("[2/4] 数据清洗中...")

        if self.data_source == 'keep':
            # Keep数据清洗
            df = df.fillna({
                '运动时长(秒)': 0,
                '卡路里': 0,
                '运动距离(米)': 0.0,
                '平均心率': 0,
                '最大心率': 0,
                '心率记录': '[]'
            })

            # 转换数据类型
            df['运动时长(秒)'] = df['运动时长(秒)'].astype(int)
            df['卡路里'] = df['卡路里'].astype(int)
            df['运动距离(米)'] = df['运动距离(米)'].astype(float)
            df['平均心率'] = df['平均心率'].astype(int)
            df['最大心率'] = df['最大心率'].astype(int)

            # 时间格式统一
            df['开始时间'] = pd.to_datetime(df['开始时间'])
            df['结束时间'] = pd.to_datetime(df['结束时间'])

        elif self.data_source == 'garmin':
            # Garmin数据清洗 - 所有字段都允许为空
            # 时间格式统一
            df['开始时间(GMT)'] = pd.to_datetime(df['开始时间(GMT)'])
            df['结束时间(GMT)'] = pd.to_datetime(df['结束时间(GMT)'])

            # 确保时长字段为整数
            df['时长(秒)'] = df['时长(秒)'].fillna(0).astype(int)

            # 数值字段处理 - 将空值保持为None而不是0
            numeric_fields = [
                '距离(米)', '平均心率', '最大心率', '心率区间1(秒)', '心率区间2(秒)',
                '心率区间3(秒)', '心率区间4(秒)', '心率区间5(秒)', '平均步频(步/分)',
                '最大步频', '平均步幅(cm)', '平均垂直振幅(cm)', '平均触地时间(ms)',
                '垂直振幅比(%)', '总步数', '平均功率(W)', '最大功率(W)',
                '标准化功率(W)', '平均速度(m/s)', '最大速度(m/s)', '功率区间1(秒)',
                '功率区间2(秒)', '功率区间3(秒)', '功率区间4(秒)', '功率区间5(秒)',
                '有氧训练效果', '无氧训练效果', '训练负荷', '活动卡路里',
                '基础代谢卡路里', '估算失水量(ml)', '中等强度时长(分)',
                '高强度时长(分)', 'Body Battery变化'
            ]

            for field in numeric_fields:
                if field in df.columns:
                    # 保持空值为None,不填充0
                    df[field] = pd.to_numeric(df[field], errors='coerce')

        print(f"   清洗完成, 有效记录: {len(df)}")
        return df

    def create_table_if_not_exists(self):
        """如果表不存在则创建"""
        print("[3/4] 检查数据库表...")
        Base.metadata.create_all(bind=self.engine)
        print("   表结构检查完成")

    def import_to_db(self, df: pd.DataFrame, truncate_first: bool = False):
        """
        导入数据到数据库 - 使用SQLAlchemy ORM

        Args:
            df: 待导入的DataFrame
            truncate_first: 是否先清空表(覆盖写入模式)

        Returns:
            dict: 导入结果统计 {'success': int, 'failed': int, 'total': int}
        """
        print("[4/4] 导入数据到数据库...")

        # 创建表(如果不存在)
        self.create_table_if_not_exists()

        session = self.SessionLocal()
        try:
            # 覆盖写入模式:先清空表
            if truncate_first:
                print("   覆盖写入模式:清空现有数据...")
                if self.data_source == 'keep':
                    session.query(TrainingRecordKeep).delete()
                else:
                    session.query(TrainingRecordGarmin).delete()
                session.commit()
                print("   数据清空完成")

            now_ts = int(datetime.now().timestamp())
            success_count = 0
            failed_count = 0
            batch_records = []

            for idx, row in df.iterrows():
                try:
                    if self.data_source == 'keep':
                        # Keep数据导入
                        record = TrainingRecordKeep(
                            user_id='default_user',
                            exercise_type=row['运动类型'],
                            duration_seconds=int(row['运动时长(秒)']),
                            start_time=row['开始时间'].to_pydatetime(),
                            end_time=row['结束时间'].to_pydatetime(),
                            calories=int(row['卡路里']) if pd.notna(row['卡路里']) else None,
                            distance_meters=float(row['运动距离(米)']) if pd.notna(row['运动距离(米)']) else None,
                            avg_heart_rate=int(row['平均心率']) if pd.notna(row['平均心率']) else None,
                            max_heart_rate=int(row['最大心率']) if pd.notna(row['最大心率']) else None,
                            heart_rate_data=str(row['心率记录']) if pd.notna(row['心率记录']) else '[]',
                            add_ts=now_ts,
                            last_modify_ts=now_ts,
                            data_source='keep_import'
                        )
                    else:
                        # Garmin数据导入
                        record = TrainingRecordGarmin(
                            user_id='default_user',
                            activity_id=str(row['ID']) if pd.notna(row.get('ID')) else None,
                            activity_name=str(row['活动名称']) if pd.notna(row.get('活动名称')) else None,
                            sport_type=row['运动类型'],
                            start_time_gmt=row['开始时间(GMT)'].to_pydatetime(),
                            end_time_gmt=row['结束时间(GMT)'].to_pydatetime(),
                            duration_seconds=int(row['时长(秒)']),
                            distance_meters=float(row['距离(米)']) if pd.notna(row.get('距离(米)')) else None,
                            avg_heart_rate=int(row['平均心率']) if pd.notna(row.get('平均心率')) else None,
                            max_heart_rate=int(row['最大心率']) if pd.notna(row.get('最大心率')) else None,
                            hr_zone_1_seconds=int(row['心率区间1(秒)']) if pd.notna(row.get('心率区间1(秒)')) else None,
                            hr_zone_2_seconds=int(row['心率区间2(秒)']) if pd.notna(row.get('心率区间2(秒)')) else None,
                            hr_zone_3_seconds=int(row['心率区间3(秒)']) if pd.notna(row.get('心率区间3(秒)')) else None,
                            hr_zone_4_seconds=int(row['心率区间4(秒)']) if pd.notna(row.get('心率区间4(秒)')) else None,
                            hr_zone_5_seconds=int(row['心率区间5(秒)']) if pd.notna(row.get('心率区间5(秒)')) else None,
                            avg_cadence=int(row['平均步频(步/分)']) if pd.notna(row.get('平均步频(步/分)')) else None,
                            max_cadence=int(row['最大步频']) if pd.notna(row.get('最大步频')) else None,
                            avg_stride_length_cm=float(row['平均步幅(cm)']) if pd.notna(row.get('平均步幅(cm)')) else None,
                            avg_vertical_oscillation_cm=float(row['平均垂直振幅(cm)']) if pd.notna(row.get('平均垂直振幅(cm)')) else None,
                            avg_ground_contact_time_ms=int(row['平均触地时间(ms)']) if pd.notna(row.get('平均触地时间(ms)')) else None,
                            vertical_ratio_percent=float(row['垂直振幅比(%)']) if pd.notna(row.get('垂直振幅比(%)')) else None,
                            total_steps=int(row['总步数']) if pd.notna(row.get('总步数')) else None,
                            avg_power_watts=int(row['平均功率(W)']) if pd.notna(row.get('平均功率(W)')) else None,
                            max_power_watts=int(row['最大功率(W)']) if pd.notna(row.get('最大功率(W)')) else None,
                            normalized_power_watts=int(row['标准化功率(W)']) if pd.notna(row.get('标准化功率(W)')) else None,
                            avg_speed_mps=float(row['平均速度(m/s)']) if pd.notna(row.get('平均速度(m/s)')) else None,
                            max_speed_mps=float(row['最大速度(m/s)']) if pd.notna(row.get('最大速度(m/s)')) else None,
                            power_zone_1_seconds=int(row['功率区间1(秒)']) if pd.notna(row.get('功率区间1(秒)')) else None,
                            power_zone_2_seconds=int(row['功率区间2(秒)']) if pd.notna(row.get('功率区间2(秒)')) else None,
                            power_zone_3_seconds=int(row['功率区间3(秒)']) if pd.notna(row.get('功率区间3(秒)')) else None,
                            power_zone_4_seconds=int(row['功率区间4(秒)']) if pd.notna(row.get('功率区间4(秒)')) else None,
                            power_zone_5_seconds=int(row['功率区间5(秒)']) if pd.notna(row.get('功率区间5(秒)')) else None,
                            aerobic_training_effect=float(row['有氧训练效果']) if pd.notna(row.get('有氧训练效果')) else None,
                            anaerobic_training_effect=float(row['无氧训练效果']) if pd.notna(row.get('无氧训练效果')) else None,
                            training_effect_label=str(row['训练效果标签']) if pd.notna(row.get('训练效果标签')) else None,
                            training_load=int(row['训练负荷']) if pd.notna(row.get('训练负荷')) else None,
                            activity_calories=int(row['活动卡路里']) if pd.notna(row.get('活动卡路里')) else None,
                            basal_metabolism_calories=int(row['基础代谢卡路里']) if pd.notna(row.get('基础代谢卡路里')) else None,
                            estimated_sweat_loss_ml=int(row['估算失水量(ml)']) if pd.notna(row.get('估算失水量(ml)')) else None,
                            moderate_intensity_minutes=int(row['中等强度时长(分)']) if pd.notna(row.get('中等强度时长(分)')) else None,
                            vigorous_intensity_minutes=int(row['高强度时长(分)']) if pd.notna(row.get('高强度时长(分)')) else None,
                            body_battery_change=int(row['Body Battery变化']) if pd.notna(row.get('Body Battery变化')) else None,
                            add_ts=now_ts,
                            last_modify_ts=now_ts,
                            data_source='garmin_import'
                        )

                    batch_records.append(record)
                    success_count += 1

                    # 批量提交(每100条)
                    if len(batch_records) >= 100:
                        session.bulk_save_objects(batch_records)
                        session.commit()
                        print(f"   已处理 {success_count}/{len(df)} 条记录...")
                        batch_records = []

                except Exception as e:
                    failed_count += 1
                    print(f"   第{idx+1}行导入失败: {e}")
                    session.rollback()

            # 提交剩余记录
            if batch_records:
                session.bulk_save_objects(batch_records)
                session.commit()

            print(f"\n导入完成!")
            print(f"   成功: {success_count} 条")
            print(f"   失败: {failed_count} 条")

            return {
                'success': success_count,
                'failed': failed_count,
                'total': len(df)
            }

        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def run(self, truncate_first: bool = False):
        """
        执行完整导入流程

        Args:
            truncate_first: 是否覆盖写入(先清空表)

        Returns:
            dict: 导入结果统计
        """
        print("="*80)
        print(f"训练数据导入工具 (SQLAlchemy ORM) - 数据源: {self.data_source.upper()}")
        print("="*80)

        try:
            # 加载数据
            df = self.load_data()

            # 清洗数据
            df = self.clean_data(df)

            # 导入数据库
            result = self.import_to_db(df, truncate_first=truncate_first)

            print("\n✅ 导入成功!")
            return result

        except Exception as e:
            print(f"\n❌ 导入失败: {e}")
            import traceback
            traceback.print_exc()
            raise  # 重新抛出异常供调用方处理


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description='训练数据导入工具')
    parser.add_argument('--source', type=str, default='keep', choices=['keep', 'garmin'],
                        help='数据源类型 (keep 或 garmin)')
    parser.add_argument('--file', type=str, help='数据文件路径')
    parser.add_argument('--truncate', action='store_true',
                        help='覆盖写入模式(先清空表)')

    args = parser.parse_args()

    # 如果未指定文件,使用默认路径
    if not args.file:
        if args.source == 'keep':
            data_file = Path(project_root) / "data" / "406099.xlsx"
        else:
            data_file = Path(project_root) / "data" / "garmin_activities.csv"
    else:
        data_file = Path(args.file)

    # 检查文件是否存在
    if not data_file.exists():
        print(f"错误: 数据文件不存在 - {data_file}")
        if args.source == 'keep':
            print("请将Keep数据文件放在 data/ 目录下,或使用 --file 参数指定路径")
        else:
            print("请将Garmin数据CSV文件放在 data/ 目录下,或使用 --file 参数指定路径")
        sys.exit(1)

    # 执行导入
    importer = TrainingDataImporter(str(data_file), data_source=args.source)
    importer.run(truncate_first=args.truncate)


if __name__ == "__main__":
    main()
