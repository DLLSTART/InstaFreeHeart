"""InstaFreeHeart · 功耗预算与续航分析（最终方案）。

输出：
  out/power_modes.png      4 种使用模式的平均功率拆解
  out/power_runtime.png    各模式续航（电池 4000 mAh / 14.8 Wh）
  out/power_overview.png   二合一总览
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.pyplot as plt
import numpy as np

for f in ("PingFang SC", "Songti SC", "Heiti SC", "STHeiti",
          "Hiragino Sans GB", "Arial Unicode MS"):
    try:
        matplotlib.font_manager.findfont(f, fallback_to_default=False)
        matplotlib.rcParams["font.sans-serif"] = [f] + matplotlib.rcParams[
            "font.sans-serif"]
        matplotlib.rcParams["axes.unicode_minus"] = False
        break
    except Exception:  # noqa: BLE001
        continue

OUT = Path(__file__).resolve().parent / "out"
OUT.mkdir(parents=True, exist_ok=True)

# ---------------------------------------------------------------------------
# 当前方案参数
# ---------------------------------------------------------------------------
BAT_WH = 14.8                  # 4000 mAh × 3.7 V
EFF_3V3 = 0.92                 # SY8088 Buck 路径效率

# ---------------------------------------------------------------------------
# 4 种使用模式（每行 = 一个子系统的「平均功率 mW」）
# ---------------------------------------------------------------------------
MODES = {
    "Deep Sleep\n(不工作)": {
        "ESP32-S3 Deep Sleep":   0.025,
        "OV5640 PWDN":           0.001,
        "INMP441 关":            0.001,
        "WS2812B 静态":          0.0,
        "IP5306 静态":           1.85,
        "ADS1115 待机":          0.5,
    },
    "★ 纯日记模式\n(1 张/分 + 持续录音 + 5min/h 上传)": {
        "ESP32-S3 Light Sleep":  2.5,
        "ESP32-S3 Active 拍照":  26.4,
        "ESP32-S3 AI 推理日记":   8.3,
        "OV5640 拍照":           7.9,
        "INMP441×2 持续录音":    9.2,
        "WiFi TX 日记上传":      9.2,
        "BLE 心跳":              1.7,
        "WS2812B 1 颗呼吸":     12.5,
        "TF 卡写入":             5.0,
        "IP5306 静态":           1.85,
        "ADS1115 NTC":           0.5,
    },
    "高强度日记\n(每分钟拍 + 实时 AI + 实时上传 + 8 灯)": {
        "ESP32-S3 Active":       330,
        "ESP32-S3 AI 推理":      165,
        "OV5640 录像":           60,
        "INMP441×2 录音":        9.2,
        "WiFi TX 实时上传":      277,
        "BLE 广告":              1.7,
        "WS2812B 8 颗白色":     240,
        "TF 卡持续写":           50,
        "IP5306 静态":           1.85,
        "ADS1115 NTC":           0.5,
    },
    "USB-C 5V 输出\n(给手机充电)": {
        "ESP32-S3 Light Sleep":  2.5,
        "WS2812B 1 颗指示":     12.5,
        "IP5306 升压损耗":       680,
        "Battery 放电内阻":      500,
        "BLE 心跳":              1.7,
        "ADS1115 NTC":           0.5,
    },
}


# ---------------------------------------------------------------------------
# 1. 平均功耗拆解
# ---------------------------------------------------------------------------
def render_modes(ax):
    modes = list(MODES.keys())
    n = len(modes)

    component_order: list[str] = []
    for m in modes:
        for comp in MODES[m]:
            if comp not in component_order:
                component_order.append(comp)

    data = {comp: [MODES[m].get(comp, 0.0) for m in modes]
            for comp in component_order}

    cmap = matplotlib.colormaps["tab20"]
    colors = [cmap(i / max(1, len(component_order) - 1))
               for i in range(len(component_order))]

    x = np.arange(n)
    width = 0.55

    bottoms = np.zeros(n)
    for i, (comp, vals) in enumerate(data.items()):
        ax.bar(x, vals, width, bottom=bottoms,
                label=comp, color=colors[i],
                edgecolor="white", linewidth=0.4)
        bottoms = bottoms + np.array(vals)

    totals = bottoms
    for i, t in enumerate(totals):
        if t > 1000:
            label = f"{t/1000:.2f} W"
        else:
            label = f"{t:.0f} mW"
        ax.text(i, t * 1.04, label, ha="center", va="bottom",
                fontsize=10, fontweight="bold",
                color="#c0392b" if t > 500 else "#27ae60" if t < 100
                       else "#e67e22")

    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=8.5)
    ax.set_ylabel("平均功率 (mW，对数轴)", fontsize=11)
    ax.set_title("① 4 种使用模式下的平均功率拆解",
                  fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=7.5, frameon=False)
    ax.set_yscale("log")
    ax.set_ylim(0.5, max(totals) * 3)
    ax.grid(True, axis="y", alpha=0.3, which="both")


# ---------------------------------------------------------------------------
# 2. 续航
# ---------------------------------------------------------------------------
def render_runtime(ax):
    modes = list(MODES.keys())
    p_load_mw = [sum(MODES[m].values()) for m in modes]
    runtime_h = [BAT_WH * 1000 / (p / EFF_3V3) if p > 0 else 0
                  for p in p_load_mw]

    x = np.arange(len(modes))
    bars = ax.bar(x, runtime_h, 0.55,
                    color="#27ae60", edgecolor="#1d6e3f", linewidth=0.6)

    for b, t in zip(bars, runtime_h):
        if t < 1:
            label = f"{t*60:.0f} min"
        elif t < 24:
            label = f"{t:.1f} h"
        elif t < 30 * 24:
            label = f"{t/24:.1f} 天"
        else:
            label = f"{t/24/30:.1f} 月"
        ax.text(b.get_x() + b.get_width()/2, t * 1.05, label,
                ha="center", va="bottom", fontsize=10,
                color="#1d6e3f", fontweight="bold")

    ax.axhline(12, color="#3498db", linestyle="--", linewidth=1.2,
                alpha=0.8, label="目标：12 小时连续工作")
    ax.set_xticks(x)
    ax.set_xticklabels(modes, fontsize=8.5)
    ax.set_ylabel("续航时间 (小时, 对数轴)", fontsize=11)
    ax.set_yscale("log")
    ax.set_ylim(0.05, max(runtime_h) * 3)
    ax.set_title(f"② 各模式续航（电池 {BAT_WH:.1f} Wh = 4000 mAh，"
                  f"3V3 路径 η={EFF_3V3:.0%}）",
                  fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="upper right", fontsize=10)
    ax.grid(True, axis="y", alpha=0.3, which="both")


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    fig = plt.figure(figsize=(20, 8))
    gs = fig.add_gridspec(1, 2, wspace=0.20,
                           top=0.88, bottom=0.10,
                           left=0.05, right=0.97)

    ax1 = fig.add_subplot(gs[0, 0])
    render_modes(ax1)
    ax2 = fig.add_subplot(gs[0, 1])
    render_runtime(ax2)

    fig.suptitle("InstaFreeHeart · 功耗预算与续航（最终方案）",
                  fontsize=15, fontweight="bold", y=0.97)
    fig.savefig(OUT / "power_overview.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {OUT/'power_overview.png'}")

    for name, fn in [("power_modes.png", render_modes),
                      ("power_runtime.png", render_runtime)]:
        fig, ax = plt.subplots(figsize=(11, 7))
        fn(ax)
        fig.savefig(OUT / name, dpi=170, bbox_inches="tight")
        plt.close(fig)
        print(f"[OK] {OUT/name}")


if __name__ == "__main__":
    main()
