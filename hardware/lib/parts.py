"""自定义 SKiDL 零件模板（不依赖 KiCad 库）。

这里为 InstaFreeHeart BOM 中的每颗芯片定义 Part TEMPLATE，引脚按
真实 datasheet（嘉立创/原厂）建立。其它 .py 文件通过 ``from
hardware.lib.parts import *`` 引入实例。

参考 datasheet：
    * ESP32-S3-WROOM-1   v1.5  (Espressif)        — 44pin SMD
    * IP5306             v2.0  (Injoinic)         — ESOP-8
    * OV5640                  (OmniVision)        — DVP-24P FPC, HW HDR
    * INMP441                 (TDK InvenSense)    — LGA-6
    * CW2015             v1.4  (Cellwise)         — DFN-8
    * SY8088                  (Silergy)           — SOT-23-5 buck
    * WS2812B-2020            (Worldsemi)         — 2020 LED
    * USB Type-C 16P          (TYPE-C-31-M-12)    — 16P 母座
    * USBLC6-2SC6             (ST)                — SOT-23-6
    * AO3400A                 (AOS)               — SOT-23 NMOS
    * TF Push-Push 9P         (Hua-Yuan)          — SD card
"""
from skidl import Part, Pin, TEMPLATE, set_default_tool, SKIDL

set_default_tool(SKIDL)


def _mk(name: str, pin_defs, footprint: str = "", value: str | None = None,
        description: str = "") -> Part:
    """根据 (pin_num, pin_name, func) 列表创建 Part 模板."""
    p = Part(lib=None, name=name, dest=TEMPLATE, footprint=footprint,
             value=value or name, description=description, tool=SKIDL)
    p.pins = []
    func_map = {
        "I": Pin.types.INPUT,
        "O": Pin.types.OUTPUT,
        "B": Pin.types.BIDIR,
        "P": Pin.types.PWRIN,
        "G": Pin.types.PWRIN,
        "W": Pin.types.PWROUT,
        "PASSIVE": Pin.types.PASSIVE,
        "OPENCOLLECTOR": Pin.types.OPENCOLL,
        "NC": Pin.types.NOCONNECT,
    }
    for num, pname, func in pin_defs:
        p.add_pins(Pin(num=str(num), name=pname,
                       func=func_map.get(func, Pin.types.PASSIVE)))
    return p


# ---------------------------------------------------------------------------
# U1: ESP32-S3-WROOM-1-N16R8（按官方 pin map，仅暴露在模组上的 IO）
# ---------------------------------------------------------------------------
ESP32S3 = _mk(
    name="ESP32-S3-WROOM-1-N16R8",
    footprint="Module:ESP32-S3-WROOM-1",
    description="MCU module: dual-core LX7 @240MHz + 16MB Flash + 8MB OctPSRAM "
                "+ WiFi 2.4G + BT5",
    pin_defs=[
        (1,  "GND",   "G"),
        (2,  "3V3",   "P"),
        (3,  "EN",    "I"),
        (4,  "IO4",   "B"),
        (5,  "IO5",   "B"),
        (6,  "IO6",   "B"),
        (7,  "IO7",   "B"),
        (8,  "IO15",  "B"),
        (9,  "IO16",  "B"),
        (10, "IO17",  "B"),
        (11, "IO18",  "B"),
        (12, "IO8",   "B"),
        (13, "IO19",  "B"),    # USB D-
        (14, "IO20",  "B"),    # USB D+
        (15, "IO3",   "B"),
        (16, "IO46",  "B"),
        (17, "IO9",   "B"),
        (18, "IO10",  "B"),
        (19, "IO11",  "B"),
        (20, "IO12",  "B"),
        (21, "IO13",  "B"),
        (22, "IO14",  "B"),
        (23, "IO21",  "B"),
        (24, "IO47",  "B"),
        (25, "IO48",  "B"),
        (26, "IO45",  "B"),
        (27, "IO0",   "B"),
        (28, "IO35",  "B"),    # 模组内部 PSRAM 占用，不可外接
        (29, "IO36",  "B"),    # 模组内部 PSRAM 占用，不可外接
        (30, "IO37",  "B"),    # 模组内部 PSRAM 占用，不可外接
        (31, "IO38",  "B"),
        (32, "IO39",  "B"),
        (33, "IO40",  "B"),
        (34, "IO41",  "B"),
        (35, "IO42",  "B"),
        (36, "RXD0",  "I"),    # IO44
        (37, "TXD0",  "O"),    # IO43
        (38, "IO2",   "B"),
        (39, "IO1",   "B"),
        (40, "GND",   "G"),
        (41, "GND",   "G"),    # EPAD（实际为底部散热焊盘）
    ],
)


# ---------------------------------------------------------------------------
# U2: OV5640 摄像头（24P 0.5mm FPC）
# ---------------------------------------------------------------------------
# 嘉立创 C44391
# 5MP + 硬件 HDR (line-interleaved)，I²C 地址 0x3C
OV5640 = _mk(
    name="OV5640",
    footprint="Connector:FFC-0.5-24P",
    description="5MP DVP CMOS image sensor with hardware HDR support",
    pin_defs=[
        (1,  "GND",    "G"),
        (2,  "3V3",    "P"),
        (3,  "SIO_C",  "I"),
        (4,  "SIO_D",  "B"),
        (5,  "VSYNC",  "O"),
        (6,  "HREF",   "O"),
        (7,  "PCLK",   "O"),
        (8,  "XCLK",   "I"),
        (9,  "D9",     "O"),
        (10, "D8",     "O"),
        (11, "D7",     "O"),
        (12, "D6",     "O"),
        (13, "D5",     "O"),
        (14, "D4",     "O"),
        (15, "D3",     "O"),
        (16, "D2",     "O"),
        (17, "RESET",  "I"),
        (18, "PWDN",   "I"),
        (19, "GND",    "G"),
        (20, "3V3",    "P"),
        (21, "GND",    "G"),
        (22, "DOVDD",  "P"),
        (23, "GND",    "G"),
        (24, "GND",    "G"),
    ],
)


# ---------------------------------------------------------------------------
# U3: INMP441 I2S MEMS Microphone
# ---------------------------------------------------------------------------
INMP441 = _mk(
    name="INMP441",
    footprint="Sensor_Audio:InvenSense_INMP441-6_3.76x4.72mm",
    description="Omnidirectional digital MEMS microphone with I2S output "
                "(SD pin is tri-state, allows shared bus for stereo)",
    pin_defs=[
        (1, "SCK",  "I"),
        (2, "SD",   "B"),    # BIDIR: 实际是 tri-state（Hi-Z 半周期），允许双麦共用
        (3, "WS",   "I"),
        (4, "L/R",  "I"),
        (5, "GND",  "G"),
        (6, "VDD",  "P"),
    ],
)


# ---------------------------------------------------------------------------
# U4: IP5306 (I2C版本) 移动电源 SoC
# ---------------------------------------------------------------------------
IP5306 = _mk(
    name="IP5306",
    footprint="Package_SO:ESOP-8_3.9x4.9mm_P1.27mm_EP2.41x3.61mm",
    description="Single-chip power bank: Li-ion charger + 5V boost + LED + key",
    pin_defs=[
        (1, "L",       "PASSIVE"),   # 升压电感节点
        (2, "VOUT",    "B"),         # 5V 输出（双向 — 既输出又作为电源参考）
        (3, "VBAT",    "B"),         # 锂电池（充入/放出 双向）
        (4, "GND",     "G"),
        (5, "VIN",     "P"),         # USB VBUS 5V
        (6, "KEY",     "I"),         # 按键 + 状态控制
        (7, "LIGHT",   "O"),         # 手电控制（未使用 → NC）
        (8, "BASE",    "O"),         # LED 灯电指示（接 4 颗指示灯，可选）
    ],
)


# ---------------------------------------------------------------------------
# U5: CW2015 库仑计电量计
# ---------------------------------------------------------------------------
CW2015 = _mk(
    name="CW2015",
    footprint="Package_DFN_QFN:DFN-8-1EP_2x3mm_P0.5mm_EP0.61x2.2mm",
    description="I2C fuel gauge for 1S Li-ion battery",
    pin_defs=[
        (1, "VDD",    "P"),     # 接 BAT+
        (2, "ALERT",  "O"),     # OD 输出，可悬空
        (3, "SCL",    "I"),
        (4, "SDA",    "B"),
        (5, "NC",     "NC"),
        (6, "NC",     "NC"),
        (7, "NC",     "NC"),
        (8, "GND",    "G"),
        (9, "EPAD",   "G"),
    ],
)


# ---------------------------------------------------------------------------
# U6: SY8088ABC — 1.5 MHz/1A 同步降压 buck
# ---------------------------------------------------------------------------
# 嘉立创 C36420，SOT-23-5，η=92% @ 200 mA
# Vin: 2.7~6.5 V，Vout: 3.3 V (用 1MΩ + 619kΩ 反馈分压)
# 外围：1× 2.2 µH 功率电感 + 1× 22 µF (in) + 1× 10 µF (out)
SY8088 = _mk(
    name="SY8088",
    footprint="Package_TO_SOT_SMD:SOT-23-5",
    description="3.3V/1A synchronous buck, 1.5MHz, 92% efficiency",
    pin_defs=[
        (1, "EN",  "I"),       # 高电平开启，>0.85 V
        (2, "GND", "G"),
        (3, "LX",  "PASSIVE"), # 开关节点（接电感）
        (4, "VIN", "P"),       # 接 BAT (3.0~4.2V)
        (5, "FB",  "I"),       # 反馈，0.6 V 内部基准
    ],
)


# ---------------------------------------------------------------------------
# WS2812B-2020 (单颗灯珠 — 4P)
# ---------------------------------------------------------------------------
WS2812B = _mk(
    name="WS2812B-2020",
    footprint="LED_SMD:LED_WS2812B-2020",
    description="Addressable RGB LED with built-in controller",
    pin_defs=[
        (1, "VDD",  "P"),
        (2, "DOUT", "O"),
        (3, "GND",  "G"),
        (4, "DIN",  "I"),
    ],
)


# ---------------------------------------------------------------------------
# USB-C 母座（TYPE-C-31-M-12 / 16P 板上型）
# ---------------------------------------------------------------------------
USB_C = _mk(
    name="USB-C-16P",
    footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
    description="USB Type-C receptacle, 16-pin (CC1/CC2 separated)",
    pin_defs=[
        ("A1",  "GND",  "G"),
        ("A4",  "VBUS", "P"),
        ("A5",  "CC1",  "B"),
        ("A6",  "DP1",  "B"),
        ("A7",  "DN1",  "B"),
        ("A8",  "SBU1", "B"),
        ("A9",  "VBUS", "P"),
        ("A12", "GND",  "G"),
        ("B1",  "GND",  "G"),
        ("B4",  "VBUS", "P"),
        ("B5",  "CC2",  "B"),
        ("B6",  "DP2",  "B"),
        ("B7",  "DN2",  "B"),
        ("B8",  "SBU2", "B"),
        ("B9",  "VBUS", "P"),
        ("B12", "GND",  "G"),
        ("S1",  "SHIELD", "G"),
    ],
)


# ---------------------------------------------------------------------------
# USBLC6-2SC6 ESD 保护
# ---------------------------------------------------------------------------
USBLC6 = _mk(
    name="USBLC6-2SC6",
    footprint="Package_TO_SOT_SMD:SOT-23-6",
    description="USB 2.0 ESD protection diode array",
    pin_defs=[
        (1, "IO1", "B"),    # D+/D- 数据通过侧
        (2, "GND", "G"),
        (3, "IO2", "B"),
        (4, "IO2'", "B"),
        (5, "VBUS", "P"),
        (6, "IO1'", "B"),
    ],
)


# ---------------------------------------------------------------------------
# AO3400A NMOS（负载开关）
# ---------------------------------------------------------------------------
AO3400 = _mk(
    name="AO3400A",
    footprint="Package_TO_SOT_SMD:SOT-23",
    description="N-channel MOSFET 30V/5.7A logic-level",
    pin_defs=[
        (1, "G", "I"),
        (2, "S", "PASSIVE"),
        (3, "D", "PASSIVE"),
    ],
)


# ---------------------------------------------------------------------------
# microSD Push-Push（9P）
# ---------------------------------------------------------------------------
SD_CARD = _mk(
    name="microSD_Push-Push",
    footprint="Connector_Card:microSD_HC_Hirose_DM3D-SF",
    description="microSD card socket, push-push, 9P",
    pin_defs=[
        (1, "DAT2",  "B"),
        (2, "DAT3_CS", "B"),
        (3, "CMD_DI", "B"),
        (4, "VDD",   "P"),
        (5, "CLK",   "I"),
        (6, "VSS",   "G"),
        (7, "DAT0_DO", "B"),
        (8, "DAT1",  "B"),
        (9, "CD",    "O"),     # 卡检测
    ],
)


# ---------------------------------------------------------------------------
# 通用按键（4 脚 SMD）
# ---------------------------------------------------------------------------
TACT_SW = _mk(
    name="SW_TACT_4P",
    footprint="Button_Switch_SMD:SW_SPST_TS-1187A",
    description="Tactile switch 4×4×1.5mm SMD",
    pin_defs=[
        (1, "A", "PASSIVE"),
        (2, "A", "PASSIVE"),
        (3, "B", "PASSIVE"),
        (4, "B", "PASSIVE"),
    ],
)


# ---------------------------------------------------------------------------
# 通用 LED（0805）
# ---------------------------------------------------------------------------
LED_0805 = _mk(
    name="LED_0805",
    footprint="LED_SMD:LED_0805_2012Metric",
    description="Standard SMD LED",
    pin_defs=[
        (1, "K", "PASSIVE"),
        (2, "A", "PASSIVE"),
    ],
)


# ---------------------------------------------------------------------------
# DW01A 1S 锂电池保护 IC （SOT-23-6）
# ---------------------------------------------------------------------------
DW01A = _mk(
    name="DW01A",
    footprint="Package_TO_SOT_SMD:SOT-23-6",
    description="1S Li-Ion battery protection (over-charge/discharge/short)",
    pin_defs=[
        (1, "OD",  "O"),         # 放电控制（接 8205A G1）
        (2, "CS",  "I"),         # 过流采样（监测 P-）
        (3, "OC",  "O"),         # 充电控制（接 8205A G2）
        (4, "TD",  "PASSIVE"),   # 延时电容引脚（NC 也可工作）
        (5, "GND", "G"),         # 接电池负极
        (6, "VDD", "P"),         # 接电池正极
    ],
)


# ---------------------------------------------------------------------------
# 8205A (FS8205) 双 N-MOSFET （SOT-23-6 共漏极）
# ---------------------------------------------------------------------------
FS8205 = _mk(
    name="8205A",
    footprint="Package_TO_SOT_SMD:SOT-23-6",
    description="Dual N-MOSFET, common drain (battery protection partner)",
    pin_defs=[
        (1, "S1", "PASSIVE"),
        (2, "G1", "I"),
        (3, "D2", "PASSIVE"),    # 漏极内部连通 D1
        (4, "S2", "PASSIVE"),
        (5, "G2", "I"),
        (6, "D1", "PASSIVE"),
    ],
)


# ---------------------------------------------------------------------------
# ADS1115 — 4 通道 16-bit I²C ADC（用于 NTC 温度采集）
# ---------------------------------------------------------------------------
# 嘉立创 C37593 / TI ADS1115IDGSR  MSOP-10
# 默认地址：ADDR -> GND = 0x48
# AIN0..3 是 4 个单端模拟输入（也可两两差分），分辨率 16 bit，
# 内置 PGA（±0.256~±6.144 V），采样速率最高 860 sps。
ADS1115 = _mk(
    name="ADS1115",
    footprint="Package_SO:MSOP-10_3x3mm_P0.5mm",
    description="16-bit 4-ch I2C ADC (used for 3 NTC temperature sensors)",
    pin_defs=[
        (1,  "ADDR",  "I"),         # 地址选择脚（接 GND → 0x48）
        (2,  "ALERT", "O"),         # 阈值告警/RDY（开漏，可悬空）
        (3,  "GND",   "G"),
        (4,  "AIN0",  "I"),         # NTC_BAT 分压点
        (5,  "AIN1",  "I"),         # NTC_PMU 分压点
        (6,  "AIN2",  "I"),         # NTC_MCU 分压点
        (7,  "AIN3",  "I"),         # 预留
        (8,  "VDD",   "P"),         # 接 V3V3
        (9,  "SDA",   "B"),
        (10, "SCL",   "I"),
    ],
)


# ---------------------------------------------------------------------------
# NTC 热敏电阻 — MF52E 10 kΩ B25/50 = 3950，0805
# ---------------------------------------------------------------------------
# 嘉立创 C25750
# 接法：V3V3 ── R_pu(10k) ──┬── ADC AIN_x
#                            └── NTC ── GND
# 室温 25 ℃ R_NTC = 10 kΩ → AIN_x = V3V3/2 = 1.65 V
# 50 ℃ R_NTC ≈ 4.16 kΩ → AIN_x ≈ 0.96 V
NTC_10K = _mk(
    name="NTC_10K_B3950",
    footprint="Resistor_SMD:R_0805_2012Metric",
    description="NTC thermistor 10K ohm @25C, B3950, +-1%",
    pin_defs=[
        (1, "1", "PASSIVE"),
        (2, "2", "PASSIVE"),
    ],
)
