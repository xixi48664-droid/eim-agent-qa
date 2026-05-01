-- ============================================
-- EIM Agent QA 数据库初始化脚本
-- 与 docs/design/design.md 第6章数据库设计保持一致
-- ============================================

CREATE DATABASE IF NOT EXISTS eim_agent_qa
    DEFAULT CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE eim_agent_qa;

-- 用户表（design.md 表1）
CREATE TABLE IF NOT EXISTS `user` (
    user_id         VARCHAR(32)     NOT NULL COMMENT '用户唯一标识',
    username        VARCHAR(50)     NOT NULL COMMENT '用户名，唯一不可重复',
    password        VARCHAR(100)    NOT NULL COMMENT '密码，哈希存储',
    email           VARCHAR(100)    NULL     COMMENT '邮箱',
    phone           VARCHAR(20)     NULL     COMMENT '手机号',
    role            VARCHAR(20)     NOT NULL DEFAULT 'user'    COMMENT '用户角色，取值：user/admin',
    status          VARCHAR(20)     NOT NULL DEFAULT 'enabled' COMMENT '用户状态，取值：enabled/disabled',
    create_time     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '注册时间',
    last_login_time DATETIME        NULL     COMMENT '最后登录时间',
    PRIMARY KEY (user_id),
    UNIQUE KEY uk_username (username)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 元器件表（design.md 表2）
CREATE TABLE IF NOT EXISTS `component` (
    component_id    VARCHAR(32)     NOT NULL COMMENT '元器件唯一标识',
    model           VARCHAR(100)    NOT NULL COMMENT '元器件型号',
    type            VARCHAR(50)     NULL     COMMENT '元器件类型（如：电阻、电容、芯片）',
    package_type    VARCHAR(50)     NULL     COMMENT '封装类型（如：SOP、DIP）',
    manufacturer    VARCHAR(100)    NULL     COMMENT '制造商信息',
    datasheet_url   VARCHAR(255)    NULL     COMMENT '数据手册链接',
    image_url       VARCHAR(255)    NULL     COMMENT '元器件图片地址',
    create_time     DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '数据录入时间',
    PRIMARY KEY (component_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 元器件参数表（design.md 表3）
CREATE TABLE IF NOT EXISTS `component_param` (
    param_id        VARCHAR(32)     NOT NULL COMMENT '参数唯一标识',
    component_id    VARCHAR(32)     NOT NULL COMMENT '所属元器件编号',
    param_name      VARCHAR(100)    NOT NULL COMMENT '参数名称（如：电压、功率）',
    param_value     VARCHAR(100)    NOT NULL COMMENT '参数值（如：5）',
    param_unit      VARCHAR(50)     NULL     COMMENT '参数单位（如：V、W、Ω）',
    PRIMARY KEY (param_id),
    FOREIGN KEY (component_id) REFERENCES `component`(component_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;

-- 操作日志表（design.md 表9）
CREATE TABLE IF NOT EXISTS `operation_log` (
    log_id           VARCHAR(32)     NOT NULL COMMENT '日志唯一标识',
    user_id          VARCHAR(32)     NULL     COMMENT '操作人编号',
    operation_type   VARCHAR(100)    NOT NULL COMMENT '操作类型（如：登录、查询、删除）',
    operation_target VARCHAR(100)    NULL     COMMENT '操作对象（如：用户、元器件、规范库）',
    operation_time   DATETIME        NOT NULL DEFAULT CURRENT_TIMESTAMP COMMENT '操作发生时间',
    operation_result VARCHAR(50)     NULL     COMMENT '操作结果（成功/失败）',
    PRIMARY KEY (log_id),
    FOREIGN KEY (user_id) REFERENCES `user`(user_id)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4;
