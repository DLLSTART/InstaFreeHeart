# InstaFreeHeart · 固件 (ESP-IDF v5.x)

> 该目录暂时只放散热守卫 demo（`thermal_guard.c`）；后续会陆续补充
> `app_main`、`camera_task`、`ai_task`、`led_ring_task`、`mic_task`、
> `power_manager` 等任务模块。

## 目录约定

```
firmware/
├── README.md                    ← 本文件
├── thermal_guard.c              ← 散热守卫（NTC × 3 + 4 阈值降功耗）
├── thermal_guard.h              (建议生成)
└── (后续) main/                 ← ESP-IDF 工程入口
    components/
        thermal_guard/
        camera_task/
        ai_task/
        ...
```

## thermal_guard.c 集成步骤

### 1. 拷贝到组件目录

```bash
mkdir -p components/thermal_guard
cp firmware/thermal_guard.c components/thermal_guard/
```

`components/thermal_guard/CMakeLists.txt`:

```cmake
idf_component_register(
    SRCS         "thermal_guard.c"
    INCLUDE_DIRS "."
    REQUIRES     driver freertos esp_event log
)
```

### 2. 在 `app_main()` 中初始化

```c
#include "driver/i2c_master.h"
#include "thermal_guard.h"

void app_main(void) {
    /* 1) 初始化共享 I2C 总线（OV5640 SCCB / CW2015 / ADS1115 共用）         */
    i2c_master_bus_config_t bus_cfg = {
        .i2c_port = I2C_NUM_0,
        .sda_io_num = 4,
        .scl_io_num = 5,
        .clk_source = I2C_CLK_SRC_DEFAULT,
        .glitch_ignore_cnt = 7,
        .flags.enable_internal_pullup = false,  // 已外部 4.7K 上拉
    };
    i2c_master_bus_handle_t bus;
    ESP_ERROR_CHECK(i2c_new_master_bus(&bus_cfg, &bus));

    /* 2) 启动散热守卫（自动启动后台 1 Hz 任务）                              */
    ESP_ERROR_CHECK(thermal_guard_init(bus));

    /* 3) 其它任务通过 thermal_allows() 协作                                  */
    while (1) {
        if (thermal_allows(BIT_ALLOW_AI)) {
            run_ai_inference();
        }
        vTaskDelay(pdMS_TO_TICKS(50));
    }
}
```

### 3. 看日志

正常运行（25 ℃）：

```
I (1042) thermal: T_BAT=26.3  T_PMU=27.1  T_MCU=29.5  state=OK
I (2043) thermal: T_BAT=26.4  T_PMU=27.5  T_MCU=29.8  state=OK
```

进入 WARM（>38 ℃）：

```
W (87654) thermal: T_BAT=37.1  T_PMU=38.4  T_MCU=37.9  →  OK → WARM
I (88654) thermal: T_BAT=37.2  T_PMU=38.6  T_MCU=38.0  state=WARM
```

紧急关机（>45 ℃）：

```
W (123456) thermal: T_BAT=44.0  T_PMU=46.2  T_MCU=44.8  →  CRIT → PANIC
E (123456) thermal: PANIC! Entering deep-sleep to protect user.
```

## 阈值（与 `mechanical/thermal.md` 一致）

| 状态 | 触发温度 | 允许子系统 |
|------|---------|-----------|
| OK | T < 38 ℃ | 全部允许 |
| WARM | T ≥ 38 ℃ | 灯环亮度减半，充电限到 0.5 C |
| HOT | T ≥ 41 ℃ | 暂停 AI、WiFi 仅 BLE |
| CRIT | T ≥ 43 ℃ | 仅充电不输出，禁用摄像头 |
| PANIC | T ≥ 45 ℃ | 紧急关机（deep-sleep） |

降级触发增加 1.5 ℃ 滞回，避免在阈值附近抖动。

## NTC 校准

NTC 默认参数：MF52E 10 kΩ B25/50 = 3950，± 1%。
若改用其它型号（B 值不同），修改 `thermal_guard.c` 顶部宏：

```c
#define NTC_R0      10000.0f     // 25 ℃ 阻值
#define NTC_T0      298.15f      // 25 ℃ 开尔文
#define NTC_BETA    3950.0f      // β 值
#define NTC_PULLUP  10000.0f     // 上拉电阻
```

## 烧录 / 调试

```bash
idf.py set-target esp32s3
idf.py menuconfig            # 选 PSRAM = Octal, Flash = 16MB
idf.py build flash monitor
```

预期监控输出每秒一行 `state=OK/WARM/HOT/CRIT/PANIC`，状态切换时
另有 `WARN` 行打印温度详细值。
