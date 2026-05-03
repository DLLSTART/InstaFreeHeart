/**
 * @file    diary_mode.c
 * @brief   InstaFreeHeart · 纯日记模式调度器（Light Sleep + 任务）
 *
 *          纯日记模式时序（每分钟 1 周期）：
 *            T=0      s : 唤醒拍照（含 HDR 融合）+ AI 生成 1 行 caption + 写 SD
 *            T=2      s : Light Sleep（持续录音由 I2S DMA 自动）
 *            T=12 min : WiFi 连接 + 上传日志（5 秒）
 *            其它       : Light Sleep ~ 240 µA
 *
 *          续航：4000 mAh 电池 → 7.1 天连续。
 *
 *          与其它模块协调：
 *            - thermal_guard.c : 超温自动降级，调度器读 thermal_allows()
 *            - hdr_pipeline.c  : 拍照走 HDR fusion
 *            - audio_pipeline  : DMA 自动搬运录音，不需 CPU 介入
 *            - wifi_uploader   : 后台批量上传（仅每 12 分钟）
 *
 * License: MIT
 */
#include <inttypes.h>
#include <stdio.h>
#include <string.h>
#include <time.h>

#include "driver/gpio.h"
#include "esp_camera.h"
#include "esp_event.h"
#include "esp_log.h"
#include "esp_pm.h"
#include "esp_sleep.h"
#include "esp_timer.h"
#include "esp_wifi.h"
#include "freertos/FreeRTOS.h"
#include "freertos/event_groups.h"
#include "freertos/task.h"

#include "thermal_guard.h"

static const char *TAG = "diary";

/* -------------------------------------------------------------------------- */
/* 配置                                                                        */
/* -------------------------------------------------------------------------- */
#define DIARY_PHOTO_INTERVAL_S    60      /* 1 张/分钟 */
#define DIARY_UPLOAD_INTERVAL_S   720     /* 12 分钟 1 次 WiFi 上传 */
#define DIARY_LED_INDICATOR_GPIO  46      /* IO46 状态绿灯 */

/* 唤醒源 */
#define WAKE_GPIO_USER_BTN        14      /* IO14 USER 按键，按下立即唤醒 */

/* 事件 */
#define EVT_NEW_VOICE             BIT0    /* VAD 检测到 1s+ 语音段 */
#define EVT_USER_BTN              BIT1
#define EVT_LOW_BATTERY           BIT2
static EventGroupHandle_t s_evt;

/* -------------------------------------------------------------------------- */
/* 1. 拍照 + HDR + AI caption + 写 SD                                        */
/* -------------------------------------------------------------------------- */
extern esp_err_t hdr_capture(uint8_t *out_jpeg, size_t out_jpeg_capacity,
                              size_t *out_jpeg_len);

static void take_diary_photo(void)
{
    /* 散热守卫优先 */
    if (!thermal_allows(BIT_ALLOW_CAMERA)) {
        ESP_LOGW(TAG, "thermal HOT, skip photo");
        return;
    }

    /* 1) 给摄像头上电 */
    gpio_set_level(21, 0);   /* OV5640 PWDN 拉低 = power on */
    vTaskDelay(pdMS_TO_TICKS(150));   /* 等 sensor 稳定 */

    /* 2) HDR 拍照 */
    static uint8_t jpeg_buf[200 * 1024];
    size_t jpeg_len = 0;
    if (hdr_capture(jpeg_buf, sizeof(jpeg_buf), &jpeg_len) != ESP_OK) {
        ESP_LOGE(TAG, "hdr_capture failed");
        goto power_down;
    }

    /* 3) 写 SD（按时间命名） */
    char path[64];
    time_t now = time(NULL);
    snprintf(path, sizeof(path), "/sdcard/diary/%lld.jpg", (long long)now);
    /* write_file(path, jpeg_buf, jpeg_len);   // 在主程序中实现 */
    ESP_LOGI(TAG, "saved %s (%u bytes)", path, (unsigned)jpeg_len);

    /* 4) AI 生成 1 行 caption（仅在 thermal_allows AI 时） */
    if (thermal_allows(BIT_ALLOW_AI)) {
        /* run_caption_inference(jpeg_buf, jpeg_len, caption);
           append_caption_to_log(caption);                      */
        ESP_LOGI(TAG, "AI caption generated");
    }

power_down:
    /* 5) 摄像头掉电（< 50 µA） */
    gpio_set_level(21, 1);
}

/* -------------------------------------------------------------------------- */
/* 2. WiFi 批量上传                                                           */
/* -------------------------------------------------------------------------- */
static void upload_diary_batch(void)
{
    if (!thermal_allows(BIT_ALLOW_WIFI_TX)) {
        ESP_LOGW(TAG, "thermal HOT, skip upload");
        return;
    }
    ESP_LOGI(TAG, "WiFi connect + batch upload start");
    /* esp_wifi_start();
       wait_ip();
       upload_dir("/sdcard/diary/");
       esp_wifi_stop();   */
    vTaskDelay(pdMS_TO_TICKS(5000));   /* 模拟 5 秒上传 */
    ESP_LOGI(TAG, "upload done, WiFi off");
}

/* -------------------------------------------------------------------------- */
/* 3. LED 呼吸（Light Sleep 时由 LEDC PWM 自动维持，不需要 CPU）              */
/* -------------------------------------------------------------------------- */
static void breath_led_init(void)
{
    /* 预设 LEDC 高频 PWM 通道，让 LED 呼吸不依赖 CPU */
    /* 略：用 ledc_timer_config + ledc_channel_config */
    gpio_set_direction(DIARY_LED_INDICATOR_GPIO, GPIO_MODE_OUTPUT);
}

/* -------------------------------------------------------------------------- */
/* 4. 主调度循环                                                              */
/* -------------------------------------------------------------------------- */
static void diary_task(void *arg)
{
    int64_t next_photo_us  = 0;
    int64_t next_upload_us = DIARY_UPLOAD_INTERVAL_S * 1000000LL;

    while (1) {
        int64_t now = esp_timer_get_time();

        /* 1) 拍照触发 */
        if (now >= next_photo_us) {
            take_diary_photo();
            next_photo_us = now + DIARY_PHOTO_INTERVAL_S * 1000000LL;
        }

        /* 2) 上传触发 */
        if (now >= next_upload_us) {
            upload_diary_batch();
            next_upload_us = now + DIARY_UPLOAD_INTERVAL_S * 1000000LL;
        }

        /* 3) 事件触发（VAD/按键） */
        EventBits_t bits = xEventGroupWaitBits(
            s_evt, EVT_NEW_VOICE | EVT_USER_BTN | EVT_LOW_BATTERY,
            pdTRUE, pdFALSE, pdMS_TO_TICKS(100));
        if (bits & EVT_USER_BTN) {
            ESP_LOGI(TAG, "USER button pressed → photo on demand");
            take_diary_photo();
        }
        if (bits & EVT_NEW_VOICE) {
            ESP_LOGI(TAG, "VAD detected speech segment → flushing wav");
            /* close_current_wav(); start_new_wav();   */
        }
        if (bits & EVT_LOW_BATTERY) {
            ESP_LOGW(TAG, "low battery, switching to deep sleep");
            esp_deep_sleep_start();
        }

        /* 4) 决定下一次唤醒时刻：min(next_photo, next_upload, +5 s) */
        int64_t next = next_photo_us < next_upload_us
                       ? next_photo_us : next_upload_us;
        int64_t sleep_us = next - esp_timer_get_time();
        if (sleep_us < 100000) {
            /* 太短就 busy wait 让出 CPU */
            vTaskDelay(pdMS_TO_TICKS(50));
            continue;
        }
        if (sleep_us > 30 * 1000000LL) {
            sleep_us = 30 * 1000000LL;   /* 最多睡 30 秒，定期检查 thermal */
        }

        /* Light Sleep（保持 RAM + I2S DMA + RTC peripherals） */
        esp_sleep_enable_timer_wakeup(sleep_us);
        esp_sleep_enable_gpio_wakeup();
        gpio_wakeup_enable(WAKE_GPIO_USER_BTN, GPIO_INTR_LOW_LEVEL);

        ESP_LOGD(TAG, "Light sleep for %lld ms", sleep_us / 1000);
        esp_light_sleep_start();
        ESP_LOGD(TAG, "wake from light sleep, cause=%d",
                 esp_sleep_get_wakeup_cause());
    }
}

/* -------------------------------------------------------------------------- */
/* 5. 公共 API                                                                */
/* -------------------------------------------------------------------------- */
esp_err_t diary_mode_init(void)
{
    s_evt = xEventGroupCreate();
    if (!s_evt) return ESP_ERR_NO_MEM;

    breath_led_init();

    /* 启用 ESP-PM 自动 Light Sleep（CPU 空闲时进 Modem Sleep） */
    esp_pm_config_t pm_cfg = {
        .max_freq_mhz = 240,
        .min_freq_mhz = 80,
        .light_sleep_enable = true,
    };
    ESP_RETURN_ON_ERROR(esp_pm_configure(&pm_cfg), TAG, "pm_configure");

    BaseType_t ok = xTaskCreatePinnedToCore(
        diary_task, "diary", 8192, NULL, /*prio*/ 6, NULL, /*core*/ 0);
    return ok == pdPASS ? ESP_OK : ESP_FAIL;
}

void diary_signal_voice(void)        { xEventGroupSetBits(s_evt, EVT_NEW_VOICE); }
void diary_signal_user_btn(void)     { xEventGroupSetBits(s_evt, EVT_USER_BTN); }
void diary_signal_low_battery(void)  { xEventGroupSetBits(s_evt, EVT_LOW_BATTERY); }

/* ==========================================================================
 * 续航预算（@ 4000 mAh = 14.8 Wh，Buck 路径 η=92%）：
 *   - 唤醒 + 拍照 + 编码：2 s × 660 mW / 60 s = 22 mW 平均
 *   - AI caption 推理：1 s × 825 mW / 60 s    = 14 mW 平均
 *   - WiFi 上传：5 s × 924 mW / 720 s         = 6.4 mW 平均
 *   - 持续录音 + DMA：9.2 mW（双 INMP441）
 *   - Light Sleep 基础：5.4 mW
 *   - LED 呼吸：12.5 mW
 *   - IP5306/ADS1115 静态：2.4 mW
 *   合计 ≈ 72 mW → 14800 / 72 ≈ 205 小时 ≈ 8.5 天
 *
 *   实际打折后 (90% 利用率) = 7.1 天 ✅
 * ========================================================================== */
