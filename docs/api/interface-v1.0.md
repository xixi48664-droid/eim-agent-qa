# 基于智能体的电子信息制造业多模态图文问答系统

## 接口文档（V1.0）

---

## 1. 修订说明

本版接口文档根据新版实验报告进行设计，旨在规定**身份认证类**、**用户管理类**、**参数查询类**三类接口。主要依据有三点：

1. 系统角色分为普通用户和系统管理员，并采用 Web 形式访问，技术选型为 FastAPI + Vue3 + MySQL + Qdrant。
2. 用户认证部分明确写了：用户可通过邮箱或手机号注册和登录系统。
3. 参数查询和用户管理都已经在需求说明中写成了较完整的业务流程，因此接口设计不能再过度简化。参数查询要求支持型号或关键词检索、搜索结果列表、详细参数表和 Datasheet 链接；用户管理要求支持查看用户列表、禁用/启用、重置密码、查看操作日志。

---

## 2. 设计约定

### 2.1 接口前缀

```
/api/v1
```

### 2.2 数据格式

- 请求与响应统一使用 JSON
- 字符编码：UTF-8
- 时间格式：YYYY-MM-DD HH:mm:ss

### 2.3 认证方式

结合项目前后端分离架构，采用 JWT Token 方案。登录成功后返回 token，后续请求放在请求头中：

```
Authorization: Bearer <token>
```

### 2.4 统一响应结构

```json
{
  "code": 200,
  "message": "success",
  "data": {}
}
```

### 2.5 通用状态码

| code | 含义 |
|------|------|
| 200  | 成功 |
| 400  | 请求参数错误 |
| 401  | 未登录或认证失败 |
| 403  | 无权限 |
| 404  | 资源不存在 |
| 500  | 服务器内部错误 |

### 2.6 分页结构

所有列表类接口统一返回：

```json
{
  "pageNum": 1,
  "pageSize": 10,
  "total": 128,
  "records": []
}
```

---

## 3. 身份认证类接口

报告中明确写到用户可通过邮箱或手机号注册和登录系统，因此登录接口的账号字段不应再写成 `username`，而应使用更通用的 `account`。同时，系统角色是已有身份属性，应由后端认证后返回，而不是让前端登录时自行决定。

### 3.1 用户登录

**接口说明**

用户通过邮箱或手机号登录系统，登录成功后返回 token 与用户基础信息。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/auth/login` |
| 请求头 | Content-Type: application/json |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account | string | 是 | 邮箱或手机号 |
| password | string | 是 | 登录密码 |

**请求示例**

```json
{
  "account": "zhangsan@example.com",
  "password": "123456"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "登录成功",
  "data": {
    "token": "eyJhbGciOiJIUzI1NiJ9.xxx",
    "userId": "abc123def456",
    "account": "zhangsan@example.com",
    "role": "user",
    "status": "enabled"
  }
}
```

**失败响应示例**

```json
{
  "code": 401,
  "message": "账号或密码错误",
  "data": null
}
```

**说明**

- `role` 由后端根据用户表真实身份返回，前端不可传入
- `status=disabled` 的账号不允许登录
- 原型中的"登录角色"下拉框不参与认证逻辑
- 原型中的"注册 / 忘记密码 / 记住我"可保留为后续扩展，不纳入当前 MVP 联调范围

---

## 4. 用户管理类接口

报告已经明确：管理员可以查看用户列表、禁用/启用用户、重置用户密码、查看用户操作日志。所以这一类接口应拆成多条，而不是只做一个总接口。

> 以下接口均需管理员权限，请求头必须携带 `Authorization: Bearer <token>`。

### 4.1 用户列表查询

**接口说明**

管理员分页查询用户列表，支持按用户名、邮箱、注册时间、状态筛选。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/users` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 否 | 用户名筛选（模糊） |
| email | string | 否 | 邮箱筛选（模糊） |
| status | string | 否 | 用户状态：enabled / disabled |
| registerStart | string | 否 | 注册开始时间 |
| registerEnd | string | 否 | 注册结束时间 |
| pageNum | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

**请求示例**

```
GET /api/v1/admin/users?username=zhang&status=enabled&pageNum=1&pageSize=10
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "pageNum": 1,
    "pageSize": 10,
    "total": 128,
    "records": [
      {
        "userId": "abc123",
        "username": "zhangsan",
        "email": "zhangsan@example.com",
        "status": "enabled",
        "registerTime": "2024-01-15 09:00:00",
        "lastLoginTime": "2026-04-24 08:55:00"
      }
    ]
  }
}
```

**失败响应示例**

```json
{
  "code": 403,
  "message": "无权限访问该接口",
  "data": null
}
```

### 4.2 启用/禁用用户

**接口说明**

管理员修改用户账号状态，禁用后该用户不能登录。

| 项目 | 内容 |
|------|------|
| 请求方式 | PATCH |
| 请求路径 | `/api/v1/admin/users/{userId}/status` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| status | string | 是 | 目标状态：enabled / disabled |

**请求示例**

```json
{
  "status": "disabled"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "用户状态更新成功",
  "data": {
    "userId": "abc123",
    "status": "disabled"
  }
}
```

### 4.3 重置用户密码

**接口说明**

管理员为指定用户重置密码，返回临时密码。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/users/{userId}/reset-password` |

**请求参数**

当前 MVP 不要求 Body 参数，由后端自动生成 8 位临时密码。

**成功响应示例**

```json
{
  "code": 200,
  "message": "密码重置成功",
  "data": {
    "userId": "abc123",
    "tempPassword": "Abc@2026"
  }
}
```

### 4.4 查看用户操作日志

**接口说明**

管理员查看指定用户的操作日志，至少应覆盖登录、参数查询、拍照识别等行为。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/users/{userId}/logs` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| operationType | string | 否 | 操作类型，如 login、query、recognize |
| startTime | string | 否 | 开始时间 |
| endTime | string | 否 | 结束时间 |
| pageNum | int | 否 | 页码 |
| pageSize | int | 否 | 每页条数 |

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "pageNum": 1,
    "pageSize": 10,
    "total": 2,
    "records": [
      {
        "logId": "xyz001",
        "operationType": "login",
        "operationDesc": "登录 系统",
        "operationTime": "2026-04-24 08:55:00"
      },
      {
        "logId": "xyz002",
        "operationType": "query",
        "operationDesc": "查询元器件 STM32F103C8T6 参数",
        "operationTime": "2026-04-24 09:10:12"
      }
    ]
  }
}
```

---

## 5. 参数查询类接口

报告中参数查询的完整流程：

- 输入型号或关键词
- 系统查询数据库
- 如有多个匹配，先展示搜索结果列表
- 用户选择具体型号
- 再展示详细参数表
- 并提供官方 Datasheet 链接

元器件记录的核心字段：型号、类型、封装、厂商、核心参数 JSON、Datasheet 链接、图片链接、更新时间。

> 以下接口需登录，请求头必须携带 `Authorization: Bearer <token>`。

### 5.1 元器件搜索

**接口说明**

用户通过输入型号或关键词搜索元器件，返回候选列表。对应参数查询用例中的"展示搜索结果列表"阶段。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/components/search` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| keyword | string | 是 | 元器件型号或关键词 |
| pageNum | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

**请求示例**

```
GET /api/v1/components/search?keyword=STM32F103C8T6&pageNum=1&pageSize=10
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "pageNum": 1,
    "pageSize": 10,
    "total": 2,
    "records": [
      {
        "componentId": "def456",
        "model": "STM32F103C8T6",
        "type": "MCU",
        "packageType": "LQFP48",
        "manufacturer": "STMicroelectronics"
      },
      {
        "componentId": "def457",
        "model": "STM32F103CBT6",
        "type": "MCU",
        "packageType": "LQFP48",
        "manufacturer": "STMicroelectronics"
      }
    ]
  }
}
```

**无结果响应示例**

```json
{
  "code": 404,
  "message": "未查询到匹配的元器件",
  "data": null
}
```

### 5.2 元器件参数详情

**接口说明**

根据用户选择的元器件，返回完整参数表、Datasheet 链接及相关信息。对应参数查询用例中的"展示详细参数表"阶段。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/components/{componentId}` |

**路径参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| componentId | string | 是 | 元器件主键 ID |

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "componentId": "def456",
    "model": "STM32F103C8T6",
    "type": "MCU",
    "packageType": "LQFP48",
    "manufacturer": "STMicroelectronics",
    "coreParams": {
      "内核": "ARM Cortex-M3",
      "主频": "72MHz",
      "Flash": "64KB",
      "RAM": "20KB",
      "工作电压": "2.0-3.6V",
      "引脚数": "48"
    },
    "datasheetUrl": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
    "imageUrl": "https://example.com/images/stm32f103c8t6.png",
    "updatedAt": "2026-04-20 10:20:00"
  }
}
```

**失败响应示例**

```json
{
  "code": 404,
  "message": "元器件不存在",
  "data": null
}
```

**说明**

- `coreParams` 对应报告里的"核心参数 JSON"，由 `component_param` 表聚合生成
- `datasheetUrl` 对应报告里的"Datasheet 链接"
- `imageUrl` 对应报告里的"图片链接"
- `updatedAt` 对应报告里的"更新时间"

---

## 6. MVP 实现说明

### 6.1 实现范围

本次 MVP 阶段已实现以上 3 类接口的全部端点（共 7 个）。

**暂不实现：** 注册、角色选择、拍照识件、OCR、大模型问答、向量检索、服务监控、知识库维护。

### 6.2 架构分层

```
api/ (Controller)  →  services/ (Service)  →  repositories/ (Repository)  →  entities/ (Entity)
       ↕                        ↕
   schemas/ (DTO)          core/ (Config, Security, Response)
```

**类名与设计文档对照：**

| 设计文档类 | 文件 | 职责 |
|-----------|------|------|
| UserController (4.1) | `api/user_controller.py` | 登录请求接收 |
| AdminController (4.4) | `api/admin_controller.py` | 管理员请求接收 |
| QaController (4.3) | `api/qa_controller.py` | 参数查询请求接收 |
| UserService (4.8) | `services/user_service.py` | 认证业务逻辑 |
| AdminService (4.14) | `services/admin_service.py` | 管理员业务逻辑 |
| QueryService (4.10) | `services/query_service.py` | 参数查询业务逻辑 |
| UserRepository (4.16) | `repositories/user_repository.py` | 用户数据访问 |
| ComponentRepository (4.17) | `repositories/component_repository.py` | 元器件数据访问 |
| HistoryRepository (4.20) | `repositories/history_repository.py` | 操作日志数据访问 |

### 6.3 登录逻辑与角色判断

**登录流程：**

1. 用户提交 `account`（邮箱或手机号）+ `password`
2. `UserService.authenticate()` → 按邮箱或手机号查询用户
3. 校验 `status == "enabled"`（禁用账号拒绝登录）
4. `verifyPassword()` bcrypt 哈希校验
5. 生成 JWT，记录登录日志
6. 返回 `{ token, userId, account, role, status }`

**角色来源：**

- `role` 由 `user` 表预置，种子数据已写入 admin（admin/admin123）和 user（user/user123）
- 登录成功后 `role` 随响应返回，前端据此跳转：`admin` → 管理端，`user` → 用户端
- **前端不可传递 role 参数，角色只能由后端数据库决定**

### 6.4 权限矩阵

| 接口 | 未登录 | 普通用户 | 管理员 |
|------|:------:|:--------:|:------:|
| POST `/api/v1/auth/login` | ✓ | ✓ | ✓ |
| GET `/api/v1/admin/users` | 401 | 403 | ✓ |
| PATCH `/api/v1/admin/users/{userId}/status` | 401 | 403 | ✓ |
| POST `/api/v1/admin/users/{userId}/reset-password` | 401 | 403 | ✓ |
| GET `/api/v1/admin/users/{userId}/logs` | 401 | 403 | ✓ |
| GET `/api/v1/components/search` | 401 | ✓ | ✓ |
| GET `/api/v1/components/{componentId}` | 401 | ✓ | ✓ |

### 6.5 前端对接

**Token 使用：**

```
Authorization: Bearer <token>
```

**根据 role 跳转：**

```javascript
if (role === 'admin') {
  router.push('/admin/dashboard');
} else {
  router.push('/user/home');
}
```

**Token 过期处理：** 默认有效期 24 小时（`JWT_EXPIRE_MINUTES=1440`），前端收到 401 时应跳转登录页。

### 6.6 运行步骤

```bash
# 1. 进入后端目录
cd backend

# 2. 安装依赖
pip install -r requirements.txt

# 3. 配置环境变量
cp .env.example .env
# 编辑 .env，填写 DATABASE_URL 和 JWT_SECRET_KEY

# 4. 初始化数据库（建表）
mysql -u root -p < ../database/mysql/schema.sql

# 5. 写入种子数据
cd ../database/mysql
python seed.py

# 6. 启动服务
cd ../../backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000

# Swagger 文档地址: http://localhost:8000/docs
```

### 6.7 接口测试示例

**1) 管理员登录**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account": "admin@example.com", "password": "admin123"}'
```

**2) 普通用户登录**

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"account": "user@example.com", "password": "user123"}'
```

**3) 管理员查询用户列表**

```bash
TOKEN="<管理员登录返回的 token>"

curl -X GET "http://localhost:8000/api/v1/admin/users?pageNum=1&pageSize=10" \
  -H "Authorization: Bearer $TOKEN"
```

**4) 普通用户访问管理员接口（预期 403）**

```bash
USER_TOKEN="<普通用户登录返回的 token>"

curl -X GET "http://localhost:8000/api/v1/admin/users" \
  -H "Authorization: Bearer $USER_TOKEN"
```

**5) 查询元器件**

```bash
curl -X GET "http://localhost:8000/api/v1/components/search?keyword=STM32" \
  -H "Authorization: Bearer $TOKEN"
```

**6) 查看元器件详情**

```bash
curl -X GET "http://localhost:8000/api/v1/components/{componentId}" \
  -H "Authorization: Bearer $TOKEN"
```

**7) 禁用用户**

```bash
curl -X PATCH "http://localhost:8000/api/v1/admin/users/{userId}/status" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"status": "disabled"}'
```

**8) 重置用户密码**

```bash
curl -X POST "http://localhost:8000/api/v1/admin/users/{userId}/reset-password" \
  -H "Authorization: Bearer $TOKEN"
```

**9) 查看用户操作日志**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/{userId}/logs" \
  -H "Authorization: Bearer $TOKEN"
```

### 6.8 数据库表

| 表名 | 字段 |
|------|------|
| `user` | user_id, username, password, email, phone, role, status, create_time, last_login_time |
| `component` | component_id, model, type, package_type, manufacturer, datasheet_url, image_url, create_time |
| `component_param` | param_id, component_id(FK), param_name, param_value, param_unit |
| `operation_log` | log_id, user_id(FK), operation_type, operation_target, operation_time, operation_result |
