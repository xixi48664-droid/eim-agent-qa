# 基于智能体的电子信息制造业多模态图文问答系统

## 接口文档（V1.0）

---

## 1. 修订说明

本版接口文档根据新版实验报告进行设计，旨在规定**身份认证类**、**用户管理类**、**个人中心类**、**参数查询类**、**元器件管理类**、**规范管理类**、**教程管理类**、**服务监控类**、**问答历史类**、**文件管理类**、**拍照识件类**、**AI 综合问答类**、**流程指导类**、**规范文档类**十四类接口。主要依据有三点：

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

```json
{
  "code": 403,
  "message": "账号已被禁用",
  "data": null
}
```

**说明**

- `role` 由后端根据用户表真实身份返回，前端不可传入
- `status=disabled` 的账号不允许登录，返回 403
- 原型中的"登录角色"下拉框不参与认证逻辑

### 3.2 用户注册

**接口说明**

用户通过邮箱或手机号注册新账号。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/auth/register` |
| 请求头 | Content-Type: application/json |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account | string | 是 | 邮箱或手机号 |
| username | string | 是 | 用户名 |
| password | string | 是 | 登录密码（最少6位） |
| confirmPassword | string | 是 | 确认密码 |

**请求示例**

```json
{
  "account": "newuser@example.com",
  "username": "newuser",
  "password": "123456",
  "confirmPassword": "123456"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "注册成功",
  "data": {
    "userId": "abc123def456",
    "username": "newuser",
    "account": "newuser@example.com"
  }
}
```

**失败响应示例**

```json
{
  "code": 400,
  "message": "该邮箱或手机号已被注册",
  "data": null
}
```

### 3.3 用户登出

**接口说明**

用户登出系统，记录登出日志。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/auth/logout` |
| 认证 | 需携带 Token |

**成功响应示例**

```json
{
  "code": 200,
  "message": "已登出",
  "data": null
}
```
### 3.4 忘记密码

**接口说明**

用户通过邮箱或手机号申请密码重置，系统生成重置令牌。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/auth/forgot-password` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| account | string | 是 | 邮箱或手机号 |

**请求示例**

```json
{
  "account": "zhangsan@example.com"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "重置链接已发送",
  "data": null
}
```

### 3.5 通过令牌重置密码

**接口说明**

用户使用重置令牌修改密码。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/auth/reset-password` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| token | string | 是 | 密码重置令牌 |
| newPassword | string | 是 | 新密码（最少6位） |
| confirmPassword | string | 是 | 确认新密码 |

**请求示例**

```json
{
  "token": "abc123xyz",
  "newPassword": "654321",
  "confirmPassword": "654321"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "密码重置成功",
  "data": null
}
```

**失败响应示例**

```json
{
  "code": 400,
  "message": "重置令牌无效或已过期",
  "data": null
}
```

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

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| password | string | 否 | 指定新密码。不传则自动生成 8 位临时密码 |

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

### 4.5 批量启用/禁用用户

**接口说明**

管理员批量修改用户状态。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/users/batch-status` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| userIds | array | 是 | 用户 ID 列表 |
| status | string | 是 | 目标状态：enabled / disabled |

**请求示例**

```json
{
  "userIds": ["abc123", "def456"],
  "status": "disabled"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "已禁用2个用户",
  "data": {
    "affectedCount": 2,
    "failedIds": []
  }
}
```

### 4.6 批量删除用户

**接口说明**

管理员批量删除用户。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/users/batch-delete` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| userIds | array | 是 | 用户 ID 列表 |

**请求示例**

```json
{
  "userIds": ["abc123", "def456"]
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "已删除2个用户",
  "data": {
    "affectedCount": 2,
    "failedIds": []
  }
}
```

---

## 5. 个人中心类接口

> 以下接口需登录，请求头必须携带 `Authorization: Bearer <token>`。

### 5.1 查看个人信息

当前登录用户查看个人信息及活动统计。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/user/profile` |

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "userId": "abc123",
    "username": "zhangsan",
    "email": "zhangsan@example.com",
    "phone": "13800138000",
    "role": "user",
    "status": "enabled",
    "department": "研发部",
    "avatar": null,
    "registerTime": "2026-05-03 12:00:00",
    "lastLoginTime": "2026-05-03 13:00:00",
    "questionCount": 0,
    "savedRecordCount": 0,
    "exportReportCount": 0,
    "satisfactionScore": 0.0
  }
}
```

### 5.2 编辑个人信息

当前用户修改用户名、邮箱、手机号。

| 项目 | 内容 |
|------|------|
| 请求方式 | PUT |
| 请求路径 | `/api/v1/user/profile` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| username | string | 否 | 新用户名 |
| email | string | 否 | 新邮箱 |
| phone | string | 否 | 新手机号 |
| department | string | 否 | 部门 |
| avatar | string | 否 | 头像 URL |

**请求示例**

```json
{
  "phone": "13800138000"
}
```

### 5.3 修改密码

当前用户自行修改密码，需验证原密码。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/user/change-password` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| oldPassword | string | 是 | 原密码 |
| newPassword | string | 是 | 新密码（最少6位） |
| confirmPassword | string | 是 | 确认新密码 |

**请求示例**

```json
{
  "oldPassword": "123456",
  "newPassword": "654321",
  "confirmPassword": "654321"
}
```

**失败响应示例**

```json
{
  "code": 400,
  "message": "原密码错误",
  "data": null
}
```

### 5.4 活动统计

当前用户的操作活动统计。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/user/stats` |

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "totalOperations": 5,
    "loginCount": 3,
    "questionCount": 0,
    "savedRecordCount": 0,
    "exportReportCount": 0,
    "satisfactionScore": 0.0
  }
}
```

### 5.5 近期操作记录

当前用户的分页操作记录。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/user/activities` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| pageNum | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

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
        "logId": "log001",
        "operationType": "登录",
        "operationDesc": "登录 系统",
        "operationTime": "2026-05-03 13:00:00"
      }
    ]
  }
}
```

---
## 6. 参数查询类接口

报告中参数查询的完整流程：

- 输入型号或关键词
- 系统查询数据库
- 如有多个匹配，先展示搜索结果列表
- 用户选择具体型号
- 再展示详细参数表
- 并提供官方 Datasheet 链接

元器件记录的核心字段：型号、类型、封装、厂商、核心参数 JSON、Datasheet 链接、图片链接、更新时间。

> 以下接口需登录，请求头必须携带 `Authorization: Bearer <token>`。

### 6.1 元器件搜索

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

### 6.2 元器件参数详情

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

## 7. 元器件管理类接口

> 以下接口均需管理员权限，请求头必须携带 `Authorization: Bearer <token>`。

### 7.1 元器件列表查询

**接口说明**

管理员分页查询元器件列表，支持按型号、类型、厂商筛选。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/components` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 否 | 型号筛选（模糊） |
| type | string | 否 | 类型筛选（模糊） |
| manufacturer | string | 否 | 厂商筛选（模糊） |
| pageNum | int | 否 | 页码，默认 1 |
| pageSize | int | 否 | 每页条数，默认 10 |

**请求示例**

```
GET /api/v1/admin/components?type=MCU&pageNum=1&pageSize=10
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "pageNum": 1,
    "pageSize": 10,
    "total": 5,
    "records": [
      {
        "componentId": "abc123def456",
        "model": "STM32F103C8T6",
        "type": "MCU",
        "packageType": "LQFP48",
        "manufacturer": "STMicroelectronics",
        "datasheetUrl": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
        "imageUrl": null,
        "paramCount": 6,
        "createTime": "2026-05-01 12:00:00",
        "updateTime": "2026-05-03 10:30:00"
      }
    ]
  }
}
```

### 7.2 新增元器件

**接口说明**

管理员新增元器件记录，可同时添加多个参数。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/components` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 是 | 元器件型号 |
| type | string | 否 | 类型 |
| packageType | string | 否 | 封装类型 |
| manufacturer | string | 否 | 厂商 |
| datasheetUrl | string | 否 | Datasheet 链接 |
| imageUrl | string | 否 | 图片链接 |
| params | array | 否 | 参数列表 |

**params 子字段**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| paramName | string | 是 | 参数名称 |
| paramValue | string | 是 | 参数值 |
| paramUnit | string | 否 | 参数单位 |

**请求示例**

```json
{
  "model": "STM32F103C8T6",
  "type": "MCU",
  "packageType": "LQFP48",
  "manufacturer": "STMicroelectronics",
  "datasheetUrl": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
  "params": [
    { "paramName": "内核", "paramValue": "ARM Cortex-M3" },
    { "paramName": "主频", "paramValue": "72", "paramUnit": "MHz" },
    { "paramName": "Flash", "paramValue": "64", "paramUnit": "KB" }
  ]
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "新增元器件成功",
  "data": {
    "componentId": "abc123def456",
    "model": "STM32F103C8T6",
    "type": "MCU",
    "packageType": "LQFP48",
    "manufacturer": "STMicroelectronics",
    "datasheetUrl": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
    "imageUrl": null,
    "paramCount": 3,
    "createTime": "2026-05-03 12:00:00",
    "updateTime": "2026-05-03 12:00:00"
  }
}
```

**失败响应示例**

```json
{
  "code": 400,
  "message": "元器件型号已存在: STM32F103C8T6",
  "data": null
}
```

### 7.3 编辑元器件

**接口说明**

管理员编辑元器件信息及参数。传入的字段会覆盖旧值，未传的字段保持不变。params 传入时，先删除旧参数再写入新参数。

| 项目 | 内容 |
|------|------|
| 请求方式 | PUT |
| 请求路径 | `/api/v1/admin/components/{componentId}` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| model | string | 否 | 元器件型号 |
| type | string | 否 | 类型 |
| packageType | string | 否 | 封装类型 |
| manufacturer | string | 否 | 厂商 |
| datasheetUrl | string | 否 | Datasheet 链接 |
| imageUrl | string | 否 | 图片链接 |
| params | array | 否 | 参数列表（传 null 表示不修改） |

**成功响应示例**

```json
{
  "code": 200,
  "message": "更新元器件成功",
  "data": {
    "componentId": "abc123def456",
    "model": "STM32F103C8T6",
    "type": "MCU",
    "packageType": "LQFP64",
    "manufacturer": "STMicroelectronics",
    "datasheetUrl": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
    "imageUrl": null,
    "paramCount": 4,
    "createTime": "2026-05-01 12:00:00",
    "updateTime": "2026-05-03 12:05:00"
  }
}
```

### 7.4 删除元器件

**接口说明**

管理员删除元器件及其所有参数。

| 项目 | 内容 |
|------|------|
| 请求方式 | DELETE |
| 请求路径 | `/api/v1/admin/components/{componentId}` |

**成功响应示例**

```json
{
  "code": 200,
  "message": "删除元器件成功",
  "data": null
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

---
## 8. 规范管理类接口

> 以下接口均需管理员权限。

### 8.1 规范列表查询

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/standards` |

**请求参数:** standardName(否), standardCode(否), pageNum(否,默认1), pageSize(否,默认10)

### 8.2 新增规范

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/standards` |

**请求参数:** standardCode(否), standardName(是), section(否), summary(否), tags(否), relatedProcess(否)

### 8.3 编辑规范

| 项目 | 内容 |
|------|------|
| 请求方式 | PUT |
| 请求路径 | `/api/v1/admin/standards/{standardId}` |

请求参数同 8.2，所有字段可选。

### 8.4 删除规范

| 项目 | 内容 |
|------|------|
| 请求方式 | DELETE |
| 请求路径 | `/api/v1/admin/standards/{standardId}` |

---

## 9. 教程管理类接口

> 以下接口均需管理员权限。

### 9.1 教程列表查询

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/tutorials` |

**请求参数:** processName(否), pageNum(否), pageSize(否)

### 9.2 教程详情

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/tutorials/{tutorialId}` |

返回教程基本信息及全部步骤。

### 9.3 新增教程

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/admin/tutorials` |

**请求参数:** processName(是), estimatedTime(否), steps(是,步骤数组: stepNo/stepTitle/stepContent/imageUrl/note/faq)

### 9.4 编辑教程

| 项目 | 内容 |
|------|------|
| 请求方式 | PUT |
| 请求路径 | `/api/v1/admin/tutorials/{tutorialId}` |

`processName`、`estimatedTime`、`steps` 均为可选。传入 steps 时先删旧再写新。

### 9.5 删除教程

| 项目 | 内容 |
|------|------|
| 请求方式 | DELETE |
| 请求路径 | `/api/v1/admin/tutorials/{tutorialId}` |

---

## 10. 服务监控类接口

> 以下接口需管理员权限，请求头必须携带 `Authorization: Bearer <token>`。

### 10.1 获取服务监控数据

**接口说明**

管理员获取各外部服务的健康状态、API 调用统计及近期错误日志。

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/admin/monitor` |

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "overall": "healthy",
    "services": {
      "modelService": {"status": "available"},
      "ocrService": {"status": "available", "mode": "qwen-vl"},
      "vectorStore": {"status": "available", "mode": "qdrant-local", "points_count": 19},
      "fileStorage": {"status": "available"},
      "database": {"status": "available"}
    },
    "checkedAt": "2026-05-03 17:39:56",
    "apiStats": {
      "hours": 24,
      "totalCalls": 141,
      "qps": 0.002,
      "byType": [
        {"type": "AI 问答", "count": 35},
        {"type": "登录", "count": 70}
      ]
    },
    "latencyStats": {
      "hours": 24,
      "avgMs": 320.5,
      "maxMs": 1500.0,
      "count": 141
    },
    "timeSeries": [
      {"time": "2026-05-03T00:00:00", "count": 12},
      {"time": "2026-05-03T01:00:00", "count": 8}
    ],
    "recentErrors": {
      "hours": 24,
      "total": 0,
      "records": []
    }
  }
}
```

**说明**

- `overall` 取值 `healthy`（全部可用）或 `degraded`（部分异常）
- `services` 包含模型服务、OCR 服务、向量数据库、文件存储、数据库 5 项健康状态
- `apiStats` 统计近 24 小时内各类型接口调用次数及 QPS
- `latencyStats` 统计推理延迟（平均值、最大值、采样数）
- `timeSeries` 按小时聚合的调用量时间序列
- `recentErrors` 展示近 24 小时内的错误操作日志

---

## 11. 问答历史类接口

> 以下接口需登录。

### 11.1 会话列表

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/chat/sessions` |

返回当前用户的会话列表，含消息数量。

### 11.2 会话消息

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/chat/sessions/{sessionId}` |

返回指定会话的全部消息记录。

### 11.3 删除会话

| 项目 | 内容 |
|------|------|
| 请求方式 | DELETE |
| 请求路径 | `/api/v1/chat/sessions/{sessionId}` |

### 11.4 批量删除会话

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/chat/sessions/batch-delete` |

请求体: `["sessionId1", "sessionId2", ...]` 返回: `{ successCount, failCount }`

### 11.5 提交回答反馈

**接口说明**

用户对问答结果进行"有用/无用"反馈，用于计算满意度评分。

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/chat/feedback` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| messageId | string | 是 | 回答消息编号 |
| feedback | string | 是 | 反馈类型：like / dislike |

**请求示例**

```json
{
  "messageId": "msg001",
  "feedback": "like"
}
```

**成功响应示例**

```json
{
  "code": 200,
  "message": "反馈已提交",
  "data": {
    "messageId": "msg001",
    "feedback": "like"
  }
}
```

---

## 12. 文件管理类接口

> 以下接口需登录。

### 12.1 上传文件

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/files/upload` |
| Content-Type | multipart/form-data |

**请求参数:** file(是, 文件), 支持 jpg/jpeg/png/gif/webp/bmp/pdf，最大 10MB。

**成功响应示例**

```json
{
  "code": 200,
  "message": "上传成功",
  "data": {
    "fileId": "abc123.png",
    "fileName": "photo.jpg",
    "fileSize": 204800,
    "fileUrl": "/api/v1/files/abc123.png",
    "uploadTime": "2026-05-03T12:00:00"
  }
}
```

### 12.2 下载文件

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/files/{fileId}` |

返回文件二进制流，Content-Type 根据扩展名自动设置。

### 12.3 删除文件

| 项目 | 内容 |
|------|------|
| 请求方式 | DELETE |
| 请求路径 | `/api/v1/files/{fileId}` |

---

## 13. 拍照识件类接口

> 以下接口需登录。

### 13.1 上传图片识别元器件

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/recognize` |
| Content-Type | multipart/form-data |

**请求参数:** imageFile (是, 图片文件), 支持 jpeg/png/gif/webp/bmp，最大 10MB。

**成功响应示例**

```json
{
  "code": 200,
  "message": "识别完成",
  "data": {
    "sessionId": "abc123def456",
    "componentId": "def456",
    "model": "STM32F103C8T6",
    "type": "MCU",
    "packageType": "LQFP48",
    "manufacturer": "STMicroelectronics",
    "confidence": 0.95,
    "ocrText": "STM32F103C8T6 ARM Cortex-M3"
  }
}
```

### 13.2 提交识别反馈

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/recognize/feedback` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| sessionId | string | 是 | 识别会话编号 |
| isCorrect | bool | 是 | 识别是否正确 |
| correction | string | 否 | 正确型号（当 isCorrect=false 时） |

**成功响应示例**

```json
{
  "code": 200,
  "message": "反馈已提交",
  "data": {
    "feedbackId": "log001",
    "status": "recorded"
  }
}
```

---

## 14. AI 综合问答类接口

> 以下接口需登录。综合问答通过智能体调度管线（AgentOrchestrator → IntentClassifier → TaskDispatcher）自动识别意图并路由到对应服务。

### 14.1 发起问答

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/chat/ask` |

**请求参数**

| 参数名 | 类型 | 必填 | 说明 |
|--------|------|------|------|
| text | string | 否 | 问题文本 |
| imageUrl | string | 否 | 图片地址（已上传的文件ID） |

text 和 imageUrl 不能同时为空。

**成功响应示例**

```json
{
  "code": 200,
  "message": "问答完成",
  "data": {
    "sessionId": "abc123def456",
    "answer": "找到 1 个相关元器件：\n- STM32F103C8T6 (MCU | STMicroelectronics | LQFP48)",
    "intent": "参数查询",
    "confidence": 0.85,
    "sources": [
      {
        "sourceType": "component",
        "sourceId": "def456",
        "sourceTitle": "STM32F103C8T6",
        "contentSnippet": "MCU STMicroelectronics"
      }
    ],
    "recommendedQuestions": [
      "STM32F103C8T6的详细参数？"
    ]
  }
}
```

### 14.2 继续对话

| 项目 | 内容 |
|------|------|
| 请求方式 | POST |
| 请求路径 | `/api/v1/chat/sessions/{sessionId}/continue` |

请求体同 14.1。系统将自动加载历史上下文拼接后重新进入调度管线。

---

## 15. 流程指导类接口

> 以下接口需登录。提供面向普通用户的工序教程查询功能。

### 15.1 按工序名称查询

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/tutorials/guide` |

**请求参数:** processName (是, string) — 工序名称。

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "tutorialId": "abc123",
    "processName": "SMT贴片",
    "totalSteps": 5,
    "estimatedTime": "30分钟",
    "steps": [
      {
        "stepId": "s1",
        "stepNo": 1,
        "stepTitle": "准备物料",
        "stepContent": "检查元器件和PCB板",
        "imageUrl": null,
        "note": "注意静电防护",
        "faq": "Q: 如何检查？A: 目视检查"
      }
    ]
  }
}
```

### 15.2 获取教程步骤详情

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/tutorials/guide/{tutorialId}` |

返回格式同 15.1。

---

## 16. 规范文档类接口

> 以下接口需登录。提供面向普通用户的规范文档详情查询功能。

### 16.1 获取规范文档详情

| 项目 | 内容 |
|------|------|
| 请求方式 | GET |
| 请求路径 | `/api/v1/standards/{standardId}` |

**路径参数:** standardId (是, string) — 规范文档编号。

**成功响应示例**

```json
{
  "code": 200,
  "message": "查询成功",
  "data": {
    "standardId": "cdf238bdcaaf40ac903dca18a5910649",
    "standardCode": "IPC-A-600",
    "standardName": "印制电路板的可接受性标准",
    "section": "焊盘质量",
    "summary": "IPC-A-600规定PCB焊盘验收标准...",
    "tags": "PCB,焊盘,验收,质量,IPC",
    "relatedProcess": "PCB制造,来料检验"
  }
}
```

**错误响应**

| code | message | 说明 |
|------|---------|------|
| 404 | 规范文档不存在 | standardId 无效 |
| 401 | — | 未登录 |

---

## 17. MVP 实现说明

### 17.1 实现范围

本次 MVP 阶段已实现以上 14 类接口的全部端点（共 47 个）。

**暂不实现：** 角色选择。

### 17.2 架构分层

```
api/ (Controller)  →  services/ (Service)  →  repositories/ (Repository)  →  entities/ (Entity)
       ↕                        ↕
   schemas/ (DTO)          core/ (Config, Security, Response)
```

**类名与设计文档对照：**

| 设计文档类 | 文件 | 职责 |
|-----------|------|------|
| UserController (4.1) | `api/user_controller.py` | 认证请求接收 |
| AdminController (4.4) | `api/admin_controller.py` | 管理员请求接收 |
| QaController (4.3) | `api/qa_controller.py` | 问答及历史请求接收 |
| — | `api/file_controller.py` | 文件上传请求接收 |
| FileService (4.16) | `services/file_service.py` | 文件管理业务逻辑 |
| UserService (4.8) | `services/user_service.py` | 认证业务逻辑 |
| AdminService (4.14) | `services/admin_service.py` | 管理员业务逻辑 |
| QueryService (4.10) | `services/query_service.py` | 参数查询业务逻辑 |
| HistoryService (4.13) | `services/history_service.py` | 历史记录业务逻辑 |
| MonitorService (4.15) | `services/monitor_service.py` | 服务监控业务逻辑 |
| UserRepository (4.17) | `repositories/user_repository.py` | 用户数据访问 |
| ComponentRepository (4.18) | `repositories/component_repository.py` | 元器件数据访问 |
| StandardRepository (4.19) | `repositories/standard_repository.py` | 规范数据访问 |
| TutorialRepository (4.20) | `repositories/tutorial_repository.py` | 教程数据访问 |
| HistoryRepository (4.21) | `repositories/history_repository.py` | 日志与历史数据访问 |
| ModelClient (4.31) | `external/model_client.py` | 多模态模型适配器 |
| OcrClient (4.32) | `external/ocr_client.py` | OCR 服务适配器 |
| VectorStoreClient (4.33) | `external/vector_store_client.py` | 向量数据库适配器 |
| FileStorageClient (4.34) | `external/file_storage_client.py` | 文件存储适配器 |
| RecognitionController (4.2) | `api/recognition_controller.py` | 拍照识件请求接收 |
| AgentOrchestrator (4.5) | `agent/orchestrator.py` | 智能体调度入口 |
| IntentClassifier (4.6) | `agent/intent_classifier.py` | 意图分类器 |
| TaskDispatcher (4.7) | `agent/task_dispatcher.py` | 任务分发器 |
| RecognitionService (4.9) | `services/recognition_service.py` | 拍照识件业务逻辑 |
| QaService (4.11) | `services/qa_service.py` | 规范问答业务逻辑 |
| TutorialService (4.12) | `services/tutorial_service.py` | 流程指导业务逻辑 |

### 17.3 登录逻辑与角色判断

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

### 17.4 权限矩阵

| 接口 | 未登录 | 普通用户 | 管理员 |
|------|:------:|:--------:|:------:|
| POST `/api/v1/auth/login` | ✓ | ✓ | ✓ |
| POST `/api/v1/auth/register` | ✓ | ✓ | ✓ |
| POST `/api/v1/auth/logout` | 401 | ✓ | ✓ |
| POST `/api/v1/auth/forgot-password` | ✓ | ✓ | ✓ |
| POST `/api/v1/auth/reset-password` | ✓ | ✓ | ✓ |
| GET `/api/v1/user/profile` | 401 | ✓ | ✓ |
| PUT `/api/v1/user/profile` | 401 | ✓ | ✓ |
| POST `/api/v1/user/change-password` | 401 | ✓ | ✓ |
| GET `/api/v1/user/stats` | 401 | ✓ | ✓ |
| GET `/api/v1/user/activities` | 401 | ✓ | ✓ |
| GET `/api/v1/admin/users` | 401 | 403 | ✓ |
| PATCH `/api/v1/admin/users/{userId}/status` | 401 | 403 | ✓ |
| POST `/api/v1/admin/users/{userId}/reset-password` | 401 | 403 | ✓ |
| POST `/api/v1/admin/users/batch-status` | 401 | 403 | ✓ |
| POST `/api/v1/admin/users/batch-delete` | 401 | 403 | ✓ |
| GET `/api/v1/admin/users/{userId}/logs` | 401 | 403 | ✓ |
| GET `/api/v1/admin/components` | 401 | 403 | ✓ |
| POST `/api/v1/admin/components` | 401 | 403 | ✓ |
| PUT `/api/v1/admin/components/{componentId}` | 401 | 403 | ✓ |
| DELETE `/api/v1/admin/components/{componentId}` | 401 | 403 | ✓ |
| GET `/api/v1/components/search` | 401 | ✓ | ✓ |
| GET `/api/v1/components/{componentId}` | 401 | ✓ | ✓ |
| GET `/api/v1/admin/standards` | 401 | 403 | ✓ |
| POST `/api/v1/admin/standards` | 401 | 403 | ✓ |
| PUT `/api/v1/admin/standards/{standardId}` | 401 | 403 | ✓ |
| DELETE `/api/v1/admin/standards/{standardId}` | 401 | 403 | ✓ |
| GET `/api/v1/admin/tutorials` | 401 | 403 | ✓ |
| GET `/api/v1/admin/tutorials/{tutorialId}` | 401 | 403 | ✓ |
| POST `/api/v1/admin/tutorials` | 401 | 403 | ✓ |
| PUT `/api/v1/admin/tutorials/{tutorialId}` | 401 | 403 | ✓ |
| DELETE `/api/v1/admin/tutorials/{tutorialId}` | 401 | 403 | ✓ |
| GET `/api/v1/admin/monitor` | 401 | 403 | ✓ |
| GET `/api/v1/chat/sessions` | 401 | ✓ | ✓ |
| GET `/api/v1/chat/sessions/{sessionId}` | 401 | ✓ | ✓ |
| DELETE `/api/v1/chat/sessions/{sessionId}` | 401 | ✓ | ✓ |
| POST `/api/v1/chat/sessions/batch-delete` | 401 | ✓ | ✓ |
| POST `/api/v1/chat/feedback` | 401 | ✓ | ✓ |
| POST `/api/v1/files/upload` | 401 | ✓ | ✓ |
| GET `/api/v1/files/{fileId}` | 401 | ✓ | ✓ |
| DELETE `/api/v1/files/{fileId}` | 401 | ✓ | ✓ |
| POST `/api/v1/recognize` | 401 | ✓ | ✓ |
| POST `/api/v1/recognize/feedback` | 401 | ✓ | ✓ |
| POST `/api/v1/chat/ask` | 401 | ✓ | ✓ |
| POST `/api/v1/chat/sessions/{sessionId}/continue` | 401 | ✓ | ✓ |
| GET `/api/v1/tutorials/guide` | 401 | ✓ | ✓ |
| GET `/api/v1/tutorials/guide/{tutorialId}` | 401 | ✓ | ✓ |
| GET `/api/v1/standards/{standardId}` | 401 | ✓ | ✓ |

### 17.5 前端对接

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

### 17.6 运行步骤

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

### 17.7 接口测试示例

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
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{}'
```

**9) 查看用户操作日志**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/users/{userId}/logs" \
  -H "Authorization: Bearer $TOKEN"
```

**10) 新增元器件**

```bash
curl -X POST http://localhost:8000/api/v1/admin/components \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"model":"STM32F103C8T6","type":"MCU","packageType":"LQFP48","manufacturer":"STMicro","params":[{"paramName":"Flash","paramValue":"64","paramUnit":"KB"}]}'
```

**11) 查询元器件列表**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/components?model=STM32&pageNum=1&pageSize=10" \
  -H "Authorization: Bearer $TOKEN"
```

**12) 编辑元器件**

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/components/{componentId}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"manufacturer":"STMicroelectronics","type":"MCU"}'
```

**13) 删除元器件**

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/components/{componentId}" \
  -H "Authorization: Bearer $TOKEN"
```

**14) 用户注册**

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"account":"newuser@example.com","username":"newuser","password":"123456","confirmPassword":"123456"}'
```

**15) 查看个人信息**

```bash
curl -X GET "http://localhost:8000/api/v1/user/profile" \
  -H "Authorization: Bearer $TOKEN"
```

**16) 编辑个人信息**

```bash
curl -X PUT "http://localhost:8000/api/v1/user/profile" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"phone":"13800138000"}'
```

**17) 自行修改密码**

```bash
curl -X POST "http://localhost:8000/api/v1/user/change-password" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"oldPassword":"123456","newPassword":"654321","confirmPassword":"654321"}'
```

**18) 新增规范**

```bash
curl -X POST http://localhost:8000/api/v1/admin/standards \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"standardCode":"IPC-A-610","standardName":"电子组件的可接受性","section":"第3章"}'
```

**19) 查询规范列表**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/standards?pageNum=1&pageSize=10" \
  -H "Authorization: Bearer $TOKEN"
```

**20) 编辑规范**

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/standards/{standardId}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"standardName":"更新后的规范名称"}'
```

**21) 删除规范**

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/standards/{standardId}" \
  -H "Authorization: Bearer $TOKEN"
```

**22) 新增教程**

```bash
curl -X POST http://localhost:8000/api/v1/admin/tutorials \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"processName":"SMT贴片","estimatedTime":"30分钟","steps":[{"stepNo":1,"stepTitle":"准备物料","stepContent":"检查元器件和PCB板"}]}'
```

**23) 查询教程列表**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/tutorials?pageNum=1&pageSize=10" \
  -H "Authorization: Bearer $TOKEN"
```

**24) 教程详情**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/tutorials/{tutorialId}" \
  -H "Authorization: Bearer $TOKEN"
```

**25) 编辑教程**

```bash
curl -X PUT "http://localhost:8000/api/v1/admin/tutorials/{tutorialId}" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"processName":"SMT贴片(修订)"}'
```

**26) 删除教程**

```bash
curl -X DELETE "http://localhost:8000/api/v1/admin/tutorials/{tutorialId}" \
  -H "Authorization: Bearer $TOKEN"
```

**27) 查看问答历史**

```bash
curl -X GET "http://localhost:8000/api/v1/chat/sessions" \
  -H "Authorization: Bearer $TOKEN"
```

**28) 上传文件**

```bash
curl -X POST http://localhost:8000/api/v1/files/upload \
  -H "Authorization: Bearer $TOKEN" \
  -F "file=@/path/to/image.jpg"
```

**29) 下载文件**

```bash
curl -X GET "http://localhost:8000/api/v1/files/{fileId}" \
  -H "Authorization: Bearer $TOKEN" \
  --output downloaded.jpg
```

**30) 删除文件**

```bash
curl -X DELETE "http://localhost:8000/api/v1/files/{fileId}" \
  -H "Authorization: Bearer $TOKEN"
```

**31) 拍照识件**

```bash
curl -X POST http://localhost:8000/api/v1/recognize \
  -H "Authorization: Bearer $TOKEN" \
  -F "imageFile=@/path/to/component.jpg"
```

**32) 提交识别反馈**

```bash
curl -X POST http://localhost:8000/api/v1/recognize/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"sessionId":"abc123","isCorrect":false,"correction":"STM32F103CBT6"}'
```

**33) AI 综合问答**

```bash
curl -X POST http://localhost:8000/api/v1/chat/ask \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"STM32F103的Flash大小是多少？"}'
```

**34) 继续对话**

```bash
curl -X POST "http://localhost:8000/api/v1/chat/sessions/{sessionId}/continue" \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"text":"那它的RAM呢？"}'
```

**35) 按工序名称查询教程**

```bash
curl -X GET "http://localhost:8000/api/v1/tutorials/guide?processName=SMT贴片" \
  -H "Authorization: Bearer $TOKEN"
```

**36) 获取教程步骤详情**

```bash
curl -X GET "http://localhost:8000/api/v1/tutorials/guide/{tutorialId}" \
  -H "Authorization: Bearer $TOKEN"
```

**37) 获取规范文档详情**

```bash
curl -X GET "http://localhost:8000/api/v1/standards/{standardId}" \
  -H "Authorization: Bearer $TOKEN"
```

**38) 忘记密码**

```bash
curl -X POST http://localhost:8000/api/v1/auth/forgot-password \
  -H "Content-Type: application/json" \
  -d '{"account":"user@example.com"}'
```

**39) 通过令牌重置密码**

```bash
curl -X POST http://localhost:8000/api/v1/auth/reset-password \
  -H "Content-Type: application/json" \
  -d '{"token":"abc123xyz","newPassword":"654321","confirmPassword":"654321"}'
```

**40) 批量启用/禁用用户**

```bash
curl -X POST http://localhost:8000/api/v1/admin/users/batch-status \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"userIds":["abc123","def456"],"status":"disabled"}'
```

**41) 批量删除用户**

```bash
curl -X POST http://localhost:8000/api/v1/admin/users/batch-delete \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"userIds":["abc123","def456"]}'
```

**42) 提交回答反馈**

```bash
curl -X POST http://localhost:8000/api/v1/chat/feedback \
  -H "Authorization: Bearer $TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"messageId":"msg001","feedback":"like"}'
```

**43) 查看服务监控**

```bash
curl -X GET "http://localhost:8000/api/v1/admin/monitor" \
  -H "Authorization: Bearer $TOKEN"
```

### 17.8 数据库表

| 表名 | 字段 |
|------|------|
| `user` | user_id, username, password, email, phone, role, status, department, avatar, reset_token, reset_token_expiry, create_time, last_login_time |
| `component` | component_id, model, type, package_type, manufacturer, datasheet_url, image_url, create_time, update_time |
| `component_param` | param_id, component_id(FK), param_name, param_value, param_unit |
| `process_standard` | standard_id, standard_code, standard_name, section, summary, tags, related_process |
| `tutorial` | tutorial_id, process_name, total_steps, estimated_time |
| `tutorial_step` | step_id, tutorial_id(FK), step_no, step_title, step_content, image_url, note, faq |
| `chat_session` | session_id, user_id(FK), title, create_time, update_time |
| `chat_message` | message_id, session_id(FK), sender_type, content, image_url, source_info, feedback, create_time |
| `operation_log` | log_id, user_id(FK), operation_type, operation_target, operation_time, operation_result, response_time_ms |
