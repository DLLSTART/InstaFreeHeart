# InstaFreeHeart 引脚分配

> 主控：ESP32-S3-WROOM-1-N16R8（44-pin SMD 模组）
> 模组内部已占用 GPIO 33~37（Octal PSRAM/Flash），对外不可用。
> Strapping pin（避免做普通 IO）：GPIO0, 3, 45, 46
> USB-OTG 内部走 GPIO19/20（如使用原生 USB）。

## 引脚分配表

| GPIO | 方向 | 连接 | 子系统 | 说明 |
|-----:|------|------|--------|------|
| IO0  | I    | SW1 (BOOT) + 10 kΩ 上拉 | 系统 | 兼下载启动 |
| IO1  | —    | NC | — | 预留 |
| IO2  | I    | INMP441 ×2 共享 SD（双麦立体声 LR 时序） | 麦克风 I²S | 主/副麦共用一根 SD 线，按 LR 通道分时复用 |
| IO3  | —    | NC（strapping，建议悬空或外部上拉） | — | 慎用 |
| IO4  | I/O  | I²C SDA (CW2015 + OV5640 SCCB + ADS1115 共用) | I²C0 | 4.7 kΩ 上拉到 3V3 |
| IO5  | O    | I²C SCL (CW2015 + OV5640 SCCB + ADS1115 共用) | I²C0 | 4.7 kΩ 上拉到 3V3 |
| IO6  | I    | OV5640 VSYNC | 摄像头 DVP | |
| IO7  | I    | OV5640 HREF | 摄像头 DVP | |
| IO8  | I    | OV5640 D2 | 摄像头 DVP | |
| IO9  | I    | OV5640 D1 | 摄像头 DVP | |
| IO10 | I    | OV5640 D3 | 摄像头 DVP | |
| IO11 | I    | OV5640 D0 | 摄像头 DVP | |
| IO12 | I    | OV5640 D4 | 摄像头 DVP | |
| IO13 | I    | OV5640 PCLK | 摄像头 DVP | |
| IO14 | I    | SW2 (USER) | 按键 | 模式切换 / 唤醒 |
| IO15 | O    | OV5640 XCLK | 摄像头 DVP | LEDC PWM 20 MHz |
| IO16 | I    | OV5640 D7 | 摄像头 DVP | |
| IO17 | I    | OV5640 D6 | 摄像头 DVP | |
| IO18 | I    | OV5640 D5 | 摄像头 DVP | |
| IO19 | I/O  | USB-C D- | USB-OTG | 原生 USB Serial/JTAG |
| IO20 | I/O  | USB-C D+ | USB-OTG | 原生 USB Serial/JTAG |
| IO21 | O    | OV5640 PWDN | 摄像头 DVP | 高电平断电省流 |
| IO38 | O    | WS2812B DIN | 灯环 | RMT/SPI 驱动 |
| IO39 | O    | TF_CS | microSD SPI | CS |
| IO40 | O    | TF_SCK | microSD SPI | |
| IO41 | O    | INMP441 WS (LRCLK) | 麦克风 I²S | |
| IO42 | O    | INMP441 SCK (BCLK) | 麦克风 I²S | |
| IO43 | I/O  | UART0 TX (调试串口) | 调试 | 默认 U0TXD |
| IO44 | I/O  | UART0 RX (调试串口) | 调试 | 默认 U0RXD |
| IO45 | I    | IP5306 KEY (开机/状态检测) | 电源 | strapping，外部需弱上拉 |
| IO46 | O    | LED_PWR (状态绿灯) | 状态 | strapping，仅做 OUT 上电后 |
| IO47 | I    | TF_MISO | microSD SPI | |
| IO48 | O    | TF_MOSI | microSD SPI | |

## 总线占用一览

- **DVP（摄像头并行总线）**：IO6,7,8,9,10,11,12,13,15,16,17,18,21（含 XCLK/PWDN）
- **I²C0**：IO4(SDA) / IO5(SCL) — 挂载：
  - OV5640 SCCB（地址 0x3C）
  - CW2015（地址 0xC4 / 0x62 — 1S 锂电库仑计）
  - ADS1115（地址 0x48 — 散热三 NTC 温度采集，AIN0=电池 / AIN1=PMU / AIN2=MCU）
- **I²S0**：IO2(SD) / IO41(WS) / IO42(SCK) — 双 INMP441 立体声（MIC_A=L 通道, MIC_B=R 通道，共用 SD 线）
- **SPI3 (HSPI)**：IO39(CS) / IO40(SCK) / IO47(MISO) / IO48(MOSI) → microSD
- **RMT**：IO38 → WS2812 DIN
- **USB-OTG**：IO19(D-) / IO20(D+) → USB-C 数据
- **UART0**：IO43(TX) / IO44(RX) → 调试

## 已知冲突 / 注意事项

1. **I²C0 三机共用**：OV5640 SCCB (0x3C) + CW2015 (0x62) + ADS1115 (0x48)，地址互不冲突。
2. **IO45/46 是 strapping pin**：上电时电平会影响 boot mode。IO45 接 IP5306 KEY 用「OD + 弱上拉」；IO46 仅做输出（默认 LOW，不影响 boot）。
3. **PSRAM Octal 占用 IO33~37**：模组内部连接，PCB 上不要外接这些网络。
4. **摄像头与 microSD 不复用 IO**：刻意避免 ESP32-CAM 老板上 SDIO 与 DVP 抢 IO 的问题。
5. **DVP 数据 D0~D7 使用 ESP32-S3 GPIO 矩阵**：可任意映射，编号顺序在 `esp_camera_config_t` 中调整即可。
6. **散热温度采集走外部 ADS1115（不占 GPIO）**：ESP32-S3 的 ADC1（IO1~10）几乎被 I2C/I2S/DVP 占满，且 ADC2（IO11~20）在 WiFi 工作时被禁用。把 3 颗 NTC 挂到 ADS1115 后清爽集成，详见 [`../mechanical/thermal.md`](../mechanical/thermal.md)。
