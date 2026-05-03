/**
 * @file    thermal_guard.c
 * @brief   InstaFreeHeart · 散热守卫固件 demo（ESP-IDF v5.x）
 *
 * 功能：
 *   - 通过外挂 ADS1115（I²C 地址 0x48）每秒采样 3 颗 NTC 10K B3950
 *     T_BAT (AIN0)：电池正极极耳
 *     T_PMU (AIN1)：IP5306 顶面
 *     T_MCU (AIN2)：ESP32-S3 模组旁（皮肤侧代理温度）
 *   - 4 阈值降功耗策略：
 *       T < 38 ℃ → THERMAL_OK     全功率
 *       T ≥ 38 ℃ → THERMAL_WARM   降流 50%、灯环亮度减半
 *       T ≥ 41 ℃ → THERMAL_HOT    暂停 AI、WiFi 仅保留 BLE
 *       T ≥ 43 ℃ → THERMAL_CRIT   仅充电不输出，禁用摄像头
 *       T ≥ 45 ℃ → THERMAL_PANIC  紧急关机
 *   - 通过 FreeRTOS event group 与其它任务（AI、Camera、LED、PMIC）协调。
 *
 * 编译：放入 components/thermal_guard/ 或 main/ 即可，CMakeLists 见末尾注释。
 *
 * License: MIT
 */
#include <math.h>
#include <stdio.h>
#include <string.h>

#include "driver/i2c_master.h"
#include "esp_err.h"
#include "esp_log.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"

static const char *TAG = "thermal";

/* -------------------------------------------------------------------------- */
/* 1. 硬件参数（与 hardware/schematic.py + parameters.scad 保持一致）         */
/* -------------------------------------------------------------------------- */
#define I2C_SDA_GPIO        4         /* IO4  — 与 OV5640 SCCB / CW2015 共用 */
#define I2C_SCL_GPIO        5
#define I2C_FREQ_HZ         400000    /* 400 kHz Fast Mode                   */

#define ADS1115_ADDR        0x48      /* ADDR 接 GND                         */

/* NTC: MF52E 10K @25 ℃, B25/50 = 3950, ±1%                                  */
#define NTC_R0              10000.0f  /* @25 ℃                              */
#define NTC_T0              298.15f   /* 25 ℃ in Kelvin                     */
#define NTC_BETA            3950.0f
#define NTC_PULLUP          10000.0f  /* 上拉电阻 10 kΩ                      */

#define ADS1115_VREF        4.096f    /* PGA = ±4.096 V → LSB = 125 µV       */
#define ADS1115_FS          (1L << 15)

/* -------------------------------------------------------------------------- */
/* 2. 散热阈值（℃）— 与 mechanical/thermal.md 一致                          */
/* -------------------------------------------------------------------------- */
#define T_OK_HI             38.0f
#define T_WARM_HI           41.0f
#define T_HOT_HI            43.0f
#define T_CRIT_HI           45.0f
#define T_HYSTERESIS        1.5f      /* 防抖：降级阈值要再低 1.5 ℃才升级    */

/* -------------------------------------------------------------------------- */
/* 3. 状态机                                                                  */
/* -------------------------------------------------------------------------- */
typedef enum {
    THERMAL_OK = 0,    /* 全功率                                               */
    THERMAL_WARM,      /* 降流 50%、灯环亮度减半                              */
    THERMAL_HOT,       /* 暂停 AI、WiFi 仅 BLE                                 */
    THERMAL_CRIT,      /* 仅充电不输出，禁摄像头                              */
    THERMAL_PANIC,     /* 紧急关机                                             */
} thermal_level_t;

static const char *level_name[] = {
    "OK", "WARM", "HOT", "CRIT", "PANIC"
};

/* 与外部任务协调的事件 bit                                                   */
#define BIT_ALLOW_AI        BIT0
#define BIT_ALLOW_WIFI_TX   BIT1
#define BIT_ALLOW_CAMERA    BIT2
#define BIT_ALLOW_USB_OUT   BIT3
#define BIT_ALLOW_LED_FULL  BIT4

static EventGroupHandle_t s_thermal_evt;
static thermal_level_t    s_level    = THERMAL_OK;
static i2c_master_dev_handle_t s_ads = NULL;

/* -------------------------------------------------------------------------- */
/* 4. ADS1115 寄存器                                                          */
/* -------------------------------------------------------------------------- */
#define ADS_REG_CONV   0x00
#define ADS_REG_CFG    0x01

/* config: OS=1 single-shot, MUX=AINx, PGA=±4.096V (=001), MODE=single-shot,
 *         DR=128SPS, COMP_QUE=disable                                        */
static uint16_t ads_cfg_for_channel(uint8_t ch)
{
    uint16_t cfg = 0x8000          /* OS = 1 (start)                          */
                 | ((4 + ch) << 12)/* MUX: AIN_x vs GND                       */
                 | (0x1   <<  9)   /* PGA = ±4.096 V                          */
                 | (0x1   <<  8)   /* MODE = single-shot                      */
                 | (0x4   <<  5)   /* DR = 128 SPS                            */
                 | 0x3;            /* COMP_QUE = disable                      */
    return cfg;
}

static esp_err_t ads_write_cfg(uint16_t cfg)
{
    uint8_t buf[3] = { ADS_REG_CFG, cfg >> 8, cfg & 0xFF };
    return i2c_master_transmit(s_ads, buf, sizeof(buf), pdMS_TO_TICKS(50));
}

static esp_err_t ads_read_conv(int16_t *out)
{
    uint8_t reg = ADS_REG_CONV;
    uint8_t rx[2];
    esp_err_t err = i2c_master_transmit_receive(
        s_ads, &reg, 1, rx, 2, pdMS_TO_TICKS(50));
    if (err == ESP_OK) {
        *out = (int16_t)((rx[0] << 8) | rx[1]);
    }
    return err;
}

static esp_err_t ads_read_channel_mv(uint8_t ch, float *mv)
{
    ESP_RETURN_ON_ERROR(ads_write_cfg(ads_cfg_for_channel(ch)),
                         TAG, "ads_write_cfg ch=%u", ch);
    /* 128 SPS → 一次 ~7.8 ms，给够 12 ms 余量                                */
    vTaskDelay(pdMS_TO_TICKS(12));
    int16_t raw;
    ESP_RETURN_ON_ERROR(ads_read_conv(&raw), TAG, "ads_read_conv");
    *mv = (float)raw * (ADS1115_VREF * 1000.0f) / (float)ADS1115_FS;
    return ESP_OK;
}

/* -------------------------------------------------------------------------- */
/* 5. NTC 阻值 → 温度                                                        */
/* -------------------------------------------------------------------------- */
/* 接法：V3V3(3.3V) ── R_pullup(10K) ──┬── ADC ── R_ntc ── GND               */
static float ntc_voltage_to_celsius(float v_adc_mv)
{
    /* 注意：V3V3 实际上接的是 LDO 输出，3.3 V ± 1%。这里直接用 3300 mV。     */
    const float vcc_mv = 3300.0f;
    if (v_adc_mv < 1.0f || v_adc_mv > vcc_mv - 1.0f) {
        return NAN;       /* 短路或开路                                      */
    }
    /* R_ntc = R_pu × V_ntc / (V_cc - V_ntc)                                   */
    float r_ntc = NTC_PULLUP * v_adc_mv / (vcc_mv - v_adc_mv);
    /* β 方程：1/T = 1/T0 + (1/β) × ln(R/R0)                                   */
    float inv_T = 1.0f / NTC_T0
                  + logf(r_ntc / NTC_R0) / NTC_BETA;
    return 1.0f / inv_T - 273.15f;
}

/* -------------------------------------------------------------------------- */
/* 6. 状态机 + 协调                                                           */
/* -------------------------------------------------------------------------- */
static thermal_level_t classify(float t_max, thermal_level_t prev)
{
    /* 升级（超阈）立即触发；降级（恢复）需要回退 T_HYSTERESIS                 */
    float lo = T_HYSTERESIS;
    switch (prev) {
        case THERMAL_PANIC: if (t_max > T_CRIT_HI - lo) return THERMAL_PANIC; break;
        case THERMAL_CRIT:  if (t_max > T_HOT_HI  - lo) return THERMAL_CRIT;  break;
        case THERMAL_HOT:   if (t_max > T_WARM_HI - lo) return THERMAL_HOT;   break;
        case THERMAL_WARM:  if (t_max > T_OK_HI   - lo) return THERMAL_WARM;  break;
        default: break;
    }
    if (t_max >= T_CRIT_HI) return THERMAL_PANIC;
    if (t_max >= T_HOT_HI)  return THERMAL_CRIT;
    if (t_max >= T_WARM_HI) return THERMAL_HOT;
    if (t_max >= T_OK_HI)   return THERMAL_WARM;
    return THERMAL_OK;
}

static void apply_level(thermal_level_t lv)
{
    EventBits_t allow = 0;
    switch (lv) {
        case THERMAL_OK:
            allow = BIT_ALLOW_AI | BIT_ALLOW_WIFI_TX | BIT_ALLOW_CAMERA
                    | BIT_ALLOW_USB_OUT | BIT_ALLOW_LED_FULL;
            break;
        case THERMAL_WARM:
            /* 降流 50% 由 PMIC 任务自行根据 LED_FULL 缺位降亮度              */
            allow = BIT_ALLOW_AI | BIT_ALLOW_WIFI_TX | BIT_ALLOW_CAMERA
                    | BIT_ALLOW_USB_OUT;
            break;
        case THERMAL_HOT:
            /* 不允许 AI 推理 + 不允许 WiFi 高功耗 TX                          */
            allow = BIT_ALLOW_CAMERA | BIT_ALLOW_USB_OUT;
            break;
        case THERMAL_CRIT:
            /* 仅允许充电；禁止 USB-out / Camera / AI                          */
            allow = 0;
            break;
        case THERMAL_PANIC:
            /* 全部任务停止；下游应进入 deep-sleep 或软关机                    */
            allow = 0;
            break;
    }
    /* 一次性原子更新，避免任务之间错乱                                       */
    xEventGroupClearBits(s_thermal_evt, 0xFFFFFF);
    xEventGroupSetBits(s_thermal_evt, allow);
}

/* 给其它任务的查询 API。例：                                                 */
/*   if (thermal_allows(BIT_ALLOW_AI)) run_ai_one_step();                    */
bool thermal_allows(EventBits_t bit)
{
    return (xEventGroupGetBits(s_thermal_evt) & bit) == bit;
}

thermal_level_t thermal_get_level(void) { return s_level; }

/* -------------------------------------------------------------------------- */
/* 7. 后台采样任务（1 Hz）                                                    */
/* -------------------------------------------------------------------------- */
static void thermal_task(void *arg)
{
    const TickType_t period = pdMS_TO_TICKS(1000);
    TickType_t last = xTaskGetTickCount();
    float t[3];

    while (1) {
        for (int ch = 0; ch < 3; ++ch) {
            float mv = 0;
            if (ads_read_channel_mv(ch, &mv) != ESP_OK) {
                t[ch] = NAN;
                continue;
            }
            t[ch] = ntc_voltage_to_celsius(mv);
        }
        float t_max = 0;
        for (int i = 0; i < 3; ++i) {
            if (!isnan(t[i]) && t[i] > t_max) t_max = t[i];
        }

        thermal_level_t new_level = classify(t_max, s_level);
        if (new_level != s_level) {
            ESP_LOGW(TAG,
                "T_BAT=%.2f ℃  T_PMU=%.2f ℃  T_MCU=%.2f ℃  →  %s → %s",
                t[0], t[1], t[2], level_name[s_level], level_name[new_level]);
            s_level = new_level;
            apply_level(s_level);

            if (s_level == THERMAL_PANIC) {
                ESP_LOGE(TAG, "PANIC! Entering deep-sleep to protect user.");
                /* 在真实固件中：保存日志、关 LED、进入 deep-sleep            */
                /* esp_deep_sleep_start();                                     */
            }
        } else {
            ESP_LOGI(TAG,
                "T_BAT=%.1f  T_PMU=%.1f  T_MCU=%.1f  state=%s",
                t[0], t[1], t[2], level_name[s_level]);
        }
        vTaskDelayUntil(&last, period);
    }
}

/* -------------------------------------------------------------------------- */
/* 8. 初始化                                                                  */
/* -------------------------------------------------------------------------- */
esp_err_t thermal_guard_init(i2c_master_bus_handle_t bus)
{
    s_thermal_evt = xEventGroupCreate();
    if (!s_thermal_evt) return ESP_ERR_NO_MEM;
    /* 默认全允许（OK 状态）                                                   */
    xEventGroupSetBits(s_thermal_evt,
        BIT_ALLOW_AI | BIT_ALLOW_WIFI_TX | BIT_ALLOW_CAMERA
        | BIT_ALLOW_USB_OUT | BIT_ALLOW_LED_FULL);

    i2c_device_config_t dev = {
        .dev_addr_length = I2C_ADDR_BIT_LEN_7,
        .device_address  = ADS1115_ADDR,
        .scl_speed_hz    = I2C_FREQ_HZ,
    };
    ESP_RETURN_ON_ERROR(
        i2c_master_bus_add_device(bus, &dev, &s_ads),
        TAG, "i2c add ADS1115");

    BaseType_t ok = xTaskCreatePinnedToCore(
        thermal_task, "thermal", 4096, NULL, /*prio*/ 5, NULL, /*core*/ 1);
    return ok == pdPASS ? ESP_OK : ESP_FAIL;
}

/* ==========================================================================
 * 使用示例（在 app_main 中）：
 *
 *   i2c_master_bus_handle_t bus;          // 假设已创建
 *   ESP_ERROR_CHECK(thermal_guard_init(bus));
 *
 *   while (1) {
 *       if (thermal_allows(BIT_ALLOW_AI)) {
 *           ai_inference_step();
 *       } else {
 *           vTaskDelay(pdMS_TO_TICKS(100));
 *       }
 *   }
 *
 * components/thermal_guard/CMakeLists.txt:
 *
 *   idf_component_register(
 *       SRCS    "thermal_guard.c"
 *       INCLUDE_DIRS "."
 *       REQUIRES driver freertos esp_event log)
 *
 * ==========================================================================*/
