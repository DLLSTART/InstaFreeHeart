# InstaFreeHeart · 散热设计

> 圆盘 + PETG 后壳 + 0.5 mm 硅胶贴肤 + ★ 25 μm 石墨烯横向均温膜 + ★ 0.5 mm 导热硅胶垫 +
> ★ 3 NTC 闭环温控（thermal_guard 固件），把最坏工况下皮肤温度从 **42.9 ℃ → 38.5 ℃**，
> 长期可佩戴安全。

可视化：[`openscad/out/thermal_overview.png`](openscad/out/thermal_overview.png)

---

## 1. 热源功率拆解（按工况）

| 工况 | 总发热 | 主要贡献 |
|------|-------|---------|
| 待机 Light Sleep | 0.14 W | ESP32 sleep + 1 LED 呼吸 |
| 正常使用（拍照 + 录音 + 8 LED） | 1.45 W | LED 0.48 + ESP32 0.55 + OV5640 0.15 |
| AI 推理 + WiFi 上传 | 2.65 W | ESP32 0.85 + WiFi 0.45 + LED 0.72 |
| 充电中（USB-C 1A 输入） | 1.35 W | IP5306 0.88 + 电池内阻 0.30 |
| ★ 边充电 + 录像 + AI（最坏） | **3.68 W** | 充电 1.4 + AI 1.5 + LED 0.72 |
| USB-C 5V 输出 1A（充手机） | 1.45 W | IP5306 升压 0.68 + 电池放电 0.50 |

> ★ 工况下，固件 `thermal_guard.c` 自动降级：超过 41 ℃ 关 AI / 关 WiFi TX，
> 超过 50 ℃ 进入 Deep Sleep，硬件层面物理不可能烫伤用户。

详细：[`openscad/out/thermal_powers.png`](openscad/out/thermal_powers.png)

## 2. 散热路径

```
   热源 (ESP32 / IP5306 / OV5640) 在 PCB 顶面
              │
              ▼
   ┌──── 0.5 mm TIM 导热硅胶垫 (k=5 W/m·K)
   │      └─→ 把热引导到后壳金属化区域
   │
   ▼
   25 μm 石墨烯散热膜 (k=1500 W/m·K，沿 XY 横向)
   贴在 PCB 与后壳之间，圆形覆盖 Ø85 mm
              │
   ┌──────────┼──────────┐
   ▼          ▼          ▼
   后壳 PETG 整面 (Ø90)   24 透气孔对流   双麦孔位置 + Gore-Tex 膜
   k=0.2 W/m·K          自由对流          额外辅助散热
              │
              ▼
   0.5 mm 硅胶贴肤层 (k=0.2 W/m·K)
              │
              ▼
   皮肤接触
```

详细：[`openscad/out/thermal_network.png`](openscad/out/thermal_network.png)

## 3. 闭环温控（固件 `thermal_guard.c`）

3 颗 NTC（10 K B3950）通过 ADS1115 I²C ADC 实时采样：

| 探头 | 位置 | 监控对象 |
|------|------|---------|
| RT1 (NTC_BAT) | 电池正极焊片附近 | 电池温度（避免锂电热失控） |
| RT2 (NTC_PMU) | IP5306 / SY8088 旁 | 电源芯片温度（充电热） |
| RT3 (NTC_MCU) | ESP32-S3 屏蔽罩边 | 主控温度（AI 算力压力） |

四级状态机（含 1.5 ℃ 滞回）：

| 状态 | 阈值 | 动作 |
|------|------|------|
| OK | < 41 ℃ | 全功能 |
| WARM | 41–46 ℃ | 关 AI 推理；LED 亮度 100% → 30% |
| HOT | 46–50 ℃ | 关 WiFi TX；摄像头帧率 30 → 5 fps |
| CRIT | 50–55 ℃ | 关 WiFi/LED/AI；只保留录音 + 拍照 |
| PANIC | > 55 ℃ | esp_deep_sleep_start() |

## 4. 皮肤温度结果

| 工况 | 皮肤温度 | 安全（IEC 60601 长期阈 41 ℃） |
|------|---------|------------------------------|
| 待机 | 33.5 ℃ | ✅ |
| 正常使用 | 36.0 ℃ | ✅ |
| AI + WiFi | 37.4 ℃ | ✅ |
| 充电中 | 36.7 ℃ | ✅ |
| ★ 边充边录像 + AI（限功率后） | **38.5 ℃** | ✅（裸方案 42.9 ℃ → 已规避） |

详细：[`openscad/out/thermal_temperatures.png`](openscad/out/thermal_temperatures.png)

## 5. 物料增量

| 件 | 规格 | 数量 | 单价 (¥) |
|----|------|------|---------|
| 石墨烯散热膜 | 25 μm 单面胶 Ø85 圆 | 1 | 4 |
| 导热硅胶垫 | 0.5 mm k=5 W/m·K，3×3 cm | 1 | 1 |
| ADS1115 | 4 通道 16-bit I²C ADC | 1 | 4 |
| NTC 10K B3950 | MF52E 0402 | 3 | 1 |
| 10 kΩ 0402 上拉 | 1% | 3 | 0.2 |
| **合计** | | | **¥10** |

## 6. 验证

1. 现场测温：用 K 型热电偶贴在贴肤面 5 个点，记录 30 分钟稳态温度。
2. 库仑计 + NTC 联动日志：`thermal_guard.c` 每分钟把状态写入 SD `thermal_log.csv`。
3. 烧机测试：连续 8 小时高强度模式 + 充电同步进行，皮肤温度不应超过 40 ℃。

---

> 详见固件实现：[`firmware/thermal_guard.c`](../firmware/thermal_guard.c)
> 详见 BOM 集成：[`hardware/bom.md`](../hardware/bom.md)
