-- ============================================================
-- EIM Agent QA 数据库初始化脚本
-- 使用方法: mysql -u root -p < backend/scripts/init_db.sql
-- 或: 直接复制到 MySQL 客户端执行
-- ============================================================

CREATE DATABASE IF NOT EXISTS eim_agent_qa CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci;
USE eim_agent_qa;

-- ============================================================
-- 用户表
-- ============================================================
CREATE TABLE IF NOT EXISTS `user` (
    `user_id`           VARCHAR(32)   NOT NULL COMMENT '用户唯一标识',
    `username`          VARCHAR(50)   NOT NULL COMMENT '用户名，不可重复',
    `password`          VARCHAR(100)  NOT NULL COMMENT '密码，哈希存储',
    `email`             VARCHAR(100)  DEFAULT NULL COMMENT '邮箱',
    `phone`             VARCHAR(20)   DEFAULT NULL COMMENT '手机号',
    `role`              VARCHAR(20)   NOT NULL DEFAULT 'user' COMMENT '角色: user/admin',
    `status`            VARCHAR(20)   NOT NULL DEFAULT 'enabled' COMMENT '状态: enabled/disabled',
    `department`        VARCHAR(100)  DEFAULT NULL COMMENT '部门',
    `avatar`            VARCHAR(500)  DEFAULT NULL COMMENT '头像URL',
    `reset_token`       VARCHAR(255)  DEFAULT NULL COMMENT '密码重置令牌',
    `reset_token_expiry` DATETIME     DEFAULT NULL COMMENT '重置令牌过期时间',
    `create_time`       DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    `last_login_time`   DATETIME      DEFAULT NULL COMMENT '最后登录时间',
    PRIMARY KEY (`user_id`),
    UNIQUE KEY `uk_username` (`username`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 元器件表
-- ============================================================
CREATE TABLE IF NOT EXISTS `component` (
    `component_id`   VARCHAR(32)   NOT NULL COMMENT '元器件唯一标识',
    `model`          VARCHAR(100)  NOT NULL COMMENT '元器件型号',
    `type`           VARCHAR(255)  DEFAULT NULL COMMENT '类型分类路径',
    `package_type`   VARCHAR(50)   DEFAULT NULL COMMENT '封装类型',
    `manufacturer`   VARCHAR(100)  DEFAULT NULL COMMENT '制造商',
    `datasheet_url`  VARCHAR(1000) DEFAULT NULL COMMENT '数据手册URL',
    `image_url`      VARCHAR(1000) DEFAULT NULL COMMENT '图片URL',
    `create_time`    DATETIME      NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '录入时间',
    `update_time`    DATETIME      DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP COMMENT '更新时间',
    PRIMARY KEY (`component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 元器件参数表
-- ============================================================
CREATE TABLE IF NOT EXISTS `component_param` (
    `param_id`      VARCHAR(32)  NOT NULL COMMENT '参数唯一标识',
    `component_id`  VARCHAR(32)  NOT NULL COMMENT '所属元器件编号',
    `param_name`    VARCHAR(100) NOT NULL COMMENT '参数名称',
    `param_value`   VARCHAR(100) NOT NULL COMMENT '参数值',
    `param_unit`    VARCHAR(50)  DEFAULT NULL COMMENT '参数单位',
    PRIMARY KEY (`param_id`),
    KEY `component_id` (`component_id`),
    CONSTRAINT `component_param_ibfk_1` FOREIGN KEY (`component_id`) REFERENCES `component` (`component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 聊天会话表
-- ============================================================
CREATE TABLE IF NOT EXISTS `chat_session` (
    `session_id` VARCHAR(32)  NOT NULL,
    `user_id`    VARCHAR(32)  NOT NULL,
    `title`      VARCHAR(200) DEFAULT NULL,
    `create_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `update_time` DATETIME    NOT NULL DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    PRIMARY KEY (`session_id`),
    KEY `user_id` (`user_id`),
    CONSTRAINT `chat_session_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 聊天消息表
-- ============================================================
CREATE TABLE IF NOT EXISTS `chat_message` (
    `message_id`  VARCHAR(32)  NOT NULL,
    `session_id`  VARCHAR(32)  NOT NULL,
    `sender_type` VARCHAR(20)  NOT NULL COMMENT 'user/bot',
    `content`     TEXT         DEFAULT NULL,
    `image_url`   VARCHAR(255) DEFAULT NULL,
    `source_info` TEXT         DEFAULT NULL COMMENT '来源信息(JSON)',
    `create_time` DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP,
    `feedback`    VARCHAR(10)  DEFAULT NULL COMMENT 'like/dislike',
    PRIMARY KEY (`message_id`),
    KEY `session_id` (`session_id`),
    CONSTRAINT `chat_message_ibfk_1` FOREIGN KEY (`session_id`) REFERENCES `chat_session` (`session_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 操作日志表
-- ============================================================
CREATE TABLE IF NOT EXISTS `operation_log` (
    `log_id`            VARCHAR(32)  NOT NULL COMMENT '日志唯一标识',
    `user_id`           VARCHAR(32)  DEFAULT NULL COMMENT '操作人编号',
    `operation_type`    VARCHAR(100) NOT NULL COMMENT '操作类型',
    `operation_target`  VARCHAR(100) DEFAULT NULL COMMENT '操作对象',
    `operation_time`    DATETIME     NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作发生时间',
    `operation_result`  VARCHAR(50)  DEFAULT NULL COMMENT '操作结果',
    `response_time_ms`  BIGINT       DEFAULT NULL COMMENT '响应时间(ms)',
    PRIMARY KEY (`log_id`),
    KEY `user_id` (`user_id`),
    CONSTRAINT `operation_log_ibfk_1` FOREIGN KEY (`user_id`) REFERENCES `user` (`user_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 规范文档表
-- ============================================================
CREATE TABLE IF NOT EXISTS `process_standard` (
    `standard_id`     VARCHAR(32)  NOT NULL,
    `standard_code`   VARCHAR(100) DEFAULT NULL,
    `standard_name`   VARCHAR(200) NOT NULL,
    `section`         VARCHAR(100) DEFAULT NULL,
    `summary`         TEXT         DEFAULT NULL,
    `tags`            VARCHAR(255) DEFAULT NULL,
    `related_process` VARCHAR(255) DEFAULT NULL,
    PRIMARY KEY (`standard_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 教程表
-- ============================================================
CREATE TABLE IF NOT EXISTS `tutorial` (
    `tutorial_id`    VARCHAR(32)  NOT NULL,
    `process_name`   VARCHAR(100) NOT NULL,
    `total_steps`    INT          NOT NULL DEFAULT 0,
    `estimated_time` VARCHAR(50)  DEFAULT NULL,
    PRIMARY KEY (`tutorial_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- 教程步骤表
-- ============================================================
CREATE TABLE IF NOT EXISTS `tutorial_step` (
    `step_id`      VARCHAR(32)  NOT NULL,
    `tutorial_id`  VARCHAR(32)  NOT NULL,
    `step_no`      INT          NOT NULL,
    `step_title`   VARCHAR(200) DEFAULT NULL,
    `step_content` TEXT         NOT NULL,
    `image_url`    VARCHAR(255) DEFAULT NULL,
    `note`         TEXT         DEFAULT NULL,
    `faq`          TEXT         DEFAULT NULL,
    PRIMARY KEY (`step_id`),
    KEY `tutorial_id` (`tutorial_id`),
    CONSTRAINT `tutorial_step_ibfk_1` FOREIGN KEY (`tutorial_id`) REFERENCES `tutorial` (`tutorial_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;

-- ============================================================
-- Datasheet 记录表 (用于追踪导入状态)
-- ============================================================
CREATE TABLE IF NOT EXISTS `datasheet_record` (
    `record_id`     VARCHAR(32)  NOT NULL,
    `component_id`  VARCHAR(32)  NOT NULL,
    `source_url`    VARCHAR(1000) NOT NULL,
    `local_path`    VARCHAR(500) DEFAULT NULL,
    `file_hash`     VARCHAR(64)  DEFAULT NULL,
    `status`        VARCHAR(20)  NOT NULL COMMENT 'pending/downloaded/parsed/embedded/failed',
    `chunk_count`   INT          DEFAULT NULL,
    `error_message` TEXT         DEFAULT NULL,
    `create_time`   DATETIME     DEFAULT (now()),
    `update_time`   DATETIME     DEFAULT (now()),
    PRIMARY KEY (`record_id`),
    KEY `ix_datasheet_record_status` (`status`),
    KEY `ix_datasheet_record_file_hash` (`file_hash`),
    KEY `ix_datasheet_record_component_id` (`component_id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_unicode_ci;
