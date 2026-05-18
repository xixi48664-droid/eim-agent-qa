"""
电子元器件知识库导入脚本。

用法（在 backend/ 目录下执行）:
    python scripts/import_components.py                          # 导入全部内置数据
    python scripts/import_components.py --dry-run                # 仅预览，不写入数据库
    python scripts/import_components.py --yaml path/to/data.yaml # 从 YAML 导入
    python scripts/import_components.py --search STM32F103C8T6   # 从 Digi-Key 搜索并导入
    python scripts/import_components.py --batch models.txt       # 批量搜索导入

Digi-Key API 配置（二选一）:
    a) 环境变量: 设置 DIGIKEY_CLIENT_ID 和 DIGIKEY_CLIENT_SECRET
    b) 命令行:   --digikey-client-id xxx --digikey-client-secret xxx

注册 Digi-Key API Key: https://developer.digikey.com/  (免费注册)
"""

import argparse
import sys
import os
import time

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import httpx
from app.db.mysql import SessionLocal
from app.entities.component_info import Component, ComponentParam

# ═══════════════════════════════════════════════════════════════
# Digi-Key API 客户端
# ═══════════════════════════════════════════════════════════════

DIGIKEY_TOKEN_URL = "https://api.digikey.com/v1/oauth2/token"
DIGIKEY_SEARCH_URL = "https://api.digikey.com/products/v4/search/keyword"
DIGIKEY_PRODUCT_URL = "https://api.digikey.com/products/v4"

_UA = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"

# token 缓存（1小时有效）
_token_cache: dict[str, tuple[str, float]] = {}

# 英文参数名 → 中文参数名 翻译表
# Digi-Key 返回的参数名是英文的，通过此表翻译为中文，覆盖绝大多数元器件参数
_PARAM_TRANSLATION = {
    # ── 处理器/MCU ──
    "Core Processor": "内核",
    "Core Size": "内核位宽",
    "Speed": "主频",
    "Connectivity": "通信接口",
    "Peripherals": "外设",
    "Number of I/O": "GPIO数量",
    "Program Memory Size": "Flash容量",
    "Program Memory Type": "存储器类型",
    "EEPROM Size": "EEPROM容量",
    "RAM Size": "SRAM容量",
    "Data Converters": "数据转换器",
    "Oscillator Type": "振荡器类型",
    "Voltage - Supply (Vcc/Vdd)": "工作电压",
    "Voltage - Supply": "工作电压",
    "Supply Voltage": "工作电压",
    "Operating Temperature": "工作温度",
    "Mounting Type": "安装方式",
    "Package / Case": "封装",
    "Supplier Device Package": "供应商封装",
    "Grade": "等级",
    "Qualification": "认证",
    "Watchdog Timer": "看门狗定时器",
    "Internal Oscillator": "内部振荡器",
    "DAC Resolution": "DAC分辨率",
    "ADC Resolution": "ADC分辨率",
    "PWM Channels": "PWM通道数",
    "Timers/Counters": "定时器/计数器",

    # ── 电源管理 ──
    "Function": "功能",
    "Output Configuration": "输出配置",
    "Output Type": "输出类型",
    "Topology": "拓扑结构",
    "Output Voltage": "输出电压",
    "Voltage - Output": "输出电压",
    "Voltage - Output 1": "输出电压1",
    "Voltage - Output 2": "输出电压2",
    "Voltage - Input": "输入电压",
    "Voltage - Input (Min)": "最小输入电压",
    "Voltage - Input (Max)": "最大输入电压",
    "Voltage - Supply (Min)": "最小工作电压",
    "Voltage - Supply (Max)": "最大工作电压",
    "Current - Output": "输出电流",
    "Current - Output (Max)": "最大输出电流",
    "Current - Supply": "工作电流",
    "Current - Supply (Max)": "最大工作电流",
    "Current - Quiescent (Iq)": "静态电流",
    "Current - Quiescent (Max)": "最大静态电流",
    "Current - Output / Channel": "每通道输出电流",
    "Frequency - Switching": "开关频率",
    "Frequency - Max": "最大频率",
    "Synchronous Rectifier": "同步整流",
    "Voltage - Forward (Vf) (Typ)": "正向压降(VF)",
    "Voltage - Forward (Vf) (Max)": "最大正向压降(VF)",
    "Current - Reverse Leakage": "反向漏电流",
    "Voltage Dropout (Max)": "最大压差",
    "PSRR": "电源抑制比(PSRR)",
    "Control Features": "控制特性",
    "Protection Features": "保护特性",

    # ── 通信接口 ──
    "Protocol": "协议",
    "Data Rate": "数据速率",
    "Number of Drivers/Receivers": "驱动/接收器数量",
    "Duplex": "双工模式",
    "Receiver Hysteresis": "接收器迟滞",
    "ESD Protection": "ESD保护",
    "Standard": "标准",
    "Interface": "接口",
    "Baud Rate": "波特率",

    # ── 传感器 ──
    "Sensor Type": "传感器类型",
    "Sensing Range": "感测范围",
    "Accuracy": "精度",
    "Output": "输出",
    "Resolution": "分辨率",
    "Sampling Rate": "采样率",
    "Sensitivity": "灵敏度",
    "Response Time": "响应时间",
    "Sensing Distance": "感测距离",
    "Humidity Range": "湿度范围",
    "Temperature Range": "温度范围",

    # ── 存储器 ──
    "Memory Type": "存储器类型",
    "Memory Size": "存储容量",
    "Memory Format": "存储格式",
    "Technology": "技术",
    "Clock Frequency": "时钟频率",
    "Write Cycle Time - Word, Page": "写入周期",
    "Access Time": "访问时间",
    "Volatile": "易失性",
    "Memory Organization": "存储组织",
    "Memory Interface": "存储器接口",

    # ── 分立元件 ──
    "Diode Type": "二极管类型",
    "Current - Average Rectified (Io)": "平均整流电流(IO)",
    "Current - Reverse Leakage @ Vr": "反向漏电流@VR",
    "Reverse Recovery Time (trr)": "反向恢复时间(trr)",
    "Capacitance @ Vr, F": "结电容",
    "FET Type": "FET类型",
    "Drain to Source Voltage (Vdss)": "漏源电压(VDSS)",
    "Current - Continuous Drain (Id) @ 25°C": "连续漏极电流(ID)",
    "Rds On (Max) @ Id, Vgs": "导通电阻(RDS(on))",
    "Vgs(th) (Max) @ Id": "阈值电压(VGS(th))",
    "Gate Charge (Qg) (Max) @ Vgs": "栅极电荷(QG)",
    "Input Capacitance (Ciss) (Max) @ Vds": "输入电容(CISS)",
    "Power - Max": "最大功耗",
    "Transistor Type": "晶体管类型",
    "Current - Collector (Ic) (Max)": "最大集电极电流(IC)",
    "Vce Saturation (Max) @ Ib, Ic": "饱和压降(VCE(sat))",
    "DC Current Gain (hFE) (Min) @ Ic, Vce": "直流增益(hFE)",

    # ── 通用 ──
    "Number of Channels": "通道数",
    "Number of Outputs": "输出数",
    "Number of Inputs": "输入数",
    "Number of Bits": "位数",
    "Number of Elements": "元件数",
    "Gain Bandwidth Product": "增益带宽积(GBW)",
    "Slew Rate": "压摆率(SR)",
    "-3db Bandwidth": "-3dB带宽",
    "Current - Input Bias": "输入偏置电流",
    "Voltage - Input Offset": "输入失调电压",
    "Current - Output (Typ)": "典型输出电流",
    "Amplifier Type": "放大器类型",
    "Output Current per Channel": "每通道输出电流",
    "Temperature Coefficient": "温度系数",
    "Tolerance": "容差",
    "Power (Watts)": "功率",
    "Power Rating": "额定功率",
    "Resistance": "电阻值",
    "Capacitance": "电容值",
    "Inductance": "电感值",
    "Type": "类型",
    "Features": "特性",
    "Applications": "应用",
    "Mounting": "安装方式",
    "Orientation": "方向",
    "Termination Style": "端接方式",
    "Contact Finish": "触点镀层",
    "Number of Positions": "针脚数",
    "Number of Rows": "排数",
    "Pitch": "间距",
    "Fastening Type": "固定方式",
    "Contact Material": "触点材料",
    "Housing Material": "外壳材料",
    "Insulation Material": "绝缘材料",
    "Material - Core": "磁芯材料",
    "Frequency": "频率",
    "Frequency Stability": "频率稳定性",
    "Frequency Tolerance": "频率公差",
    "Load Capacitance": "负载电容",
    "ESR (Equivalent Series Resistance)": "等效串联电阻(ESR)",
    "Ratings": "额定值",
    "Lead Style": "引线样式",
    "Size / Dimension": "尺寸",
    "Height - Seated (Max)": "最大高度",
    "Shelf Life": "保质期",
    "Wavelength": "波长",
    "Viewing Angle": "视角",
    "Color": "颜色",
    "Luminous Intensity": "发光强度",
    "Forward Current": "正向电流",
    "Forward Voltage": "正向电压",
    "Reverse Voltage": "反向电压",
    "Test Condition": "测试条件",
    "Base Product Number": "基础型号",
    "Detailed Description": "详细描述",
    "Part Status": "零件状态",
    "Moisture Sensitivity Level (MSL)": "湿度敏感等级(MSL)",
    "RoHS Status": "RoHS状态",
    "REACH Status": "REACH状态",
    "Lead Free Status / RoHS Status": "无铅/RoHS状态",
    "Weight": "重量",
    "Lifecycle Status": "生命周期状态",
}


def _translate_param_name(en_name: str) -> str:
    """将英文参数名翻译为中文，未匹配的保持原文。"""
    name = en_name.strip()
    # 精确匹配
    if name in _PARAM_TRANSLATION:
        return _PARAM_TRANSLATION[name]
    # 尝试部分匹配（去除 @ 等修饰符后的核心名）
    base = name.split("@")[0].strip().rstrip(",")
    if base in _PARAM_TRANSLATION:
        return _PARAM_TRANSLATION[base]
    return name


# 分类名翻译
_CATEGORY_TRANSLATION = {
    "Integrated Circuits (ICs)": "集成电路(IC)",
    "Embedded": "嵌入式",
    "Microcontrollers": "微控制器(MCU)",
    "Microprocessors": "微处理器(MPU)",
    "FPGAs": "FPGA",
    "Memory": "存储器",
    "PMIC": "电源管理IC",
    "Power Management (PMIC)": "电源管理IC",
    "Voltage Regulators": "电压稳压器",
    "DC DC Switching Regulators": "DC-DC开关稳压器",
    "Linear Voltage Regulators": "线性稳压器(LDO)",
    "Battery Management": "电池管理IC",
    "Sensors": "传感器",
    "Transducers": "换能器",
    "Isolators": "隔离器",
    "Connectors": "连接器",
    "Interconnects": "互连器件",
    "RF and Wireless": "射频/无线",
    "Cable Assemblies": "线缆组件",
    "Potentiometers": "电位器",
    "Variable Resistors": "可变电阻",
    "Crystals": "晶振",
    "Oscillators": "振荡器",
    "Resonators": "谐振器",
    "Memory - Modules": "存储器模块",
    "Cards": "存储卡",
    "Power Supplies - Board Mount": "板载电源",
    "Power Supplies - External/Internal": "外接/内置电源",
    "Industrial Automation and Controls": "工业自动化",
    "Maker/DIY, Educational": "创客/教育",
    "Hardware, Fasteners, Accessories": "五金/紧固件",
    "Boxes, Enclosures, Racks": "机箱/机柜",
    "Computer Equipment": "计算机设备",
    "Embedded Computers": "嵌入式计算机",
    "Fans, Blowers, Thermal Management": "风扇/热管理",
    "Audio Products": "音频产品",
    "Cables, Wires - Management": "线缆管理",
    "Tapes, Adhesives, Materials": "胶带/粘合剂",
    "Tools": "工具",
    "RF Transceivers": "射频收发器",
    "RF Amplifiers": "射频放大器",
    "RF Modules": "射频模块",
    "Temperature Sensors": "温度传感器",
    "Humidity Sensors": "湿度传感器",
    "Pressure Sensors": "压力传感器",
    "Motion Sensors": "运动传感器",
    "Optical Sensors": "光学传感器",
    "Image Sensors": "图像传感器",
    "Discrete Semiconductor Products": "分立半导体",
    "Diodes": "二极管",
    "Rectifiers": "整流器",
    "Zener Diodes": "齐纳二极管",
    "TVS Diodes": "TVS二极管",
    "Schottky Diodes": "肖特基二极管",
    "Transistors": "晶体管",
    "MOSFETs": "MOSFET",
    "BJTs": "双极型晶体管(BJT)",
    "IGBTs": "IGBT",
    "JFETs": "JFET",
    "Thyristors": "晶闸管",
    "Interface": "接口IC",
    "Drivers, Receivers, Transceivers": "驱动/接收/收发器",
    "Controllers": "控制器",
    "USB": "USB接口",
    "Ethernet": "以太网接口",
    "CAN": "CAN接口",
    "RS-232": "RS-232接口",
    "RS-422, RS-485": "RS-422/RS-485接口",
    "Logic": "逻辑IC",
    "Gates and Inverters": "门电路/反相器",
    "Flip Flops": "触发器",
    "Latches": "锁存器",
    "Buffers, Drivers, Receivers, Transceivers": "缓冲/驱动/收发器",
    "Shift Registers": "移位寄存器",
    "Signal Switches": "信号开关",
    "Analog Switches": "模拟开关",
    "Multiplexers": "多路复用器",
    "Amplifiers": "放大器",
    "Operational Amplifiers": "运算放大器",
    "Instrumentation Amplifiers": "仪表放大器",
    "Comparators": "比较器",
    "Audio Amplifiers": "音频放大器",
    "Data Acquisition": "数据采集",
    "ADC": "模数转换器(ADC)",
    "DAC": "数模转换器(DAC)",
    "ADCs/DACs": "ADC/DAC",
    "Special Purpose ADCs/DACs": "专用ADC/DAC",
    "Clock/Timing": "时钟/定时",
    "Oscillators": "振荡器",
    "Crystals": "晶振",
    "Real Time Clocks": "实时时钟(RTC)",
    "Timers": "定时器",
    "Clock Generators": "时钟发生器",
    "RF/IF and RFID": "射频/中频",
    "RF Transceivers": "射频收发器",
    "RF Amplifiers": "射频放大器",
    "RF Mixers": "射频混频器",
    "RF Switches": "射频开关",
    "RF Antennas": "射频天线",
    "RF Modules": "射频模块",
    "NFC/RFID": "NFC/RFID",
    "Wireless Modules": "无线模块",
    "Audio": "音频",
    "Connectors": "连接器",
    "Terminal Blocks": "接线端子",
    "Rectangular Connectors": "矩形连接器",
    "Circular Connectors": "圆形连接器",
    "USB Connectors": "USB连接器",
    "D-Sub Connectors": "D-Sub连接器",
    "Relays": "继电器",
    "Switches": "开关",
    "LEDs": "LED",
    "LED Lighting": "LED照明",
    "Optoelectronics": "光电器件",
    "Display Modules": "显示模块",
    "LCD, OLED": "LCD/OLED",
    "Filters": "滤波器",
    "Ferrite Beads and Chips": "磁珠",
    "Common Mode Chokes": "共模扼流圈",
    "Inductors, Coils, Chokes": "电感/线圈/扼流圈",
    "Resistors": "电阻",
    "Chip Resistor": "贴片电阻",
    "Through Hole Resistors": "插件电阻",
    "Capacitors": "电容",
    "Ceramic Capacitors": "陶瓷电容",
    "Aluminum Electrolytic Capacitors": "铝电解电容",
    "Tantalum Capacitors": "钽电容",
    "Film Capacitors": "薄膜电容",
    "Circuit Protection": "电路保护",
    "Fuses": "保险丝",
    "PTC Resettable Fuses": "PTC自恢复保险丝",
    "ESD Suppressors": "ESD抑制器",
    "Thermal Management": "热管理",
    "Heat Sinks": "散热器",
    "Fans": "风扇",
    "Power Supplies": "电源",
    "AC DC Converters": "AC-DC转换器",
    "DC DC Converters": "DC-DC转换器",
    "Battery Products": "电池产品",
    "Batteries": "电池",
    "Battery Chargers": "电池充电器",
    "Battery Holders": "电池座",
    "Cables, Wires": "线缆/导线",
    "Test and Measurement": "测试与测量",
    "Tools and Supplies": "工具与耗材",
    "Development Boards, Kits, Programmers": "开发板/套件/编程器",
    "Evaluation Boards": "评估板",
    "Programmers, Emulators, and Debuggers": "编程/仿真/调试器",
}


def _translate_category(en_cat: str) -> str:
    """将 Digi-Key 分类名翻译为中文。"""
    cat = en_cat.strip()
    if cat in _CATEGORY_TRANSLATION:
        return _CATEGORY_TRANSLATION[cat]
    # 尝试按 / 或 , 拆分后逐段匹配
    for sep in ("/", ","):
        parts = cat.split(sep)
        if len(parts) > 1:
            translated = []
            for part in parts:
                part = part.strip()
                if part in _CATEGORY_TRANSLATION:
                    translated.append(_CATEGORY_TRANSLATION[part])
                else:
                    translated.append(part)
            return "/".join(translated)
    return cat


def _digikey_request(method: str, url: str, client_id: str, client_secret: str,
                     max_retries: int = 2, **kwargs) -> httpx.Response:
    """发送 Digi-Key API 请求，带 SSL 重试。"""
    token = _get_digikey_token(client_id, client_secret)
    req_headers = kwargs.pop("headers", {})
    req_headers.update({
        "User-Agent": _UA,
        "Authorization": f"Bearer {token}",
        "X-DIGIKEY-Client-Id": client_id,
    })

    last_error = None
    for attempt in range(max_retries + 1):
        try:
            resp = httpx.request(method, url, headers=req_headers, timeout=20.0, **kwargs)
            resp.raise_for_status()
            return resp
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError) as e:
            last_error = e
            if attempt < max_retries:
                time.sleep(1)
                continue
        except Exception as e:
            raise e
    raise last_error


def _get_digikey_token(client_id: str, client_secret: str) -> str:
    """获取 Digi-Key OAuth2 access token，带缓存和重试。"""
    cache_key = f"{client_id}:{client_secret}"
    if cache_key in _token_cache:
        token, expires_at = _token_cache[cache_key]
        if time.time() < expires_at - 60:
            return token

    for attempt in range(3):
        try:
            resp = httpx.post(
                DIGIKEY_TOKEN_URL,
                data={
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "grant_type": "client_credentials",
                },
                headers={
                    "User-Agent": _UA,
                    "Content-Type": "application/x-www-form-urlencoded",
                },
                timeout=15.0,
            )
            resp.raise_for_status()
            data = resp.json()
            token = data["access_token"]
            expires_in = data.get("expires_in", 3600)
            _token_cache[cache_key] = (token, time.time() + expires_in)
            return token
        except (httpx.ConnectError, httpx.ReadError, httpx.RemoteProtocolError):
            if attempt < 2:
                time.sleep(1)
                continue
            raise


# Digi-Key 返回的泛化顶层分类，如果分类是这些之一，优先用关键词分段分类覆盖
_GENERIC_CATEGORIES = {
    "集成电路(IC)", "Integrated Circuits (ICs)",
    "分立半导体", "Discrete Semiconductor Products",
    "传感器/换能器", "Sensors, Transducers",
    "RF and Wireless", "RF/IF and RFID",
    "Isolators",
    "Connectors, Interconnects",
    "光电器件", "Optoelectronics",
    "电路保护", "Circuit Protection",
}


def _digikey_search(client_id: str, client_secret: str, keyword: str, limit: int = 5,
                    default_type: str = "") -> list[dict]:
    """搜索 Digi-Key 元器件，返回可导入的元器件列表。default_type 用于覆盖泛化分类。"""
    try:
        resp = _digikey_request(
            "POST", DIGIKEY_SEARCH_URL, client_id, client_secret,
            json={"Keywords": keyword, "Limit": limit, "Offset": 0},
            headers={"Accept": "application/json", "Content-Type": "application/json"},
        )
        data = resp.json()
    except Exception as e:
        print(f"  [错误] Digi-Key 搜索失败: {e}")
        return []

    results = []
    for item in data.get("Products", []):
        mfr = item.get("Manufacturer", {}) or {}
        mfr_name = mfr.get("Name", "") if isinstance(mfr, dict) else str(mfr)

        cat = item.get("Category", {}) or {}
        cat_name = cat.get("Name", "") if isinstance(cat, dict) else ""
        type_cn = _translate_category(cat_name)

        # 如果 Digi-Key 返回的是泛化顶层分类，用关键词分段分类覆盖
        if default_type and (type_cn in _GENERIC_CATEGORIES or cat_name in _GENERIC_CATEGORIES):
            type_cn = default_type

        params = []
        for p in item.get("Parameters", []):
            name = _translate_param_name(p.get("Parameter", "").strip())
            value = p.get("Value", "").strip()
            params.append({"name": name, "value": value, "unit": ""})

        variations = item.get("ProductVariations", []) or []
        pkg_type = variations[0].get("PackageType", {}).get("Name", "") if variations else ""

        results.append({
            "model": item.get("ManufacturerProductNumber", ""),
            "type": type_cn,
            "package_type": pkg_type,
            "manufacturer": mfr_name,
            "datasheet_url": item.get("DatasheetUrl", ""),
            "image_url": item.get("PhotoUrl", ""),
            "params": params,
        })
    return results


# ═══════════════════════════════════════════════════════════════
# 内置元器件数据（47条）
# ═══════════════════════════════════════════════════════════════

COMPONENTS = [
    # ═══ MCU / 处理器 ═══
    {
        "model": "STM32F103C8T6",
        "type": "MCU",
        "package_type": "LQFP-48",
        "manufacturer": "STMicroelectronics",
        "datasheet_url": "https://www.st.com/resource/en/datasheet/stm32f103c8.pdf",
        "params": [
            {"name": "内核", "value": "ARM Cortex-M3", "unit": ""},
            {"name": "主频", "value": "72", "unit": "MHz"},
            {"name": "Flash", "value": "64", "unit": "KB"},
            {"name": "SRAM", "value": "20", "unit": "KB"},
            {"name": "工作电压", "value": "2.0-3.6", "unit": "V"},
            {"name": "GPIO", "value": "37", "unit": "路"},
            {"name": "ADC", "value": "2×12位", "unit": ""},
            {"name": "工作温度", "value": "-40~85", "unit": "°C"},
        ],
    },
    {
        "model": "STM32F407VGT6",
        "type": "MCU",
        "package_type": "LQFP-100",
        "manufacturer": "STMicroelectronics",
        "datasheet_url": "https://www.st.com/resource/en/datasheet/stm32f407vg.pdf",
        "params": [
            {"name": "内核", "value": "ARM Cortex-M4F", "unit": ""},
            {"name": "主频", "value": "168", "unit": "MHz"},
            {"name": "Flash", "value": "1024", "unit": "KB"},
            {"name": "SRAM", "value": "192", "unit": "KB"},
            {"name": "工作电压", "value": "1.8-3.6", "unit": "V"},
            {"name": "GPIO", "value": "82", "unit": "路"},
            {"name": "DSP", "value": "有", "unit": ""},
            {"name": "FPU", "value": "单精度", "unit": ""},
            {"name": "工作温度", "value": "-40~85", "unit": "°C"},
        ],
    },
    {
        "model": "ESP32-WROOM-32E",
        "type": "MCU/WiFi",
        "package_type": "SMD-38",
        "manufacturer": "Espressif",
        "datasheet_url": "https://www.espressif.com/sites/default/files/documentation/esp32-wroom-32e_datasheet_en.pdf",
        "params": [
            {"name": "内核", "value": "Xtensa LX6 双核", "unit": ""},
            {"name": "主频", "value": "240", "unit": "MHz"},
            {"name": "Flash", "value": "16", "unit": "MB"},
            {"name": "SRAM", "value": "520", "unit": "KB"},
            {"name": "WiFi", "value": "802.11 b/g/n", "unit": ""},
            {"name": "蓝牙", "value": "BLE 4.2", "unit": ""},
            {"name": "工作电压", "value": "3.0-3.6", "unit": "V"},
            {"name": "GPIO", "value": "34", "unit": "路"},
        ],
    },
    {
        "model": "ATmega328P-AU",
        "type": "MCU",
        "package_type": "TQFP-32",
        "manufacturer": "Microchip",
        "datasheet_url": "https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/ATmega328P_DS40001984C.pdf",
        "params": [
            {"name": "内核", "value": "AVR 8位", "unit": ""},
            {"name": "主频", "value": "20", "unit": "MHz"},
            {"name": "Flash", "value": "32", "unit": "KB"},
            {"name": "SRAM", "value": "2", "unit": "KB"},
            {"name": "EEPROM", "value": "1", "unit": "KB"},
            {"name": "工作电压", "value": "1.8-5.5", "unit": "V"},
            {"name": "GPIO", "value": "23", "unit": "路"},
        ],
    },
    {
        "model": "GD32F103CBT6",
        "type": "MCU",
        "package_type": "LQFP-48",
        "manufacturer": "GigaDevice",
        "datasheet_url": "https://www.gigadevice.com.cn/product/mcu/gd32f103cbt6",
        "params": [
            {"name": "内核", "value": "ARM Cortex-M3", "unit": ""},
            {"name": "主频", "value": "108", "unit": "MHz"},
            {"name": "Flash", "value": "128", "unit": "KB"},
            {"name": "SRAM", "value": "20", "unit": "KB"},
            {"name": "工作电压", "value": "2.6-3.6", "unit": "V"},
            {"name": "GPIO", "value": "37", "unit": "路"},
            {"name": "备注", "value": "STM32F103 PIN2PIN替代", "unit": ""},
        ],
    },
    # ═══ 电源管理 IC ═══
    {
        "model": "AMS1117-3.3",
        "type": "LDO稳压器",
        "package_type": "SOT-223",
        "manufacturer": "AMS",
        "datasheet_url": "https://www.advanced-monolithic.com/pdf/ds1117.pdf",
        "params": [
            {"name": "输出电压", "value": "3.3", "unit": "V"},
            {"name": "最大输出电流", "value": "1", "unit": "A"},
            {"name": "输入电压范围", "value": "4.75-15", "unit": "V"},
            {"name": "压差", "value": "1.1", "unit": "V"},
            {"name": "工作温度", "value": "-40~125", "unit": "°C"},
        ],
    },
    {
        "model": "LM2596S-ADJ",
        "type": "DC-DC降压",
        "package_type": "TO-263-5",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/lm2596.pdf",
        "params": [
            {"name": "输入电压", "value": "4.5-40", "unit": "V"},
            {"name": "输出电压", "value": "1.23-37", "unit": "V"},
            {"name": "最大输出电流", "value": "3", "unit": "A"},
            {"name": "开关频率", "value": "150", "unit": "kHz"},
            {"name": "效率", "value": "最高88", "unit": "%"},
            {"name": "工作温度", "value": "-40~125", "unit": "°C"},
        ],
    },
    {
        "model": "MP1584EN",
        "type": "DC-DC降压",
        "package_type": "SOIC-8",
        "manufacturer": "MPS",
        "datasheet_url": "https://www.monolithicpower.com/en/documentview/productdocument/index/version/2/document_type/Datasheet/lang/en/sku/MP1584/",
        "params": [
            {"name": "输入电压", "value": "4.5-28", "unit": "V"},
            {"name": "输出电压", "value": "0.8-25", "unit": "V"},
            {"name": "最大输出电流", "value": "3", "unit": "A"},
            {"name": "开关频率", "value": "1.5", "unit": "MHz"},
            {"name": "效率", "value": "最高95", "unit": "%"},
        ],
    },
    {
        "model": "TPS5430DDAR",
        "type": "DC-DC降压",
        "package_type": "SOIC-8",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/tps5430.pdf",
        "params": [
            {"name": "输入电压", "value": "5.5-36", "unit": "V"},
            {"name": "输出电压", "value": "1.22-31", "unit": "V"},
            {"name": "最大输出电流", "value": "3", "unit": "A"},
            {"name": "开关频率", "value": "500", "unit": "kHz"},
            {"name": "效率", "value": "最高95", "unit": "%"},
        ],
    },
    {
        "model": "TP4056",
        "type": "锂电池充电IC",
        "package_type": "SOP-8",
        "manufacturer": "TPOWER",
        "datasheet_url": "https://www.tpwic.com/uploadfile/202301/TP4056.pdf",
        "params": [
            {"name": "充电电流", "value": "0.1-1", "unit": "A"},
            {"name": "充电电压", "value": "4.2", "unit": "V"},
            {"name": "输入电压", "value": "4.0-8.0", "unit": "V"},
            {"name": "充电方式", "value": "CC/CV 线性", "unit": ""},
            {"name": "保护", "value": "温度/反接", "unit": ""},
        ],
    },
    {
        "model": "XL6009E1",
        "type": "DC-DC升压",
        "package_type": "TO-263-5",
        "manufacturer": "XLSEMI",
        "datasheet_url": "https://www.xlsemi.com/datasheet/XL6009%20datasheet.pdf",
        "params": [
            {"name": "输入电压", "value": "3.6-32", "unit": "V"},
            {"name": "输出电压", "value": "最高45", "unit": "V"},
            {"name": "最大输出电流", "value": "4", "unit": "A"},
            {"name": "开关频率", "value": "400", "unit": "kHz"},
            {"name": "效率", "value": "最高94", "unit": "%"},
        ],
    },
    # ═══ 通信接口 IC ═══
    {
        "model": "CH340G",
        "type": "USB转串口",
        "package_type": "SOP-16",
        "manufacturer": "WCH",
        "datasheet_url": "https://www.wch.cn/downloads/CH340DS1_PDF.html",
        "params": [
            {"name": "接口", "value": "USB 2.0 → UART", "unit": ""},
            {"name": "波特率", "value": "50-2000000", "unit": "bps"},
            {"name": "工作电压", "value": "3.3/5.0", "unit": "V"},
            {"name": "流控", "value": "支持RTS/CTS", "unit": ""},
        ],
    },
    {
        "model": "CP2102-GMR",
        "type": "USB转串口",
        "package_type": "QFN-28",
        "manufacturer": "Silicon Labs",
        "datasheet_url": "https://www.silabs.com/documents/public/data-sheets/cp2102-9.pdf",
        "params": [
            {"name": "接口", "value": "USB 2.0 → UART", "unit": ""},
            {"name": "波特率", "value": "300-1000000", "unit": "bps"},
            {"name": "工作电压", "value": "3.0-3.6", "unit": "V"},
            {"name": "内置", "value": "EEPROM/收发器", "unit": ""},
        ],
    },
    {
        "model": "MAX485ESA+",
        "type": "RS485收发器",
        "package_type": "SOIC-8",
        "manufacturer": "Maxim",
        "datasheet_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/MAX1487-MAX491.pdf",
        "params": [
            {"name": "通信协议", "value": "RS-485/RS-422", "unit": ""},
            {"name": "速率", "value": "2.5", "unit": "Mbps"},
            {"name": "工作电压", "value": "5.0", "unit": "V"},
            {"name": "节点数", "value": "32", "unit": "个"},
            {"name": "ESD保护", "value": "±15kV", "unit": ""},
        ],
    },
    {
        "model": "SP3485EN-L/TR",
        "type": "RS485收发器",
        "package_type": "SOIC-8",
        "manufacturer": "MaxLinear",
        "datasheet_url": "https://www.maxlinear.com/ds/sp3485.pdf",
        "params": [
            {"name": "通信协议", "value": "RS-485/RS-422", "unit": ""},
            {"name": "速率", "value": "10", "unit": "Mbps"},
            {"name": "工作电压", "value": "3.3", "unit": "V"},
            {"name": "节点数", "value": "32", "unit": "个"},
        ],
    },
    {
        "model": "LAN8720A-CP-TR",
        "type": "以太网PHY",
        "package_type": "QFN-24",
        "manufacturer": "Microchip",
        "datasheet_url": "https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/00002165B.pdf",
        "params": [
            {"name": "接口", "value": "RMII", "unit": ""},
            {"name": "速率", "value": "10/100", "unit": "Mbps"},
            {"name": "工作电压", "value": "3.3", "unit": "V"},
            {"name": "功耗", "value": "极低 (SMSC)", "unit": ""},
        ],
    },
    # ═══ 传感器 ═══
    {
        "model": "BME280",
        "type": "环境传感器",
        "package_type": "LGA-8",
        "manufacturer": "Bosch Sensortec",
        "datasheet_url": "https://www.bosch-sensortec.com/media/boschsensortec/downloads/datasheets/bst-bme280-ds002.pdf",
        "params": [
            {"name": "功能", "value": "温度/湿度/气压", "unit": ""},
            {"name": "温度精度", "value": "±1.0", "unit": "°C"},
            {"name": "湿度精度", "value": "±3", "unit": "%RH"},
            {"name": "气压精度", "value": "±1", "unit": "hPa"},
            {"name": "接口", "value": "I²C/SPI", "unit": ""},
            {"name": "工作电压", "value": "1.71-3.6", "unit": "V"},
        ],
    },
    {
        "model": "MPU6050",
        "type": "IMU传感器",
        "package_type": "QFN-24",
        "manufacturer": "TDK InvenSense",
        "datasheet_url": "https://invensense.tdk.com/wp-content/uploads/2015/02/MPU-6000-Datasheet1.pdf",
        "params": [
            {"name": "功能", "value": "3轴陀螺仪+3轴加速度计", "unit": ""},
            {"name": "陀螺仪量程", "value": "±250/500/1000/2000", "unit": "°/s"},
            {"name": "加速度量程", "value": "±2/4/8/16", "unit": "g"},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.375-3.46", "unit": "V"},
        ],
    },
    {
        "model": "VL53L0CXV0DH/1",
        "type": "激光测距",
        "package_type": "LGA-12",
        "manufacturer": "STMicroelectronics",
        "datasheet_url": "https://www.st.com/resource/en/datasheet/vl53l0x.pdf",
        "params": [
            {"name": "测量范围", "value": "最高2000", "unit": "mm"},
            {"name": "精度", "value": "±3", "unit": "%"},
            {"name": "光源", "value": "940nm VCSEL", "unit": ""},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.6-3.5", "unit": "V"},
        ],
    },
    {
        "model": "SHT30-DIS-B",
        "type": "温湿度传感器",
        "package_type": "DFN-8",
        "manufacturer": "Sensirion",
        "datasheet_url": "https://sensirion.com/media/documents/213E6A3B/63A5A569/Datasheet_SHT3x_DIS.pdf",
        "params": [
            {"name": "温度精度", "value": "±0.2", "unit": "°C"},
            {"name": "湿度精度", "value": "±2", "unit": "%RH"},
            {"name": "温度范围", "value": "-40~125", "unit": "°C"},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.15-5.5", "unit": "V"},
        ],
    },
    {
        "model": "DS18B20+",
        "type": "温度传感器",
        "package_type": "TO-92",
        "manufacturer": "Maxim",
        "datasheet_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/DS18B20.pdf",
        "params": [
            {"name": "测量范围", "value": "-55~125", "unit": "°C"},
            {"name": "精度", "value": "±0.5", "unit": "°C"},
            {"name": "分辨率", "value": "9-12", "unit": "位"},
            {"name": "接口", "value": "1-Wire", "unit": ""},
            {"name": "工作电压", "value": "3.0-5.5", "unit": "V"},
        ],
    },
    # ═══ 逻辑/驱动 IC ═══
    {
        "model": "74HC595D",
        "type": "移位寄存器",
        "package_type": "SOP-16",
        "manufacturer": "Nexperia",
        "datasheet_url": "https://assets.nexperia.com/documents/data-sheet/74HC_HCT595.pdf",
        "params": [
            {"name": "功能", "value": "8位移位寄存器+锁存", "unit": ""},
            {"name": "输出电流", "value": "±25", "unit": "mA"},
            {"name": "级联", "value": "支持无限级联", "unit": ""},
            {"name": "工作电压", "value": "2.0-6.0", "unit": "V"},
            {"name": "最高频率", "value": "100", "unit": "MHz"},
        ],
    },
    {
        "model": "ULN2003ADR",
        "type": "达林顿管阵列",
        "package_type": "SOP-16",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/uln2003a.pdf",
        "params": [
            {"name": "通道数", "value": "7", "unit": "路"},
            {"name": "单路输出电流", "value": "500", "unit": "mA"},
            {"name": "输出电压", "value": "最高50", "unit": "V"},
            {"name": "内置", "value": "续流二极管", "unit": ""},
        ],
    },
    {
        "model": "PCA9685PW",
        "type": "PWM驱动器",
        "package_type": "TSSOP-28",
        "manufacturer": "NXP",
        "datasheet_url": "https://www.nxp.com/docs/en/data-sheet/PCA9685.pdf",
        "params": [
            {"name": "通道数", "value": "16", "unit": "路"},
            {"name": "分辨率", "value": "12", "unit": "位"},
            {"name": "频率", "value": "24-1526", "unit": "Hz"},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.3-5.5", "unit": "V"},
        ],
    },
    # ═══ 存储器 ═══
    {
        "model": "W25Q64JVSSIQ",
        "type": "NOR Flash",
        "package_type": "SOIC-8",
        "manufacturer": "Winbond",
        "datasheet_url": "https://www.winbond.com/resource-files/W25Q64JV%20SPI%20RevC%2008102020%20Plus.pdf",
        "params": [
            {"name": "容量", "value": "64", "unit": "Mbit"},
            {"name": "接口", "value": "SPI/QSPI", "unit": ""},
            {"name": "读写速度", "value": "133", "unit": "MHz"},
            {"name": "擦除次数", "value": "10万", "unit": "次"},
            {"name": "工作电压", "value": "2.7-3.6", "unit": "V"},
        ],
    },
    {
        "model": "AT24C02C-SSHM-T",
        "type": "EEPROM",
        "package_type": "SOIC-8",
        "manufacturer": "Microchip",
        "datasheet_url": "https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/AT24C02C-I2C-Compatible-2-Wire-Serial-EEPROM-DS20001941K.pdf",
        "params": [
            {"name": "容量", "value": "2", "unit": "Kbit"},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "擦写次数", "value": "100万", "unit": "次"},
            {"name": "数据保存", "value": "100", "unit": "年"},
            {"name": "工作电压", "value": "1.7-5.5", "unit": "V"},
        ],
    },
    {
        "model": "W25N01GVZEIG",
        "type": "NAND Flash",
        "package_type": "WSON-8",
        "manufacturer": "Winbond",
        "datasheet_url": "https://www.winbond.com/resource-files/W25N01GV%20RevB%20041019.pdf",
        "params": [
            {"name": "容量", "value": "1", "unit": "Gbit"},
            {"name": "接口", "value": "SPI", "unit": ""},
            {"name": "页大小", "value": "2048+64", "unit": "Byte"},
            {"name": "块大小", "value": "64", "unit": "KB"},
            {"name": "工作电压", "value": "2.7-3.6", "unit": "V"},
        ],
    },
    # ═══ 显示/触摸 ═══
    {
        "model": "SSD1306",
        "type": "OLED驱动IC",
        "package_type": "COG/LQFP-52",
        "manufacturer": "Solomon Systech",
        "datasheet_url": "https://cdn-shop.adafruit.com/datasheets/SSD1306.pdf",
        "params": [
            {"name": "分辨率", "value": "128×64", "unit": "像素"},
            {"name": "颜色", "value": "单色（白/蓝）", "unit": ""},
            {"name": "接口", "value": "I²C/SPI/8位并口", "unit": ""},
            {"name": "工作电压", "value": "3.3-5.0", "unit": "V"},
        ],
    },
    {
        "model": "ILI9341V",
        "type": "TFT驱动IC",
        "package_type": "COG",
        "manufacturer": "Ilitek",
        "datasheet_url": "https://www.ilitek.com/upload/PDF/ILI9341_DS_V1.11.pdf",
        "params": [
            {"name": "分辨率", "value": "240×320", "unit": "像素"},
            {"name": "色深", "value": "262K/16.7M", "unit": ""},
            {"name": "接口", "value": "SPI/8位并口", "unit": ""},
            {"name": "工作电压", "value": "1.65-3.3", "unit": "V"},
        ],
    },
    # ═══ 连接器 ═══
    {
        "model": "XH-4A (2.54mm)",
        "type": "线对板连接器",
        "package_type": "THT",
        "manufacturer": "JST替代",
        "datasheet_url": "",
        "params": [
            {"name": "间距", "value": "2.54", "unit": "mm"},
            {"name": "针数", "value": "4", "unit": "P"},
            {"name": "额定电流", "value": "3", "unit": "A"},
            {"name": "额定电压", "value": "250", "unit": "V"},
            {"name": "温度范围", "value": "-25~85", "unit": "°C"},
        ],
    },
    {
        "model": "USB-AF-90D",
        "type": "USB连接器",
        "package_type": "THT-90°",
        "manufacturer": "通用",
        "datasheet_url": "",
        "params": [
            {"name": "类型", "value": "USB 2.0 Type-A 母座", "unit": ""},
            {"name": "安装", "value": "90°直插", "unit": ""},
            {"name": "额定电流", "value": "1.5", "unit": "A"},
            {"name": "寿命", "value": "1500", "unit": "次"},
        ],
    },
    {
        "model": "TYPE-C-31-M-12",
        "type": "USB Type-C",
        "package_type": "SMT",
        "manufacturer": "Molex",
        "datasheet_url": "",
        "params": [
            {"name": "类型", "value": "USB 3.1 Type-C 母座", "unit": ""},
            {"name": "安装", "value": "16P SMT", "unit": ""},
            {"name": "速率", "value": "10", "unit": "Gbps"},
            {"name": "额定电流", "value": "5", "unit": "A"},
        ],
    },
    # ═══ 分立元件 ═══
    {
        "model": "SS34F",
        "type": "肖特基二极管",
        "package_type": "SMAF",
        "manufacturer": "MCC",
        "datasheet_url": "",
        "params": [
            {"name": "VRRM", "value": "40", "unit": "V"},
            {"name": "IF(AV)", "value": "3", "unit": "A"},
            {"name": "VF", "value": "0.55", "unit": "V"},
            {"name": "IR", "value": "0.5", "unit": "mA"},
            {"name": "TRR", "value": "极快", "unit": ""},
        ],
    },
    {
        "model": "BAT54S",
        "type": "肖特基二极管",
        "package_type": "SOT-23",
        "manufacturer": "Nexperia",
        "datasheet_url": "",
        "params": [
            {"name": "VRRM", "value": "30", "unit": "V"},
            {"name": "IF(AV)", "value": "200", "unit": "mA"},
            {"name": "VF", "value": "0.32", "unit": "V"},
            {"name": "配置", "value": "串联双管", "unit": ""},
        ],
    },
    {
        "model": "SI2302DS",
        "type": "N-MOSFET",
        "package_type": "SOT-23",
        "manufacturer": "VBsemi",
        "datasheet_url": "",
        "params": [
            {"name": "VDS", "value": "20", "unit": "V"},
            {"name": "ID", "value": "3", "unit": "A"},
            {"name": "RDS(on)", "value": "45", "unit": "mΩ"},
            {"name": "VGS(th)", "value": "0.5-1.2", "unit": "V"},
            {"name": "应用", "value": "低端开关/电源切换", "unit": ""},
        ],
    },
    {
        "model": "AO3400A",
        "type": "N-MOSFET",
        "package_type": "SOT-23",
        "manufacturer": "AOS",
        "datasheet_url": "",
        "params": [
            {"name": "VDS", "value": "30", "unit": "V"},
            {"name": "ID", "value": "5.7", "unit": "A"},
            {"name": "RDS(on)", "value": "26.5", "unit": "mΩ"},
            {"name": "VGS(th)", "value": "0.9-2.2", "unit": "V"},
        ],
    },
    # ═══ 晶振/时钟 ═══
    {
        "model": "X32258MSB4SI",
        "type": "无源晶振",
        "package_type": "SMD-3225",
        "manufacturer": "YXC",
        "datasheet_url": "",
        "params": [
            {"name": "频率", "value": "8", "unit": "MHz"},
            {"name": "频率公差", "value": "±10", "unit": "ppm"},
            {"name": "负载电容", "value": "20", "unit": "pF"},
            {"name": "温度稳定性", "value": "±30", "unit": "ppm"},
        ],
    },
    {
        "model": "DS3231MZ+",
        "type": "RTC时钟IC",
        "package_type": "SOIC-8",
        "manufacturer": "Maxim",
        "datasheet_url": "https://www.analog.com/media/en/technical-documentation/data-sheets/DS3231M.pdf",
        "params": [
            {"name": "精度", "value": "±2", "unit": "ppm"},
            {"name": "年误差", "value": "<1", "unit": "分钟"},
            {"name": "温度补偿", "value": "内置TCXO", "unit": ""},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.3-5.5", "unit": "V"},
        ],
    },
    # ═══ 射频/无线 ═══
    {
        "model": "nRF24L01P+",
        "type": "2.4GHz射频",
        "package_type": "QFN-20",
        "manufacturer": "Nordic",
        "datasheet_url": "https://www.nordicsemi.com/-/media/DevZone/Other/Product%20Specifications/nRF24L01P_PS_v1.0.pdf",
        "params": [
            {"name": "频段", "value": "2400-2525", "unit": "MHz"},
            {"name": "速率", "value": "250k/1M/2M", "unit": "bps"},
            {"name": "通信距离", "value": "约100", "unit": "m"},
            {"name": "接口", "value": "SPI", "unit": ""},
            {"name": "工作电压", "value": "1.9-3.6", "unit": "V"},
        ],
    },
    {
        "model": "SIM800C",
        "type": "GSM/GPRS模块",
        "package_type": "LCC-42",
        "manufacturer": "SIMCom",
        "datasheet_url": "https://simcom.ee/documents/SIM800C/SIM800C_Hardware_Design_V1.05.pdf",
        "params": [
            {"name": "频段", "value": "850/900/1800/1900", "unit": "MHz"},
            {"name": "GPRS", "value": "Class 12", "unit": ""},
            {"name": "通信接口", "value": "UART", "unit": ""},
            {"name": "工作电压", "value": "3.4-4.4", "unit": "V"},
            {"name": "峰值电流", "value": "2", "unit": "A"},
        ],
    },
    # ═══ 运放/比较器 ═══
    {
        "model": "LM358DR",
        "type": "运算放大器",
        "package_type": "SOP-8",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/lm358.pdf",
        "params": [
            {"name": "通道数", "value": "2", "unit": "路"},
            {"name": "GBW", "value": "1.1", "unit": "MHz"},
            {"name": "SR", "value": "0.3", "unit": "V/μs"},
            {"name": "输入偏置", "value": "典型20", "unit": "nA"},
            {"name": "工作电压", "value": "3-32", "unit": "V"},
        ],
    },
    {
        "model": "LM393DR",
        "type": "电压比较器",
        "package_type": "SOP-8",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/lm393.pdf",
        "params": [
            {"name": "通道数", "value": "2", "unit": "路"},
            {"name": "响应时间", "value": "1.3", "unit": "μs"},
            {"name": "输出类型", "value": "开漏", "unit": ""},
            {"name": "工作电压", "value": "2-30", "unit": "V"},
        ],
    },
    # ═══ 保护器件 ═══
    {
        "model": "SMBJ5.0CA",
        "type": "TVS瞬态抑制",
        "package_type": "SMB",
        "manufacturer": "Littelfuse",
        "datasheet_url": "https://www.littelfuse.com/~/media/electronics/datasheets/tvs_diodes/littelfuse_tvs_diode_smbj_datasheet.pdf.pdf",
        "params": [
            {"name": "VRWM", "value": "5.0", "unit": "V"},
            {"name": "VBR", "value": "6.4-7.0", "unit": "V"},
            {"name": "VCLAMP", "value": "9.2", "unit": "V"},
            {"name": "PPK", "value": "600", "unit": "W"},
            {"name": "极性", "value": "双向", "unit": ""},
        ],
    },
    {
        "model": "PTC自恢复保险丝 1812L110PR",
        "type": "PTC保险丝",
        "package_type": "1812",
        "manufacturer": "Littelfuse",
        "datasheet_url": "",
        "params": [
            {"name": "保持电流", "value": "1.1", "unit": "A"},
            {"name": "跳闸电流", "value": "2.2", "unit": "A"},
            {"name": "最大电压", "value": "6", "unit": "V"},
            {"name": "最大故障电流", "value": "100", "unit": "A"},
        ],
    },
    # ═══ ADC/DAC ═══
    {
        "model": "ADS1115IDGSR",
        "type": "ADC",
        "package_type": "VSSOP-10",
        "manufacturer": "TI",
        "datasheet_url": "https://www.ti.com/lit/ds/symlink/ads1115.pdf",
        "params": [
            {"name": "分辨率", "value": "16", "unit": "位"},
            {"name": "通道数", "value": "4", "unit": "路"},
            {"name": "采样率", "value": "8-860", "unit": "SPS"},
            {"name": "PGA", "value": "±0.256~±6.144V", "unit": ""},
            {"name": "接口", "value": "I²C", "unit": ""},
        ],
    },
    {
        "model": "MCP4725A0T-E/CH",
        "type": "DAC",
        "package_type": "SOT-23-6",
        "manufacturer": "Microchip",
        "datasheet_url": "https://www.microchip.com/content/dam/mchp/documents/OTH/ProductDocuments/DataSheets/22039d.pdf",
        "params": [
            {"name": "分辨率", "value": "12", "unit": "位"},
            {"name": "输出", "value": "0~VDD", "unit": "V"},
            {"name": "内置", "value": "EEPROM", "unit": ""},
            {"name": "接口", "value": "I²C", "unit": ""},
            {"name": "工作电压", "value": "2.7-5.5", "unit": "V"},
        ],
    },
    # ═══ LED驱动 ═══
    {
        "model": "WS2812B-V5",
        "type": "智能LED",
        "package_type": "SMD-5050",
        "manufacturer": "Worldsemi",
        "datasheet_url": "https://www.world-semi.com/uploads/soft/210819/WS2812B_V5(1).pdf",
        "params": [
            {"name": "颜色", "value": "RGB全彩", "unit": ""},
            {"name": "灰度", "value": "256×256×256", "unit": ""},
            {"name": "协议", "value": "单总线归零码", "unit": ""},
            {"name": "级联", "value": "支持无限", "unit": "个"},
            {"name": "工作电压", "value": "3.7-5.3", "unit": "V"},
        ],
    },
]


# ═══════════════════════════════════════════════════════════════
# 导入逻辑
# ═══════════════════════════════════════════════════════════════

def import_components(db, items: list[dict], dry_run: bool = False):
    """将元器件列表写入数据库。已存在的 model 跳过。"""
    inserted = 0
    skipped = 0

    for item in items:
        if not item.get("model"):
            skipped += 1
            continue

        existing = db.query(Component).filter(Component.model == item["model"]).first()
        if existing:
            skipped += 1
            print(f"  [跳过] {item['model']} (已存在)")
            continue

        if dry_run:
            print(f"  [预览] {item['model']} — {item.get('type','?')} — {len(item.get('params', []))} 个参数")
            inserted += 1
            continue

        comp = Component(
            model=item["model"],
            type=item.get("type", "")[:255],
            package_type=item.get("package_type", "")[:255],
            manufacturer=item.get("manufacturer", "")[:255],
            datasheet_url=item.get("datasheet_url", "")[:500],
            image_url=item.get("image_url", "")[:500],
        )
        db.add(comp)
        db.flush()

        for p in item.get("params", []):
            param = ComponentParam(
                component_id=comp.component_id,
                param_name=p.get("name", ""),
                param_value=p.get("value", ""),
                param_unit=p.get("unit", ""),
            )
            db.add(param)

        print(f"  [导入] {item['model']} — {len(item.get('params', []))} 个参数")
        inserted += 1

    if not dry_run and inserted > 0:
        db.commit()

    print(f"\n完成: 导入 {inserted} 条, 跳过 {skipped} 条")
    return inserted, skipped


def import_from_yaml(filepath: str, dry_run: bool = False):
    """从 YAML 文件导入元器件。"""
    import yaml

    with open(filepath, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    if not isinstance(data, list):
        print("Error: YAML 顶层应为数组格式")
        return

    db = SessionLocal()
    try:
        import_components(db, data, dry_run)
    finally:
        db.close()


def import_from_digikey(client_id: str, client_secret: str, keyword: str,
                        max_results: int = 5, dry_run: bool = False,
                        default_type: str = ""):
    """从 Digi-Key 搜索元器件并导入。"""
    print(f"从 Digi-Key 搜索: \"{keyword}\"\n")
    results = _digikey_search(client_id, client_secret, keyword, limit=max_results,
                              default_type=default_type)

    if not results:
        print("未获取到任何数据。")
        return

    print(f"\n获取到 {len(results)} 个元器件，开始导入...\n")
    db = SessionLocal()
    try:
        import_components(db, results, dry_run)
    finally:
        db.close()


def _parse_batch_keywords(filepath: str) -> list[tuple[str, str]]:
    """解析批量关键词文件，返回 [(keyword, section_type), ...]。

    文件格式：
        # ── 分段标题 ──
        关键词1
        关键词2
        # ── 另一个分段 ──
        关键词3
    """
    section_map = {
        "MCU": "MCU/MPU", "MPU": "MCU/MPU",
        "电源管理": "电源管理IC", "电源管理 IC": "电源管理IC",
        "传感器": "传感器",
        "通信接口": "通信接口",
        "存储器": "存储器",
        "运放": "运放/比较器/仪表放大器", "比较器": "运放/比较器/仪表放大器",
        "仪表放大器": "运放/比较器/仪表放大器",
        "ADC": "ADC/DAC", "DAC": "ADC/DAC",
        "逻辑 IC": "逻辑IC", "逻辑": "逻辑IC",
        "MOSFET": "MOSFET",
        "二极管": "二极管",
        "晶振": "晶振/时钟", "时钟": "晶振/时钟",
        "连接器": "连接器",
        "LED": "LED/光耦/光电器件", "光耦": "LED/光耦/光电器件",
        "光电器件": "LED/光耦/光电器件",
        "电阻": "电阻",
        "电容": "电容",
        "电感": "电感/磁珠", "磁珠": "电感/磁珠",
        "保险丝": "保险丝/电路保护", "电路保护": "保险丝/电路保护",
    }
    results = []
    current_section = ""
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            stripped = line.strip()
            if not stripped or stripped.startswith("# ═"):
                continue
            if stripped.startswith("#"):
                # 解析分段标题，如 "# ── MCU / MPU 系列 ──"
                title = stripped.lstrip("# ").strip("─ ").strip()
                for key, val in section_map.items():
                    if key in title:
                        current_section = val
                        break
                continue
            results.append((stripped, current_section))
    return results


def import_from_batch(client_id: str, client_secret: str, filepath: str,
                      max_per: int = 5, dry_run: bool = False):
    """从文本文件批量搜索导入（每行一个关键词，支持分段标题）。"""
    items = _parse_batch_keywords(filepath)
    print(f"批量导入 {len(items)} 个关键词\n")

    for i, (kw, section_type) in enumerate(items):
        print(f"{'='*50}")
        section_info = f"  [{section_type}]" if section_type else ""
        print(f"[{i+1}/{len(items)}] 搜索: {kw}{section_info}")
        print(f"{'='*50}")
        import_from_digikey(client_id, client_secret, kw, max_results=max_per,
                            dry_run=dry_run, default_type=section_type)
        if i < len(items) - 1:
            time.sleep(1)


def _get_digikey_credentials(args) -> tuple[str, str]:
    """从命令行参数或环境变量获取 Digi-Key 凭据。"""
    client_id = args.digikey_client_id or os.environ.get("DIGIKEY_CLIENT_ID")
    client_secret = args.digikey_client_secret or os.environ.get("DIGIKEY_CLIENT_SECRET")

    if not client_id or not client_secret:
        print(
            "错误: 需要 Digi-Key API 凭据。\n\n"
            "获取方式:\n"
            "  1. 访问 https://developer.digikey.com/ 注册（免费）\n"
            "  2. 创建 Organization → 创建 App → 获取 Client ID 和 Client Secret\n"
            "  3. 通过以下方式之一提供凭据:\n"
            "     a) 环境变量:  export DIGIKEY_CLIENT_ID=xxx\n"
            "                   export DIGIKEY_CLIENT_SECRET=xxx\n"
            "     b) 命令行:    --digikey-client-id xxx --digikey-client-secret xxx\n"
        )
        sys.exit(1)

    return client_id, client_secret


# ═══════════════════════════════════════════════════════════════
# CLI
# ═══════════════════════════════════════════════════════════════

def main():
    parser = argparse.ArgumentParser(
        description="电子元器件知识库导入脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  python scripts/import_components.py                                 # 导入内置数据
  python scripts/import_components.py --dry-run                       # 预览内置数据
  python scripts/import_components.py --yaml data.yaml                # 从YAML导入
  python scripts/import_components.py --search STM32F103C8T6          # 从Digi-Key搜索导入
  python scripts/import_components.py --search STM32F103C8T6 --dry-run  # 搜索预览
  python scripts/import_components.py --batch models.txt              # 批量搜索导入

Digi-Key API Key 注册: https://developer.digikey.com/ (免费)
        """,
    )
    parser.add_argument("--dry-run", action="store_true", help="仅预览，不写入数据库")
    parser.add_argument("--yaml", type=str, help="从 YAML 文件导入")
    parser.add_argument("--search", type=str, help="从 Digi-Key 搜索型号并导入")
    parser.add_argument("--batch", type=str, help="从文本文件批量搜索导入（每行一个型号）")
    parser.add_argument("--max", type=int, default=5, help="每个关键词最多导入条数（默认5）")
    parser.add_argument("--digikey-client-id", type=str, help="Digi-Key Client ID")
    parser.add_argument("--digikey-client-secret", type=str, help="Digi-Key Client Secret")
    args = parser.parse_args()

    if args.search:
        cid, csec = _get_digikey_credentials(args)
        import_from_digikey(cid, csec, args.search, max_results=args.max, dry_run=args.dry_run)
    elif args.batch:
        cid, csec = _get_digikey_credentials(args)
        import_from_batch(cid, csec, args.batch, max_per=args.max, dry_run=args.dry_run)
    elif args.yaml:
        print(f"从 YAML 文件导入: {args.yaml}\n")
        import_from_yaml(args.yaml, args.dry_run)
    else:
        print(f"导入内置元器件数据 ({len(COMPONENTS)} 条)\n")
        db = SessionLocal()
        try:
            import_components(db, COMPONENTS, args.dry_run)
        finally:
            db.close()


if __name__ == "__main__":
    main()
