# 后端接口测试文档

## 测试环境

| 项目 | 说明 |
|------|------|
| 框架 | FastAPI + SQLAlchemy + MySQL |
| 地址 | http://localhost:8000 |
| Swagger | http://localhost:8000/docs |
| 认证方式 | JWT Token，Header: `Authorization: Bearer <token>` |
| 统一响应 | `{"code": 200, "message": "...", "data": {...}}` |

## 测试账号

| 角色 | 账号 | 密码 |
|------|------|------|
| 管理员 | admin@example.com | admin123 |
| 普通用户 | user@example.com | user123 |

## 权限矩阵

| 接口 | 未登录 | 普通用户 | 管理员 |
|------|:------:|:--------:|:------:|
| POST `/api/v1/auth/login` | 200 | 200 | 200 |
| GET `/api/v1/components/search` | 401 | 200 | 200 |
| GET `/api/v1/components/{id}` | 401 | 200 | 200 |
| GET `/api/v1/admin/users` | 401 | 403 | 200 |
| PATCH `/api/v1/admin/users/{id}/status` | 401 | 403 | 200 |
| POST `/api/v1/admin/users/{id}/reset-password` | 401 | 403 | 200 |
| GET `/api/v1/admin/users/{id}/logs` | 401 | 403 | 200 |

---

## 0. 启动服务

```powershell
cd D:\Projects\eim-agent-qa\backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

保持当前窗口运行，另开一个 PowerShell 窗口执行以下测试。

---

## 1. 管理员登录

```powershell
$r = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login -Method Post -ContentType "application/json" -Body '{"account":"admin@example.com","password":"admin123"}'
$ADMIN_TOKEN = $r.data.token
```

**预期：** `code=200`，`role=admin`，`status=enabled`

---

## 2. 元器件搜索

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/components/search?keyword=STM32" -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`records` 有数据，包含 `componentId`、`model`、`type`、`packageType`、`manufacturer`

---

## 3. 元器件详情

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/components/1f204adbc4d04326b521ef68d02ea510" -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，包含 `coreParams`（内核、主频、Flash 等）、`datasheetUrl`

---

## 4. 用户列表

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users?pageNum=1&pageSize=10" -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`records` 包含 admin 和 user，含 `userId`、`username`、`email`、`status`、`registerTime`

---

## 5. 禁用用户

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users/5ffeeeede5b340c4b9905f136fa8beec/status" -Method Patch -ContentType "application/json" -Body '{"status":"disabled"}' -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`status=disabled`。禁用后该用户无法登录。

---

## 6. 重新启用用户

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users/5ffeeeede5b340c4b9905f136fa8beec/status" -Method Patch -ContentType "application/json" -Body '{"status":"enabled"}' -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`status=enabled`

---

## 7. 重置密码（指定密码）

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users/5ffeeeede5b340c4b9905f136fa8beec/reset-password" -Method Post -ContentType "application/json" -Body '{"password":"user123"}' -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`tempPassword=user123`

不指定密码则自动生成：

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users/5ffeeeede5b340c4b9905f136fa8beec/reset-password" -Method Post -ContentType "application/json" -Body '{}' -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

---

## 8. 查看用户操作日志

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users/cba0a00b98534509a8344f9098a44309/logs" -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=200`，`records` 有登录、重置密码、修改状态等操作记录

---

## 9. 权限测试

```powershell
# 普通用户登录
$r2 = Invoke-RestMethod -Uri http://localhost:8000/api/v1/auth/login -Method Post -ContentType "application/json" -Body '{"account":"user@example.com","password":"user123"}'
$USER_TOKEN = $r2.data.token

# 9a. 普通用户访问管理接口 → 预期 403
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/admin/users" -Headers @{Authorization="Bearer $USER_TOKEN"}

# 9b. 普通用户访问元器件搜索 → 预期 200
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/components/search?keyword=ESP32" -Headers @{Authorization="Bearer $USER_TOKEN"}
```

---

## 10. 无搜索结果

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/components/search?keyword=NOTEXIST" -Headers @{Authorization="Bearer $ADMIN_TOKEN"}
```

**预期：** `code=404`，`message="未查询到匹配的元器件"`

---

## 11. 未登录访问

```powershell
Invoke-RestMethod -Uri "http://localhost:8000/api/v1/components/search?keyword=STM32"
```

**预期：** `detail="Not authenticated"`（HTTP 401）
