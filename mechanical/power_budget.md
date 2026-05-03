# InstaFreeHeart · 功耗预算与续航

> 4000 mAh / 14.8 Wh 电池 + SY8088 Buck 直供 3V3（η=92%）：
> 纯日记 5.3–7.1 天连续，高强度日记 9.8–13 h 连续。
>
> 可视化：[`openscad/out/power_overview.png`](openscad/out/power_overview.png)

---

## 1. 4 种使用模式

| 模式 | 描述 | 平均功率 | 连续续航 |
|------|------|---------|---------|
| Deep Sleep | 仅 RTC + IP5306 静态 + ADS1115 唤醒源 | **2 mW** | **6 月** |
| ★ 纯日记模式 | 1 张/分钟拍照 + 双麦持续录音 + 每小时上传 5 分钟 + 1 LED 呼吸 | **84 mW** | **7.1 天** |
| 高强度日记 | 实时 AI + 实时 WiFi 上传 + 8 LED 全亮 + 持续录像 | **1.13 W** | **13.1 h** |
| USB-C 5V 输出 1A | 给手机充电（IP5306 升压损耗 + 电池放电内阻） | **1.20 W** | **5.2 h** |

完整子系统拆解见 [`openscad/power_preview.py`](openscad/power_preview.py) 中的 `MODES` 字典。

## 2. 电源拓扑（双路供电）

```
                    ┌─ IP5306 升压 (η=88%) ──> 5V VOUT ──> USB-C 5V 输出 / WS2812B 灯环
   BAT 3.7V ────────┤                          (仅充手机 / 灯环时启用)
                    │
                    └─ SY8088 Buck (η=92%) ──> 3V3 ──> ESP32-S3 / OV5640 / 双 INMP441 /
                                                       TF / CW2015 / ADS1115
```

- 平时（无 5V 负载），3V3 走 SY8088，整机平均效率 92%。
- IP5306 仅在 USB-C 输入充电 + 5V 输出工况启用，平时静态损耗 1.85 mW。

## 3. Light Sleep 调度

ESP32-S3 各电源模式典型电流（@ 3.3 V，CPU 240 MHz）：

| 模式 | 电流 | 功率 | 唤醒时间 |
|------|------|------|---------|
| Active (双核满载) | 230 mA | 759 mW | — |
| Modem Sleep (CPU 80 MHz) | 30 mA | 99 mW | 0 µs |
| **Light Sleep (RAM 保持)** | **0.24 mA** | **0.79 mW** | **~250 µs** |
| Deep Sleep (RTC only) | 8 µA | 26 µW | ~10 ms |
| Hibernation | 2.5 µA | 8 µW | ~10 ms (冷启动) |

**纯日记模式调度（每 60 秒周期）**：
```
T=0    s : 拍照 + HDR 融合 + 编码 + AI caption  → 2.0 s active (660 mW)
T=2    s : Light Sleep + 双麦录音 (DMA 自动)
T=12 min : WiFi 上传日志 (5 s active 924 mW，仅每 12 分钟 1 次)
其它       : Light Sleep ≈ 0.79 mW + 双麦 9.2 mW = 10 mW
```

参考实现：[`../firmware/diary_mode.c`](../firmware/diary_mode.c)

## 4. 外设独立电源开关

| 外设 | 待机 | 控制方式 | 引脚 |
|------|------|---------|------|
| OV5640 | 100 mA → 50 µA (PWDN) | IO21 拉高 | IO21 |
| INMP441 ×2 | 1.4 mA → 5 µA | I²S SCK 拉低 | I²S 关闭 |
| WS2812B × 16 | 11 mA 静态 → 0 | NMOS 切 5V | Q1 / IO1 |
| TF 卡 | 30 mA → 0.5 mA | SPI deinit | 软件 |
| WiFi RF | 280 mA → 0 | esp_wifi_stop() | 软件 |
| ADC + NTC | 0.5 mW → 0.2 mW | ADS1115 single-shot | I²C 命令 |

## 5. 验证

1. **库仑计实测**：CW2015 通过 I²C 实时报告剩余容量；启动后每分钟存一次到 SD `power_log_YYYYMMDD.csv`。
2. **NTC 联动**：散热守卫 `thermal_guard.c` 超过 41 ℃ 自动降功耗，间接限制平均功率。
3. **PMU 分析仪**（如 Nordic Power Profiler Kit II）：拆机串入 BAT+ 测电流波形。
