"""InstaFreeHeart · 散热设计可视化（最终方案）。

输出：
  out/thermal_powers.png        发热功率拆解（按工况）
  out/thermal_network.png       散热路径示意（佩戴时）
  out/thermal_temperatures.png  皮肤温度（按工况，含安全阈值）
  out/thermal_overview.png      三合一总览
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches as patches
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
# 工况 → 子部件功率（W）
# ---------------------------------------------------------------------------
SCENARIOS = [
    ("待机\nLight Sleep",
     {"ESP32": 0.10, "1 LED 呼吸": 0.04}),
    ("正常使用\n(拍照+录音+8 LED)",
     {"ESP32": 0.55, "OV5640": 0.15, "INMP441×2": 0.03,
      "WS2812B 8 颗": 0.48, "TF 卡": 0.10, "杂项": 0.14}),
    ("AI 推理 +\nWiFi 上传",
     {"ESP32": 0.85, "WiFi RF": 0.45, "OV5640": 0.20,
      "WS2812B 8 颗": 0.72, "杂项": 0.43}),
    ("充电中\n(USB-C 1A)",
     {"IP5306 PMU": 0.88, "电池内阻": 0.30, "ESP32": 0.10,
      "杂项": 0.07}),
    ("★ 边充电+录像+AI\n(最坏)",
     {"IP5306 PMU": 0.88, "电池内阻": 0.55, "ESP32": 0.85,
      "OV5640": 0.20, "WS2812B": 0.72, "WiFi": 0.30, "杂项": 0.18}),
    ("USB-C 5V 输出 1A\n(给手机充)",
     {"IP5306 升压": 0.68, "电池放电": 0.50, "ESP32": 0.10,
      "杂项": 0.17}),
]

SKIN_TEMPS = {
    "待机":                   33.5,
    "正常使用":               36.0,
    "AI + WiFi":              37.4,
    "充电中":                 36.7,
    "★ 最坏 (限功率后)":      38.5,
    "USB-C 输出":             37.0,
}

SAFE_LONG = 41.0
SAFE_SHORT = 48.0


# ---------------------------------------------------------------------------
# 1. 发热功率
# ---------------------------------------------------------------------------
def render_powers(ax):
    names = [s[0] for s in SCENARIOS]
    n = len(names)

    component_order = []
    for _, comps in SCENARIOS:
        for c in comps:
            if c not in component_order:
                component_order.append(c)

    data = {c: [scn[1].get(c, 0.0) for scn in SCENARIOS]
            for c in component_order}

    cmap = matplotlib.colormaps["tab20"]
    colors = [cmap(i / max(1, len(component_order) - 1))
               for i in range(len(component_order))]

    x = np.arange(n)
    width = 0.6
    bottoms = np.zeros(n)
    for i, (c, vals) in enumerate(data.items()):
        ax.bar(x, vals, width, bottom=bottoms, label=c,
                color=colors[i], edgecolor="white", linewidth=0.4)
        bottoms = bottoms + np.array(vals)

    for i, t in enumerate(bottoms):
        ax.text(i, t + 0.05, f"{t:.2f} W", ha="center",
                va="bottom", fontsize=9, fontweight="bold",
                color="#c0392b" if t > 3.0 else
                       "#e67e22" if t > 1.5 else "#27ae60")

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("发热功率 (W)", fontsize=11)
    ax.set_title("① 各工况发热功率拆解",
                  fontsize=12, fontweight="bold", pad=10)
    ax.legend(loc="center left", bbox_to_anchor=(1.02, 0.5),
              fontsize=8, frameon=False)
    ax.set_ylim(0, max(bottoms) * 1.15)
    ax.grid(True, axis="y", alpha=0.3)


# ---------------------------------------------------------------------------
# 2. 散热路径示意
# ---------------------------------------------------------------------------
def render_network(ax):
    ax.axis("off")
    ax.set_xlim(0, 10)
    ax.set_ylim(0, 10)

    ax.text(5, 9.5, "② 散热路径（佩戴时）",
            ha="center", fontsize=12, fontweight="bold")

    boxes = [
        (1.5, 7.8, 7.0, 0.8, "热源：ESP32-S3 / IP5306 / OV5640 (PCB 顶面)",
         "#c0392b", "white"),
        (2.0, 6.7, 6.0, 0.6, "0.5 mm TIM 导热硅胶垫 (k=5 W/m·K)",
         "#f1c40f", "black"),
        (2.0, 5.7, 6.0, 0.6, "25 μm 石墨烯散热膜 (k=1500 W/m·K，横向均温)",
         "#2c3e50", "white"),
        (1.5, 4.5, 7.0, 0.8, "后壳 PETG (k=0.2 W/m·K) + 24 透气孔自由对流",
         "#9c79c8", "white"),
        (2.0, 3.4, 6.0, 0.6, "0.5 mm 硅胶贴肤层 (k=0.2 W/m·K)",
         "#c8a07d", "black"),
        (1.5, 2.2, 7.0, 0.8, "皮肤接触面 (38.5 ℃ ≤ 41 ℃ 安全阈)",
         "#27ae60", "white"),
    ]

    for x, y, w, h, label, fc, tc in boxes:
        ax.add_patch(patches.FancyBboxPatch(
            (x, y), w, h, boxstyle="round,pad=0.05",
            facecolor=fc, edgecolor="black", linewidth=0.7))
        ax.text(x + w / 2, y + h / 2, label,
                ha="center", va="center", color=tc, fontsize=9.5)

    for i in range(len(boxes) - 1):
        x = 5
        y_start = boxes[i][1]
        y_end = boxes[i + 1][1] + boxes[i + 1][3]
        ax.annotate("", xy=(x, y_end), xytext=(x, y_start),
                     arrowprops=dict(arrowstyle="->", color="#555",
                                      linewidth=1.5))

    ax.text(5, 0.8,
             "★ 闭环温控：ADS1115 + 3 NTC → thermal_guard.c 自动降功耗",
             ha="center", fontsize=10, color="#27ae60", fontweight="bold")


# ---------------------------------------------------------------------------
# 3. 皮肤温度
# ---------------------------------------------------------------------------
def render_temperatures(ax):
    names = list(SKIN_TEMPS.keys())
    temps = list(SKIN_TEMPS.values())

    x = np.arange(len(names))
    colors = ["#27ae60" if t < SAFE_LONG else
              "#f39c12" if t < SAFE_SHORT else "#c0392b"
              for t in temps]

    ax.bar(x, temps, 0.55, color=colors,
            edgecolor="black", linewidth=0.5)

    for i, t in enumerate(temps):
        ax.text(i, t + 0.3, f"{t:.1f} ℃",
                ha="center", fontsize=9.5, fontweight="bold")

    ax.axhline(SAFE_LONG, color="#27ae60", linestyle="--", linewidth=1.5,
                label=f"长期接触安全 {SAFE_LONG:.0f} ℃")
    ax.axhline(SAFE_SHORT, color="#c0392b", linestyle=":", linewidth=1.5,
                label=f"短时接触限值 {SAFE_SHORT:.0f} ℃")

    ax.set_xticks(x)
    ax.set_xticklabels(names, fontsize=9)
    ax.set_ylabel("皮肤接触面温度 (℃)", fontsize=11)
    ax.set_title("③ 皮肤温度（IEC 60601 / GB 4943.1 安全阈对比）",
                  fontsize=12, fontweight="bold", pad=10)
    ax.set_ylim(28, 50)
    ax.legend(loc="upper right", fontsize=9)
    ax.grid(True, axis="y", alpha=0.3)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    fig = plt.figure(figsize=(20, 11))
    gs = fig.add_gridspec(2, 2, hspace=0.32, wspace=0.18,
                           top=0.93, bottom=0.05,
                           left=0.05, right=0.97)
    ax1 = fig.add_subplot(gs[0, 0]); render_powers(ax1)
    ax2 = fig.add_subplot(gs[0, 1]); render_network(ax2)
    ax3 = fig.add_subplot(gs[1, :]); render_temperatures(ax3)

    fig.suptitle("InstaFreeHeart · 散热设计（最终方案）",
                  fontsize=15, fontweight="bold", y=0.985)
    fig.savefig(OUT / "thermal_overview.png", dpi=170, bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {OUT/'thermal_overview.png'}")

    for name, fn in [("thermal_powers.png", render_powers),
                      ("thermal_network.png", render_network),
                      ("thermal_temperatures.png", render_temperatures)]:
        fig, ax = plt.subplots(figsize=(11, 7))
        fn(ax)
        fig.savefig(OUT / name, dpi=170, bbox_inches="tight")
        plt.close(fig)
        print(f"[OK] {OUT/name}")


if __name__ == "__main__":
    main()
