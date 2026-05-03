"""InstaFreeHeart 主原理图 — SKiDL 描述。

运行：
    cd /Users/mac/workspace/InstaFreeHeart
    PYTHONPATH=$PYTHONPATH:hardware  python3 hardware/schematic.py

输出：
    hardware/output/instafreeheart.net   (SKiDL 风格 netlist)
    hardware/output/instafreeheart.xml   (KiCad 兼容 netlist 可在 KiCad / 嘉
                                          立创 EDA 中导入并自动布线)
    hardware/output/instafreeheart.erc   (ERC 检查报告)

说明：
    * 所有 GPIO 命名严格遵循 ESP32-S3-WROOM-1 模组焊盘编号（见
      ``hardware/lib/parts.py``）。
    * I²C 总线、I²S、SPI、DVP 等总线都使用 ``Bus`` 抽象，便于阅读。
"""
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT))

from skidl import (  # noqa: E402
    Net, Bus, Part, Pin, generate_netlist, generate_xml, ERC,
    set_default_tool, SKIDL, KICAD, TEMPLATE,
)

set_default_tool(SKIDL)


def NC(*pins):
    """将传入的引脚标记为 No-Connect（关闭其 ERC 检查）."""
    for p in pins:
        p.do_erc = False
    return pins

from lib.parts import (  # noqa: E402
    ESP32S3, OV5640, INMP441, IP5306, CW2015, SY8088,
    WS2812B, USB_C, USBLC6, AO3400, SD_CARD, TACT_SW, LED_0805,
    DW01A, FS8205, ADS1115, NTC_10K,
)


# ---------------------------------------------------------------------------
# 1. 电源网络
# ---------------------------------------------------------------------------
GND   = Net("GND")
VBUS  = Net("VBUS_5V")           # USB-C 输入
VBAT  = Net("VBAT")              # 锂电池 3.7 V
VOUT5 = Net("VOUT_5V")           # IP5306 升压输出
V3V3  = Net("V3V3")              # 系统 3.3 V

GND.drive  = Pin.drives.POWER
VBUS.drive = Pin.drives.POWER
VBAT.drive = Pin.drives.POWER
VOUT5.drive = Pin.drives.POWER
V3V3.drive = Pin.drives.POWER


# ---------------------------------------------------------------------------
# 2. USB-C 输入 + ESD 保护
# ---------------------------------------------------------------------------
J_USB = USB_C(ref="J1")
ESD   = USBLC6(ref="U9")

# VBUS 合并
J_USB["A4", "A9", "B4", "B9"] += VBUS
J_USB["A1", "A12", "B1", "B12", "S1"] += GND

# CC1 / CC2 各自 5.1k 下拉到 GND（识别为 UFP 受电）
R_CC1 = Part(lib=None, name="R", value="5.1k", footprint="Resistor_SMD:R_0402_1005Metric",
             dest=TEMPLATE, tool=SKIDL)
R_CC1.add_pins(Pin(num="1", name="~", func=Pin.types.PASSIVE),
               Pin(num="2", name="~", func=Pin.types.PASSIVE))
RCC1 = R_CC1(ref="R1")
RCC2 = R_CC1(ref="R2")
J_USB["A5"] += RCC1[1]
RCC1[2]   += GND
J_USB["B5"] += RCC2[1]
RCC2[2]   += GND

# USB 数据通过 ESD 保护后接 ESP32 的 IO19/20
USB_DP = Net("USB_DP")
USB_DN = Net("USB_DN")
J_USB["A6", "B6"] += USB_DP
J_USB["A7", "B7"] += USB_DN
ESD["VBUS"] += VBUS
ESD["GND"]  += GND
ESD[1]      += USB_DP        # IO1 通过 = D+
ESD[6]      += Net("USB_DP_MCU")
ESD[3]      += USB_DN        # IO2 通过 = D-
ESD[4]      += Net("USB_DN_MCU")

USB_DP_MCU = ESD[6].net
USB_DN_MCU = ESD[4].net


# ---------------------------------------------------------------------------
# 3. IP5306 充电 + 升压
# ---------------------------------------------------------------------------
PMIC = IP5306(ref="U4")
PMIC["VIN"]  += VBUS
PMIC["VBAT"] += VBAT
PMIC["VOUT"] += VOUT5
PMIC["GND"]  += GND

# 升压电感 2.2 µH
L_BOOST = Part(lib=None, name="L", value="2.2uH",
               footprint="Inductor_SMD:L_6.0x6.0_H3.0", dest=TEMPLATE, tool=SKIDL)
L_BOOST.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
                 Pin(num="2", func=Pin.types.PASSIVE))
L1 = L_BOOST(ref="L1")
L1[1] += PMIC["L"]
L1[2] += VBAT     # 拓扑：IP5306 内部 BOOST，电感跨在 SW 与 VBAT 之间

# IP5306 KEY → ESP32 IO45（开机/状态检测）
NET_KEY = Net("PMIC_KEY")
PMIC["KEY"] += NET_KEY


# ---------------------------------------------------------------------------
# 4. 双锂电池并联 (1S2P) + DW01A/8205A 保护板 + CW2015 电量计
# ---------------------------------------------------------------------------
# 电池芯 → 保护板 → 系统 GND。VBAT 节点是「保护板之后」的电池正极。
# 电池本身的负极 (BAT_CELL_N) 由 8205A 上的 S1/S2 串联到系统 GND。

VBAT_CELL_N = Net("BAT_CELL_N")     # 电池负极（保护板上游）
VBAT_CELL_N.drive = Pin.drives.POWER

P_BAT = Part(lib=None, name="Conn_BAT", value="BAT_3.7V_2000mAh",
             footprint="Connector:Solder_Pad_2P", dest=TEMPLATE, tool=SKIDL)
P_BAT.add_pins(Pin(num="1", name="+", func=Pin.types.PASSIVE),
               Pin(num="2", name="-", func=Pin.types.PASSIVE))
BAT1 = P_BAT(ref="BAT1")     # 第一颗 2000 mAh 软包
BAT2 = P_BAT(ref="BAT2")     # 第二颗 2000 mAh 软包，并联（总 4000 mAh）
BAT1[1] += VBAT
BAT1[2] += VBAT_CELL_N
BAT2[1] += VBAT
BAT2[2] += VBAT_CELL_N

# DW01A 保护 IC
PROT = DW01A(ref="U11")
PROT["VDD"] += VBAT             # VDD 接电池正
PROT["GND"] += VBAT_CELL_N      # GND 接电池负
PROT["CS"]  += GND              # CS 接 P-（系统 GND 即保护板对外的负极）

# 延时电容（DW01A 的 TD 脚需要 0.1µF 到 GND；可省）
add_pin_cap_TD = Part(lib=None, name="C", value="100nF",
                      footprint="Capacitor_SMD:C_0402_1005Metric",
                      dest=TEMPLATE, tool=SKIDL)
add_pin_cap_TD.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
                         Pin(num="2", func=Pin.types.PASSIVE))
C_TD = add_pin_cap_TD(ref="C6")
C_TD[1] += PROT["TD"]
C_TD[2] += VBAT_CELL_N

# 8205A 双 NMOS：D1/D2 共漏，S1 在电池负侧，S2 在系统 GND 侧
PMOS = FS8205(ref="Q2")
PMOS["S1"] += VBAT_CELL_N
PMOS["S2"] += GND
PMOS["D1"] += Net("BMS_DRAIN")   # 内部相连
PMOS["D2"] += PMOS["D1"].net     # 显式短接 D1==D2
PMOS["G1"] += PROT["OD"]         # 放电 MOSFET
PMOS["G2"] += PROT["OC"]         # 充电 MOSFET

# 保护板对外保留 R 限流（DW01A → 8205A G 之间常用 1 kΩ；这里 100Ω 足以）
R_BMS = Part(lib=None, name="R", value="100R",
             footprint="Resistor_SMD:R_0402_1005Metric",
             dest=TEMPLATE, tool=SKIDL)
R_BMS.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
               Pin(num="2", func=Pin.types.PASSIVE))
# DW01A VDD 经 R 接 BAT+（典型电路）
R_VDD = R_BMS(ref="R10")
R_VDD[1] += VBAT
R_VDD[2] += PROT["VDD"]
# DW01A VDD 退耦电容
C_VDD = add_pin_cap_TD(ref="C7")
C_VDD[1] += PROT["VDD"]
C_VDD[2] += VBAT_CELL_N

# CW2015 电量计跨在「保护板之后」的 VBAT 上
FUEL = CW2015(ref="U5")
FUEL["VDD"] += VBAT
FUEL["GND"] += GND
FUEL["EPAD"] += GND


# ---------------------------------------------------------------------------
# 5. 3.3 V 主电源（SY8088 Buck — 直接 BAT → 3.3V，η=92%）
# -----------------------------------------------------------------------------
# SY8088 同步 buck，1.5 MHz，2.7~6.5V 输入覆盖锂电全程，输出 3.3V/1A。
# 反馈分压（FB 内部基准 0.6V）：
#   R_FB1 = 1 MΩ (上)，R_FB2 = 220 kΩ (下)
#   Vout = 0.6 × (1 + 1000 / 220) = 3.32 V ≈ 3.3 V ✓
# 外围：2.2 µH 功率电感 + 22 µF (in) + 10 µF (out)
# 5V 路径仍由 IP5306 提供（仅在 USB-C 充电 + 5V 输出时启用），WS2812B 灯环
# 走 5V，主控/摄像头/麦克风/传感器走 3V3 直供。
# -----------------------------------------------------------------------------
BUCK = SY8088(ref="U6")
BUCK["VIN"] += VBAT          # ★ 直接接电池正极
BUCK["GND"] += GND
BUCK["EN"]  += VBAT          # 始终使能（默认上电）

# 输出节点 LX → L → V3V3
BUCK_LX = Net("BUCK_LX")
BUCK["LX"] += BUCK_LX

L_BUCK = Part(lib=None, name="L", value="2.2uH",
              footprint="Inductor_SMD:L_2520", dest=TEMPLATE, tool=SKIDL)
L_BUCK.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
                Pin(num="2", func=Pin.types.PASSIVE))
L2 = L_BUCK(ref="L2")
L2[1] += BUCK_LX
L2[2] += V3V3

# 反馈分压（1 MΩ + 220 kΩ → Vout = 3.32 V）
R_FB = Part(lib=None, name="R", value="placeholder",
            footprint="Resistor_SMD:R_0402_1005Metric",
            dest=TEMPLATE, tool=SKIDL)
R_FB.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
              Pin(num="2", func=Pin.types.PASSIVE))
R_FB1 = R_FB(ref="R30", value="1M")     # 上
R_FB2 = R_FB(ref="R31", value="220k")   # 下
R_FB1[1] += V3V3
R_FB1[2] += BUCK["FB"]
R_FB2[1] += BUCK["FB"]
R_FB2[2] += GND


# ---------------------------------------------------------------------------
# 6. ESP32-S3 主控
# ---------------------------------------------------------------------------
MCU = ESP32S3(ref="U1")
MCU["3V3"] += V3V3
MCU["GND"] += GND
# EPAD/底部地（pin 41）已通过模组内部到 GND
MCU["EN"]  += V3V3       # 上电默认运行；需要复位按键再加 RC

# USB
MCU["IO19"] += USB_DN_MCU
MCU["IO20"] += USB_DP_MCU

# 系统控制信号
MCU["IO45"] += NET_KEY                    # 检测 IP5306 KEY 状态
LED_PWR_NET = Net("LED_PWR")
MCU["IO46"] += LED_PWR_NET                # 状态绿灯


# ---------------------------------------------------------------------------
# 7. I2C 总线（OV5640 SCCB + CW2015 + ADS1115 共用）
# ---------------------------------------------------------------------------
I2C = Bus("I2C", 2)
I2C[0].name = "I2C_SDA"
I2C[1].name = "I2C_SCL"

MCU["IO4"] += I2C[0]
MCU["IO5"] += I2C[1]

R_PU = Part(lib=None, name="R", value="4.7k",
            footprint="Resistor_SMD:R_0402_1005Metric", dest=TEMPLATE, tool=SKIDL)
R_PU.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
              Pin(num="2", func=Pin.types.PASSIVE))
R_SDA = R_PU(ref="R3"); R_SDA[1] += V3V3; R_SDA[2] += I2C[0]
R_SCL = R_PU(ref="R4"); R_SCL[1] += V3V3; R_SCL[2] += I2C[1]

FUEL["SDA"] += I2C[0]
FUEL["SCL"] += I2C[1]


# ---------------------------------------------------------------------------
# 8. OV5640 摄像头模组（DVP，5MP，硬件 line-interleaved HDR）
# -----------------------------------------------------------------------------
# I²C 地址 0x3C，软件用 esp32-camera 库 + sensor=OV5640。
# -----------------------------------------------------------------------------
CAM = OV5640(ref="U2")
CAM["3V3"]   += V3V3
CAM["DOVDD"] += V3V3
CAM["GND"]   += GND
CAM["SIO_D"] += I2C[0]
CAM["SIO_C"] += I2C[1]

# DVP 数据 / 时序
DVP = Bus("DVP", 8)
for i in range(8):
    DVP[i].name = f"CAM_D{i}"

cam_data_pins = ["D2", "D3", "D4", "D5", "D6", "D7", "D8", "D9"]
mcu_data_ios  = ["IO11", "IO9", "IO8", "IO10",
                 "IO12", "IO18", "IO17", "IO16"]
for i in range(8):
    CAM[cam_data_pins[i]] += DVP[i]
    MCU[mcu_data_ios[i]]  += DVP[i]

CAM_VSYNC = Net("CAM_VSYNC"); CAM["VSYNC"] += CAM_VSYNC; MCU["IO6"]  += CAM_VSYNC
CAM_HREF  = Net("CAM_HREF");  CAM["HREF"]  += CAM_HREF;  MCU["IO7"]  += CAM_HREF
CAM_PCLK  = Net("CAM_PCLK");  CAM["PCLK"]  += CAM_PCLK;  MCU["IO13"] += CAM_PCLK
CAM_XCLK  = Net("CAM_XCLK");  CAM["XCLK"]  += CAM_XCLK;  MCU["IO15"] += CAM_XCLK
CAM_PWDN  = Net("CAM_PWDN");  CAM["PWDN"]  += CAM_PWDN;  MCU["IO21"] += CAM_PWDN
# RESET 上拉到 3V3 (datasheet 推荐悬空时由 SCCB 复位)
CAM["RESET"] += V3V3


# ---------------------------------------------------------------------------
# 9. INMP441 双麦克风（I²S 立体声 = 差分降噪源）
# -----------------------------------------------------------------------------
# 两颗 INMP441 共享 SCK / WS，按 LR 时序自动分通道：
#   MIC_A (主，靠近用户口部)：L/R = GND → 在 WS=LOW 半周期输出（左通道）
#   MIC_B (副，远离用户口部)：L/R = VDD → 在 WS=HIGH 半周期输出（右通道）
# 一根 SD 线即可同时承载左右两通道（INMP441 三态输出，互不干扰）。
# 软件层在 ESP-IDF I2S 中按立体声 32-bit 读，奇数样本 = MIC_A，偶数 = MIC_B。
# 差分降噪算法：signal = MIC_A - α × MIC_B（详见 firmware/audio_denoise.md）。
# -----------------------------------------------------------------------------
I2S_SD  = Net("I2S_SD")
I2S_WS  = Net("I2S_WS")
I2S_SCK = Net("I2S_SCK")
MCU["IO2"]  += I2S_SD
MCU["IO41"] += I2S_WS
MCU["IO42"] += I2S_SCK

# 主麦：L/R = GND → 左通道
MIC_A = INMP441(ref="U3")
MIC_A["VDD"] += V3V3
MIC_A["GND"] += GND
MIC_A["L/R"] += GND
MIC_A["SD"]  += I2S_SD
MIC_A["WS"]  += I2S_WS
MIC_A["SCK"] += I2S_SCK

# 副麦：L/R = VDD → 右通道（共用 SD/WS/SCK）
MIC_B = INMP441(ref="U3B")
MIC_B["VDD"] += V3V3
MIC_B["GND"] += GND
MIC_B["L/R"] += V3V3
MIC_B["SD"]  += I2S_SD
MIC_B["WS"]  += I2S_WS
MIC_B["SCK"] += I2S_SCK


# ---------------------------------------------------------------------------
# 10. microSD（SPI 模式）
# ---------------------------------------------------------------------------
SD = SD_CARD(ref="U7")
SD["VDD"] += V3V3
SD["VSS"] += GND

SD_CS   = Net("SD_CS")
SD_SCK  = Net("SD_SCK")
SD_MISO = Net("SD_MISO")
SD_MOSI = Net("SD_MOSI")

SD["DAT3_CS"] += SD_CS;   MCU["IO39"] += SD_CS
SD["CLK"]     += SD_SCK;  MCU["IO40"] += SD_SCK
SD["DAT0_DO"] += SD_MISO; MCU["IO47"] += SD_MISO
SD["CMD_DI"]  += SD_MOSI; MCU["IO48"] += SD_MOSI

# DAT1 / DAT2 在 SPI 模式下需 10kΩ 上拉，避免直接接电源被 ERC 警告
R_SD_PU = Part(lib=None, name="R", value="10k",
               footprint="Resistor_SMD:R_0402_1005Metric",
               dest=TEMPLATE, tool=SKIDL)
R_SD_PU.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
                 Pin(num="2", func=Pin.types.PASSIVE))
R_SD1 = R_SD_PU(ref="R8");  R_SD1[1] += V3V3; R_SD1[2] += SD["DAT1"]
R_SD2 = R_SD_PU(ref="R9");  R_SD2[1] += V3V3; R_SD2[2] += SD["DAT2"]
NC(SD["CD"])                       # 卡检测可选不接


# ---------------------------------------------------------------------------
# 11. WS2812B 灯环（16 颗，串接）
# ---------------------------------------------------------------------------
LED_RING_DIN = Net("LED_RING_DIN")
MCU["IO38"] += LED_RING_DIN

# 灯环电源开关：NMOS 低端切换 GND（更简单）这里直接用 5V 负载开关
M_LED = AO3400(ref="Q1")
LED_PWR_EN = Net("LED_PWR_EN")
MCU["IO1"] += LED_PWR_EN          # IO1 备用 GPIO，用作灯环使能
M_LED["G"] += LED_PWR_EN
M_LED["S"] += GND
LED_RING_GND = Net("LED_RING_GND")
LED_RING_GND.drive = Pin.drives.POWER
M_LED["D"] += LED_RING_GND

prev_dout = LED_RING_DIN
for i in range(1, 17):
    led = WS2812B(ref=f"D{i}")
    led["VDD"]  += VOUT5
    led["GND"]  += LED_RING_GND
    led["DIN"]  += prev_dout
    if i < 16:
        nxt = Net(f"LED_D{i}_OUT")
        led["DOUT"] += nxt
        prev_dout = nxt
    else:
        NC(led["DOUT"])            # 灯环末端悬空


# ---------------------------------------------------------------------------
# 12. 状态 LED
# ---------------------------------------------------------------------------
LED1 = LED_0805(ref="LED_PWR")
R_LED = Part(lib=None, name="R", value="1k",
             footprint="Resistor_SMD:R_0402_1005Metric", dest=TEMPLATE, tool=SKIDL)
R_LED.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
               Pin(num="2", func=Pin.types.PASSIVE))
RLED = R_LED(ref="R5")
LED1["A"] += V3V3
LED1["K"] += RLED[1]
RLED[2]   += LED_PWR_NET


# ---------------------------------------------------------------------------
# 13. 按键 (BOOT + USER)
# ---------------------------------------------------------------------------
SW_BOOT = TACT_SW(ref="SW1")
SW_USER = TACT_SW(ref="SW2")

R_BTN = Part(lib=None, name="R", value="10k",
             footprint="Resistor_SMD:R_0402_1005Metric", dest=TEMPLATE, tool=SKIDL)
R_BTN.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
               Pin(num="2", func=Pin.types.PASSIVE))

# BOOT (IO0): 按下接 GND，10k 上拉
RBOOT = R_BTN(ref="R6")
RBOOT[1] += V3V3
RBOOT[2] += MCU["IO0"]
SW_BOOT[1] += MCU["IO0"]
SW_BOOT[2] += MCU["IO0"]
SW_BOOT[3] += GND
SW_BOOT[4] += GND

# USER (IO14)
RUSER = R_BTN(ref="R7")
RUSER[1] += V3V3
RUSER[2] += MCU["IO14"]
SW_USER[1] += MCU["IO14"]
SW_USER[2] += MCU["IO14"]
SW_USER[3] += GND
SW_USER[4] += GND


# ---------------------------------------------------------------------------
# 13.5 散热温度采集：ADS1115 + 3 颗 NTC（挂在已有 I2C 总线上）
# -----------------------------------------------------------------------------
# 方案：ADS1115（4ch 16-bit I2C ADC，地址 0x48）通过 I2C0 与 MCU 通信。
# 3 颗 NTC 10K B3950 分别贴在：
#   NTC_BAT —— 电池正极极耳（监测电池温度）
#   NTC_PMU —— IP5306 顶面（监测充放电芯片温度）
#   NTC_MCU —— ESP32-S3 模组旁边（监测主控温度，间接代表皮肤侧温度）
# 接法：V3V3 ─ 10 kΩ ─┬── ADS1115 AIN_x
#                      └── NTC ── GND
# 25 ℃ → 1.65 V（半桥）；ADS1115 PGA = ±4.096 V，分辨率 ≈ 0.125 mV ≈ 0.05 ℃。
# 这套方案不占用任何额外 GPIO，仅复用 I2C0。
# -----------------------------------------------------------------------------
ADC_T = ADS1115(ref="U12")
ADC_T["VDD"]   += V3V3
ADC_T["GND"]   += GND
ADC_T["SDA"]   += I2C[0]
ADC_T["SCL"]   += I2C[1]
ADC_T["ADDR"]  += GND          # 地址 = 0x48
NC(ADC_T["ALERT"])             # 不使用阈值告警

R_NTC_PU = Part(lib=None, name="R", value="10k_1%",
                footprint="Resistor_SMD:R_0402_1005Metric",
                dest=TEMPLATE, tool=SKIDL)
R_NTC_PU.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
                  Pin(num="2", func=Pin.types.PASSIVE))

NTC_NODES = []
for i, (label, ain_pin) in enumerate(
        (("NTC_BAT", "AIN0"), ("NTC_PMU", "AIN1"), ("NTC_MCU", "AIN2"))):
    ntc      = NTC_10K(ref=f"RT{i + 1}")
    pull_up  = R_NTC_PU(ref=f"R{20 + i}")
    node     = Net(label)
    NTC_NODES.append(node)
    pull_up[1] += V3V3
    pull_up[2] += node
    ntc[1]     += node
    ntc[2]     += GND
    ADC_T[ain_pin] += node

NC(ADC_T["AIN3"])              # 第 4 通道留作扩展（光照传感器等）


# ---------------------------------------------------------------------------
# 13.6 显式标记未使用引脚为 NC（消除 ERC 噪声）
# ---------------------------------------------------------------------------
NC(J_USB["A8"], J_USB["B8"])
NC(PMIC["LIGHT"], PMIC["BASE"])
NC(FUEL["ALERT"])
NC(MCU["IO3"])                  # strapping 引脚不外接
NC(MCU["IO35"], MCU["IO36"], MCU["IO37"])   # 模组内部 PSRAM 占用
NC(MCU["RXD0"], MCU["TXD0"])    # 调试串口可选不接


# ---------------------------------------------------------------------------
# 14. 去耦电容 — 每个 IC 一颗 100 nF，电源轨上额外大容量
# ---------------------------------------------------------------------------
def add_cap(value: str, foot: str, ref: str, p1, p2):
    c = Part(lib=None, name="C", value=value, footprint=foot,
             dest=TEMPLATE, tool=SKIDL)
    c.add_pins(Pin(num="1", func=Pin.types.PASSIVE),
               Pin(num="2", func=Pin.types.PASSIVE))
    inst = c(ref=ref)
    inst[1] += p1
    inst[2] += p2
    return inst


cap_idx = 10
def _next_cap_ref():
    global cap_idx
    cap_idx += 1
    return f"C{cap_idx}"

# 主电源储能/滤波
add_cap("10uF",  "Capacitor_SMD:C_0805_2012Metric", "C1",  VBUS,  GND)
add_cap("100uF", "Capacitor_SMD:C_Elec_6.3x5.4",   "C2",  VBAT,  GND)
add_cap("220uF", "Capacitor_SMD:C_Elec_6.3x5.4",   "C3",  VOUT5, GND)
add_cap("22uF",  "Capacitor_SMD:C_0805_2012Metric", "C4",  V3V3,  GND)
add_cap("22uF",  "Capacitor_SMD:C_0805_2012Metric", "C5",  V3V3,  GND)

# 各 IC 旁路
for net, ic_ref in [
    (V3V3, "MCU"), (V3V3, "CAM"), (V3V3, "MIC"),
    (V3V3, "FUEL"), (VOUT5, "LDO_IN"), (V3V3, "LDO_OUT"),
    (V3V3, "ADC_T"),                # ADS1115 旁路
]:
    add_cap("100nF", "Capacitor_SMD:C_0402_1005Metric",
            _next_cap_ref(), net, GND)


# ---------------------------------------------------------------------------
# 15. 输出 netlist + ERC
# ---------------------------------------------------------------------------
OUT_DIR = ROOT / "output"
OUT_DIR.mkdir(parents=True, exist_ok=True)

ERC()

# Netlist/XML 输出切换到 KICAD 工具（SKIDL 工具仅支持 ERC，没有 netlist 输出）
set_default_tool(KICAD)
generate_netlist(file_=str(OUT_DIR / "instafreeheart.net"))
generate_xml(file_=str(OUT_DIR / "instafreeheart.xml"))

# SKiDL 在工作目录自动生成 schematic.erc / .log / _sklib.py，把它们挪到 output 目录
import shutil as _shutil
from pathlib import Path as _P
for _name in ("schematic.erc", "schematic.log", "schematic_sklib.py"):
    _src = _P.cwd() / _name
    if _src.exists():
        _dst = OUT_DIR / _name
        if _dst.exists():
            _dst.unlink()
        _shutil.move(str(_src), str(_dst))

print(f"\n[OK] netlist + xml + erc/log written to {OUT_DIR}")
