"""
种子数据脚本：预置管理员/普通用户 + 测试元器件数据。

运行方式（先 pip install -r backend/requirements.txt）:
    cd database/mysql
    python seed.py

或从项目根目录:
    python database/mysql/seed.py
"""

import sys
import os

# 将 backend 加入 Python 路径，以便复用 app 的密码工具
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "backend"))

import uuid
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from app.core.config import settings
from app.db.mysql import Base
from app.entities.user import User
from app.entities.component_info import Component, ComponentParam
from app.utils.password import hash_password

# ---------- 用户种子数据 ----------

SEED_USERS = [
    {
        "user_id": uuid.uuid4().hex,
        "username": "admin",
        "password": "admin123",
        "email": "admin@example.com",
        "phone": "13800000001",
        "role": "admin",
        "status": "enabled",
    },
    {
        "user_id": uuid.uuid4().hex,
        "username": "user",
        "password": "user123",
        "email": "user@example.com",
        "phone": "13800000002",
        "role": "user",
        "status": "enabled",
    },
]

# ---------- 元器件种子数据 ----------

SEED_COMPONENTS = [
    {
        "component_id": uuid.uuid4().hex,
        "model": "STM32F103C8T6",
        "type": "MCU",
        "package_type": "LQFP48",
        "manufacturer": "STMicroelectronics",
        "datasheet_url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
        "image_url": None,
        "params": [
            {"param_name": "内核", "param_value": "ARM Cortex-M3", "param_unit": None},
            {"param_name": "主频", "param_value": "72", "param_unit": "MHz"},
            {"param_name": "Flash", "param_value": "64", "param_unit": "KB"},
            {"param_name": "RAM", "param_value": "20", "param_unit": "KB"},
            {"param_name": "工作电压", "param_value": "2.0-3.6", "param_unit": "V"},
            {"param_name": "引脚数", "param_value": "48", "param_unit": None},
        ],
    },
    {
        "component_id": uuid.uuid4().hex,
        "model": "ESP32-WROOM-32",
        "type": "WiFi模块",
        "package_type": "SMD",
        "manufacturer": "Espressif",
        "datasheet_url": "https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32_datasheet_cn.pdf",
        "image_url": None,
        "params": [
            {"param_name": "内核", "param_value": "Xtensa LX6", "param_unit": None},
            {"param_name": "主频", "param_value": "240", "param_unit": "MHz"},
            {"param_name": "Flash", "param_value": "4", "param_unit": "MB"},
            {"param_name": "RAM", "param_value": "520", "param_unit": "KB"},
            {"param_name": "工作电压", "param_value": "3.0-3.6", "param_unit": "V"},
        ],
    },
    {
        "component_id": uuid.uuid4().hex,
        "model": "CH340G",
        "type": "USB转串口芯片",
        "package_type": "SOP16",
        "manufacturer": "WCH",
        "datasheet_url": "https://www.wch.cn/downloads/CH340DS1_PDF.html",
        "image_url": None,
        "params": [
            {"param_name": "工作电压", "param_value": "3.3-5", "param_unit": "V"},
            {"param_name": "波特率", "param_value": "50-2000000", "param_unit": "bps"},
        ],
    },
    {
        "component_id": uuid.uuid4().hex,
        "model": "10kΩ-0805",
        "type": "电阻",
        "package_type": "0805",
        "manufacturer": "Yageo",
        "datasheet_url": None,
        "image_url": None,
        "params": [
            {"param_name": "阻值", "param_value": "10", "param_unit": "kΩ"},
            {"param_name": "精度", "param_value": "±1", "param_unit": "%"},
            {"param_name": "功率", "param_value": "0.125", "param_unit": "W"},
        ],
    },
    {
        "component_id": uuid.uuid4().hex,
        "model": "100nF-0603",
        "type": "电容",
        "package_type": "0603",
        "manufacturer": "Murata",
        "datasheet_url": None,
        "image_url": None,
        "params": [
            {"param_name": "容值", "param_value": "100", "param_unit": "nF"},
            {"param_name": "耐压", "param_value": "50", "param_unit": "V"},
            {"param_name": "类型", "param_value": "MLCC", "param_unit": None},
        ],
    },
]


def seed():
    engine = create_engine(settings.DATABASE_URL)
    Base.metadata.create_all(bind=engine)

    with Session(engine) as db:
        # 插入用户
        for u in SEED_USERS:
            exists = db.query(User).filter(User.username == u["username"]).first()
            if exists:
                print(f"[跳过] 用户已存在: {u['username']}")
                continue
            user = User(
                user_id=u["user_id"],
                username=u["username"],
                password=hash_password(u["password"]),
                email=u["email"],
                phone=u["phone"],
                role=u["role"],
                status=u["status"],
            )
            db.add(user)
            print(f"[插入] 用户: {u['username']} (role={u['role']})")

        db.flush()

        # 插入元器件
        for c in SEED_COMPONENTS:
            exists = db.query(Component).filter(Component.model == c["model"]).first()
            if exists:
                print(f"[跳过] 元器件已存在: {c['model']}")
                continue
            comp = Component(
                component_id=c["component_id"],
                model=c["model"],
                type=c["type"],
                package_type=c["package_type"],
                manufacturer=c["manufacturer"],
                datasheet_url=c["datasheet_url"],
                image_url=c["image_url"],
            )
            db.add(comp)
            db.flush()

            for p in c["params"]:
                param = ComponentParam(
                    param_id=uuid.uuid4().hex,
                    component_id=comp.component_id,
                    param_name=p["param_name"],
                    param_value=p["param_value"],
                    param_unit=p["param_unit"],
                )
                db.add(param)
            print(f"[插入] 元器件: {c['model']} ({len(c['params'])} 个参数)")

        db.commit()
        print("\n种子数据写入完成。")


if __name__ == "__main__":
    seed()