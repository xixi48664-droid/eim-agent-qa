-- ============================================================
-- EIM Agent QA 增量迁移脚本
-- 适用场景：已有数据库，只需补充缺失的字段/表
-- 使用方法: mysql -u root -p eim_agent_qa < backend/scripts/migrate_db_v2.sql
-- 注意: "Duplicate column" 错误表示字段已存在，忽略即可
-- ============================================================

USE eim_agent_qa;

-- user 表新增字段 (v2 更新)
ALTER TABLE `user` ADD COLUMN `department`          VARCHAR(100)  DEFAULT NULL COMMENT '部门';
ALTER TABLE `user` ADD COLUMN `avatar`              VARCHAR(500)  DEFAULT NULL COMMENT '头像URL';
ALTER TABLE `user` ADD COLUMN `reset_token`         VARCHAR(255)  DEFAULT NULL COMMENT '密码重置�?牌';
ALTER TABLE `user` ADD COLUMN `reset_token_expiry`  DATETIME      DEFAULT NULL COMMENT '重置令牌过期时间';

-- component 表新增字段 (v2 更新)
ALTER TABLE `component` ADD COLUMN `image_url` VARCHAR(1000) DEFAULT NULL COMMENT '图片URL';

-- chat_message 表新增字段 (v2 更新)
ALTER TABLE `chat_message` ADD COLUMN `feedback` VARCHAR(10) DEFAULT NULL COMMENT 'like/dislike';

-- operation_log 表新增字段 (v2 更新)
ALTER TABLE `operation_log` ADD COLUMN `response_time_ms` BIGINT DEFAULT NULL COMMENT '响应时间(ms)';

-- ============================================================
-- 新增表 (如已存在会报错，忽略即可)
-- ============================================================

CREATE TABLE IF NOT EXISTS `datasheet_record` (
    `record_id`     VARCHAR(32)   NOT NULL,
    `component_id`  VARCHAR(32)   NOT NULL,
    `source_url`    VARCHAR(1000) NOT NULL,
    `local_path`    VARCHAR(500)  DEFAULT NULL,
    `file_hash`     VARCHAR(64)   DEFAULT NULL,
    `status`        VARCHAR(20)   NOT NULL COMMENT 'pending/downloaded/parsed/embedded/failed',
    `chunk_count`   INT           DEFAULT NULL,
    `error_message` TEXT          DEFAULT NULL,
    `create_time`   DATETIME      DEFAULT (now()),
    `update_time`   DATETIME      DEFAULT (now()),
    PRIMARY KEY (`record_id`),
    KEY `ix_datasheet_record_status` (`status`),
    KEY `ix_datasheet_record_file_hash` (`file_hash`),
    KEY `ix_datasheet_record_component_id` (`component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
