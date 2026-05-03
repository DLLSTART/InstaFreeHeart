# InstaFreeHeart · HDR 夜景日记 Pipeline

> 解决：OV5640 单帧动态范围只有 60 dB，夜景中亮处过曝、暗处涂黑。
> 方案：软件多帧曝光融合（Mertens 2007），把动态范围撑到 ~120 dB（+6 stops）。
> 适用：静态场景（夜景日记 ≥ 90% 场景适用）。
> 参考实现：[`hdr_pipeline.c`](hdr_pipeline.c)

---

## 1. 当前方案：双路 HDR

| 路径 | 实现 | 动态范围 | 适用场景 |
|------|------|---------|---------|
| 软件 Mertens fusion (3 帧) | 在 PSRAM 中算 | +6 stops | 静态场景（默认） |
| OV5640 硬件 HDR (line-interleaved) | sensor 寄存器开启 | +4 stops | 动态场景（边走边拍） |

软件 HDR 默认开启（0 成本）；当检测到运动模糊（用 ME motion estimation 判断）时，
自动切换到 OV5640 硬件 HDR 路径。两条路径在固件中按场景自动选择。

## 2. 软件 Mertens fusion 工作流

```
┌─────────────────────────────────────────────────────────────────┐
│ ① 关闭 AEC（手动曝光）                                           │
│ ② 拍 3 张：EV=-2 / EV=0 / EV=+2，间隔 80 ms (等曝光生效)         │
│ ③ 每张算 3 个权重图：                                            │
│     W_contrast    = |Y - mean3x3(Y)|     // 边缘细节             │
│     W_saturation  = max(R,G,B) - min     // 色彩饱和             │
│     W_well_exposed = 三角形(Y, 中点 128) // 远离过曝/欠曝         │
│     W = W_c × W_s × W_we                                         │
│ ④ 加权融合：out(x) = Σ_k W_k(x) × frame_k(x) / Σ_k W_k(x)        │
│ ⑤ JPEG 编码 + 写 SD                                             │
└─────────────────────────────────────────────────────────────────┘
```

### PSRAM 占用预算

| 项 | 大小 (1280×720 RGB565) |
|----|----------------------|
| 3 帧原图 | 3 × 1.83 MB = **5.49 MB** |
| 3 张权重 (uint16 Q8.8) | 3 × 1.83 MB = **5.49 MB** |
| 1 张融合输出 | **1.83 MB** |
| **峰值总占用** | **~12.8 MB** ❌ 超过 8 MB PSRAM |

### 解决方案：分块（tile）处理

把 1280×720 切成 8 个 1280×90 横条，每条单独算权重 + 融合：
- 单条占用 = 3 × 1280 × 90 × 2 + 3 × 1280 × 90 × 2 + 1280 × 90 × 2 = **1.6 MB**
- 留给 OS / WiFi / 摄像头 driver = ~6 MB ✅
- 每条耗时 ~70 ms，8 条总计 ~560 ms

如果分辨率降到 800×600（够日记缩略图用）：
- 单帧 = 800 × 600 × 2 = 0.96 MB
- 三帧 + 三权重 + 一融合 = 6.7 MB，**不需要分块** ✅

## 3. 调用约定（与其它任务的协调）

```c
#include "hdr_pipeline.h"
#include "thermal_guard.h"

void diary_take_photo(void) {
    if (!thermal_allows(BIT_ALLOW_CAMERA)) {
        ESP_LOGW(TAG, "thermal too high, skipping photo");
        return;
    }

    uint8_t *jpeg = heap_caps_malloc(200 * 1024, MALLOC_CAP_SPIRAM);
    size_t   jpeg_len;
    if (hdr_capture(jpeg, 200 * 1024, &jpeg_len) == ESP_OK) {
        char path[128];
        snprintf(path, sizeof(path),
                 "/sdcard/diary/%lld_hdr.jpg", time(NULL));
        write_file(path, jpeg, jpeg_len);
    }
    free(jpeg);
}
```

## 4. OV5640 sensor 关键参数

| 项 | 数值 |
|----|------|
| 像素 | 500 W (2592×1944 max) |
| DVP 接口 | 8-bit |
| 封装 | 24P 0.5 mm FPC |
| I²C 地址 | 0x3C |
| HDR | 硬件 line-interleaved |
| ESP-IDF 驱动 | esp32-camera (sensor=OV5640) |
| 嘉立创料号 | C44391 |

## 5. 性能 / 对比测试

预期效果（实测后填）：

| 场景 | 单帧 | HDR 融合 |
|------|------|---------|
| 夜景路灯下日记本 | 路灯爆白、文字看不清 | 路灯保留细节、文字清晰可读 |
| 室内逆光人脸 | 脸黑成剪影 | 脸 + 背景都清晰 |
| 屏幕拍照（手机/电脑） | 屏幕过曝 | 屏幕内容可读 |
| 阳光直射 | 阴影涂黑 | 阴影细节恢复 |

## 6. 进一步优化（v2 路线）

1. **GPU/SIMD 加速**：ESP32-S3 PIE (128-bit SIMD) 有 vector add/mul，权重计算可加速 4×
2. **拉普拉斯金字塔融合**：Mertens 原论文用 5 层金字塔，效果更好但内存翻 2×
3. **AI 去噪**：融合后跑一遍 esp-dl 的去噪 CNN（如 DnCNN-tiny），SNR +6 dB
4. **白平衡矫正**：融合前对 3 帧分别白平衡（LSC），避免色偏
5. **运动检测**：拍前用 ME (motion estimation) 判断场景静止度，动态场景退化为单帧

## 7. 参考实现（开源）

- [Mertens 原论文](https://mericam.github.io/papers/exposure_fusion_reduced.pdf)
- [OpenCV `cv::createMergeMertens()`](https://docs.opencv.org/4.x/d7/dd6/classcv_1_1MergeMertens.html)
- [ESP-IDF esp32-camera](https://github.com/espressif/esp32-camera) — 摄像头 driver
