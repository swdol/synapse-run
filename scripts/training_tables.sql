-- ============================================
-- 中长跑训练数据表结构
-- 用于存储用户历史训练记录,供AI Agent分析挖掘
-- ============================================

-- ----------------------------
-- 训练记录主表 - Keep数据源
-- ----------------------------
DROP TABLE IF EXISTS `training_records_keep`;
CREATE TABLE `training_records_keep` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `user_id` VARCHAR(64) DEFAULT 'default_user' COMMENT '用户ID (预留字段,支持多用户)',

    -- 基础训练信息
    `exercise_type` VARCHAR(32) NOT NULL COMMENT '运动类型 (跑步/骑行/游泳等)',
    `duration_seconds` INT NOT NULL COMMENT '运动时长(秒)',
    `start_time` DATETIME NOT NULL COMMENT '开始时间',
    `end_time` DATETIME NOT NULL COMMENT '结束时间',

    -- 运动指标
    `calories` INT DEFAULT NULL COMMENT '消耗卡路里',
    `distance_meters` DECIMAL(10, 2) DEFAULT NULL COMMENT '运动距离(米)',
    `avg_heart_rate` INT DEFAULT NULL COMMENT '平均心率',
    `max_heart_rate` INT DEFAULT NULL COMMENT '最大心率',

    -- 详细数据 (JSON格式存储)
    `heart_rate_data` LONGTEXT DEFAULT NULL COMMENT '心率记录数组 (JSON格式: ["108","109",...])',

    -- 元数据
    `add_ts` BIGINT NOT NULL COMMENT '记录添加时间戳',
    `last_modify_ts` BIGINT NOT NULL COMMENT '记录最后修改时间戳',
    `data_source` VARCHAR(64) DEFAULT 'keep_import' COMMENT '数据来源 (Keep运动APP)',

    PRIMARY KEY (`id`),
    KEY `idx_training_user_id` (`user_id`),
    KEY `idx_training_start_time` (`start_time`),
    KEY `idx_training_exercise_type` (`exercise_type`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='训练记录表 - Keep数据源';

-- ----------------------------
-- 训练记录主表 - Garmin数据源
-- ----------------------------
DROP TABLE IF EXISTS `training_records_garmin`;
CREATE TABLE `training_records_garmin` (
    `id` INT NOT NULL AUTO_INCREMENT COMMENT '自增ID',
    `user_id` VARCHAR(64) DEFAULT 'default_user' COMMENT '用户ID (预留字段,支持多用户)',

    -- 基础训练信息
    `activity_id` VARCHAR(128) DEFAULT NULL COMMENT 'Garmin活动ID',
    `activity_name` VARCHAR(255) DEFAULT NULL COMMENT '活动名称',
    `sport_type` VARCHAR(64) NOT NULL COMMENT '运动类型',
    `start_time_gmt` DATETIME NOT NULL COMMENT '开始时间(GMT)',
    `end_time_gmt` DATETIME NOT NULL COMMENT '结束时间(GMT)',
    `duration_seconds` INT NOT NULL COMMENT '时长(秒)',
    `distance_meters` DECIMAL(10, 2) DEFAULT NULL COMMENT '距离(米)',

    -- 心率指标
    `avg_heart_rate` INT DEFAULT NULL COMMENT '平均心率',
    `max_heart_rate` INT DEFAULT NULL COMMENT '最大心率',
    `hr_zone_1_seconds` INT DEFAULT NULL COMMENT '心率区间1(秒)',
    `hr_zone_2_seconds` INT DEFAULT NULL COMMENT '心率区间2(秒)',
    `hr_zone_3_seconds` INT DEFAULT NULL COMMENT '心率区间3(秒)',
    `hr_zone_4_seconds` INT DEFAULT NULL COMMENT '心率区间4(秒)',
    `hr_zone_5_seconds` INT DEFAULT NULL COMMENT '心率区间5(秒)',

    -- 步频步幅指标
    `avg_cadence` INT DEFAULT NULL COMMENT '平均步频(步/分)',
    `max_cadence` INT DEFAULT NULL COMMENT '最大步频',
    `avg_stride_length_cm` DECIMAL(10, 2) DEFAULT NULL COMMENT '平均步幅(cm)',
    `avg_vertical_oscillation_cm` DECIMAL(10, 2) DEFAULT NULL COMMENT '平均垂直振幅(cm)',
    `avg_ground_contact_time_ms` INT DEFAULT NULL COMMENT '平均触地时间(ms)',
    `vertical_ratio_percent` DECIMAL(10, 2) DEFAULT NULL COMMENT '垂直振幅比(%)',
    `total_steps` INT DEFAULT NULL COMMENT '总步数',

    -- 功率指标
    `avg_power_watts` INT DEFAULT NULL COMMENT '平均功率(W)',
    `max_power_watts` INT DEFAULT NULL COMMENT '最大功率(W)',
    `normalized_power_watts` INT DEFAULT NULL COMMENT '标准化功率(W)',
    `power_zone_1_seconds` INT DEFAULT NULL COMMENT '功率区间1(秒)',
    `power_zone_2_seconds` INT DEFAULT NULL COMMENT '功率区间2(秒)',
    `power_zone_3_seconds` INT DEFAULT NULL COMMENT '功率区间3(秒)',
    `power_zone_4_seconds` INT DEFAULT NULL COMMENT '功率区间4(秒)',
    `power_zone_5_seconds` INT DEFAULT NULL COMMENT '功率区间5(秒)',

    -- 速度指标
    `avg_speed_mps` DECIMAL(10, 2) DEFAULT NULL COMMENT '平均速度(m/s)',
    `max_speed_mps` DECIMAL(10, 2) DEFAULT NULL COMMENT '最大速度(m/s)',

    -- 训练效果指标
    `aerobic_training_effect` DECIMAL(4, 2) DEFAULT NULL COMMENT '有氧训练效果',
    `anaerobic_training_effect` DECIMAL(4, 2) DEFAULT NULL COMMENT '无氧训练效果',
    `training_effect_label` VARCHAR(64) DEFAULT NULL COMMENT '训练效果标签',
    `training_load` INT DEFAULT NULL COMMENT '训练负荷',

    -- 卡路里和代谢指标
    `activity_calories` INT DEFAULT NULL COMMENT '活动卡路里',
    `basal_metabolism_calories` INT DEFAULT NULL COMMENT '基础代谢卡路里',
    `estimated_sweat_loss_ml` INT DEFAULT NULL COMMENT '估算失水量(ml)',

    -- 强度时长
    `moderate_intensity_minutes` INT DEFAULT NULL COMMENT '中等强度时长(分)',
    `vigorous_intensity_minutes` INT DEFAULT NULL COMMENT '高强度时长(分)',

    -- 其他指标
    `body_battery_change` INT DEFAULT NULL COMMENT 'Body Battery变化',

    -- 元数据
    `add_ts` BIGINT NOT NULL COMMENT '记录添加时间戳',
    `last_modify_ts` BIGINT NOT NULL COMMENT '记录最后修改时间戳',
    `data_source` VARCHAR(64) DEFAULT 'garmin_import' COMMENT '数据来源 (Garmin设备)',

    PRIMARY KEY (`id`),
    KEY `idx_garmin_user_id` (`user_id`),
    KEY `idx_garmin_start_time` (`start_time_gmt`),
    KEY `idx_garmin_sport_type` (`sport_type`),
    KEY `idx_garmin_activity_id` (`activity_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci COMMENT='训练记录表 - Garmin数据源';

-- ----------------------------
-- 训练统计视图 - Keep数据源
-- ----------------------------
CREATE OR REPLACE VIEW `training_stats_keep` AS
SELECT
    `user_id`,
    `exercise_type`,
    COUNT(*) as total_sessions,
    SUM(`duration_seconds`) as total_duration,
    AVG(`duration_seconds`) as avg_duration,
    SUM(`distance_meters`) as total_distance,
    AVG(`distance_meters`) as avg_distance,
    AVG(`avg_heart_rate`) as overall_avg_heart_rate,
    MAX(`max_heart_rate`) as peak_heart_rate,
    DATE_FORMAT(`start_time`, '%Y-%m') as month
FROM `training_records_keep`
GROUP BY `user_id`, `exercise_type`, DATE_FORMAT(`start_time`, '%Y-%m');

-- ----------------------------
-- 训练统计视图 - Garmin数据源
-- ----------------------------
CREATE OR REPLACE VIEW `training_stats_garmin` AS
SELECT
    `user_id`,
    `sport_type` as exercise_type,
    COUNT(*) as total_sessions,
    SUM(`duration_seconds`) as total_duration,
    AVG(`duration_seconds`) as avg_duration,
    SUM(`distance_meters`) as total_distance,
    AVG(`distance_meters`) as avg_distance,
    AVG(`avg_heart_rate`) as overall_avg_heart_rate,
    MAX(`max_heart_rate`) as peak_heart_rate,
    AVG(`avg_cadence`) as overall_avg_cadence,
    AVG(`avg_power_watts`) as overall_avg_power,
    AVG(`training_load`) as avg_training_load,
    DATE_FORMAT(`start_time_gmt`, '%Y-%m') as month
FROM `training_records_garmin`
GROUP BY `user_id`, `sport_type`, DATE_FORMAT(`start_time_gmt`, '%Y-%m');

-- ----------------------------
-- 索引优化说明
-- ----------------------------
-- 1. user_id: 支持多用户查询
-- 2. start_time: 支持时间范围查询 (最近7天/30天/1年等)
-- 3. exercise_type: 支持按运动类型筛选
