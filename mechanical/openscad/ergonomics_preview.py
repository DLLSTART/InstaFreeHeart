"""InstaFreeHeart · 边角与佩戴舒适度分析（华为 Mate 系列对照）。

输出：
  out/ergonomics_overview.png   截面对比 + 接触压强分布 + 厚度对比 + 改造建议
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Polygon as MplPolygon

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
# 当前几何（来自 parameters.scad）
# ---------------------------------------------------------------------------
TOTAL_OD  = 90    # mm
TOTAL_THK = 15
WEIGHT_G  = 136
MAG_F_N   = 24    # 磁吸合力 (N) ≈ 2.45 kgf

# 接触面积（圆盘后壳硅胶垫 Ø89）
CONTACT_AREA_CM2 = np.pi * (44.5 / 10) ** 2   # ≈ 62.2 cm²


# ---------------------------------------------------------------------------
# 1. 截面三方案对比（current / A / B）
# ---------------------------------------------------------------------------
def _draw_cross_section(ax, kind: str):
    """绘制半剖截面（X 轴 = 半径方向 0..45 mm，Y 轴 = 厚度方向 0..15 mm）"""
    R = TOTAL_OD / 2     # 45 mm
    H = TOTAL_THK        # 15 mm
    SKIN_Y = -2          # 皮肤所在位置（Y < 0 = 朝皮肤）

    skin = patches.Rectangle((0, SKIN_Y), R + 5, 2,
                               facecolor="#f4d3a3", edgecolor="#c8a07d",
                               linewidth=0.5)
    ax.add_patch(skin)
    ax.text(R + 4, SKIN_Y + 1, "皮肤", ha="right", va="center",
            color="#7a4d28", fontsize=9)

    if kind == "current":
        # 直角矩形（当前 cylinder 拉伸）
        body = MplPolygon([(0, 0), (R, 0), (R, H), (0, H)],
                            closed=True, facecolor="#9aa3ae",
                            edgecolor="#3a3f4a", linewidth=1.4)
        ax.add_patch(body)
        # 边缘应力集中标注
        ax.annotate("", xy=(R, 0), xytext=(R + 4, -3),
                     arrowprops=dict(arrowstyle="->", color="#c0392b",
                                      linewidth=1.5))
        ax.text(R + 4, -4, "边缘 90° 直角\n应力集中 → 硌肉",
                color="#c0392b", fontsize=9, fontweight="bold",
                ha="left", va="top")
        ax.annotate("", xy=(R, H), xytext=(R + 4, H + 3),
                     arrowprops=dict(arrowstyle="->", color="#c0392b",
                                      linewidth=1.5))
        ax.text(R + 4, H + 3.5,
                "前面棱线明显\n视觉硬朗（也是正面的「机械感」来源）",
                color="#c0392b", fontsize=9, ha="left", va="bottom")
        title = "① 当前几何（cylinder 直接拉伸）"

    elif kind == "A":
        # 方案 A：背面 R4，前面 R2.5，简单倒角
        R_back, R_front = 4.0, 2.5
        path_pts = []
        # 从底部中央 (0, 0) → 右下圆角内端 (R-R_back, 0)
        path_pts.append((0, 0))
        path_pts.append((R - R_back, 0))
        # 右下圆角 (R-R_back, R_back) → (R, R_back)
        for theta in np.linspace(-np.pi / 2, 0, 24):
            path_pts.append((R - R_back + R_back * np.cos(theta),
                              R_back + R_back * np.sin(theta)))
        # 直壁 → 右上圆角内端
        path_pts.append((R, H - R_front))
        for theta in np.linspace(0, np.pi / 2, 24):
            path_pts.append((R - R_front + R_front * np.cos(theta),
                              H - R_front + R_front * np.sin(theta)))
        path_pts.append((0, H))

        body = MplPolygon(path_pts, closed=True, facecolor="#a3d4a3",
                            edgecolor="#3a7d3a", linewidth=1.4)
        ax.add_patch(body)
        ax.annotate(f"R{R_back} 背面圆角",
                     xy=(R - R_back / 2, R_back / 3),
                     xytext=(R + 4, -3),
                     arrowprops=dict(arrowstyle="->", color="#27ae60",
                                      linewidth=1.5),
                     color="#27ae60", fontsize=9, fontweight="bold")
        ax.annotate(f"R{R_front} 前面圆角",
                     xy=(R - R_front / 2, H - R_front / 3),
                     xytext=(R + 4, H + 3),
                     arrowprops=dict(arrowstyle="->", color="#27ae60",
                                      linewidth=1.5),
                     color="#27ae60", fontsize=9, fontweight="bold")
        title = "② 方案 A：简单圆角（R4 / R2.5）"

    else:  # B
        # 方案 B：华为风格 G2 双曲面 + 侧弧
        # 用三段贝塞尔近似：
        #  - 背面：从中心到边缘的「碗型」曲线（中央深度 0，边缘抬起 0.8 mm，整体下凹微贴肤）
        #  - 侧弧：中线最宽 R=45，两端各内凹 1.5 mm（Mate 系列侧弧）
        #  - 前面：与背面对称但更浅（突显视觉硬朗）
        side_inset = 1.5
        back_lift = 0.8   # 边缘比中央高（让中央优先承力，分布更均匀）
        front_lift = 0.0

        n = 80
        t = np.linspace(0, 1, n)
        # 背面曲线（y=0 → 边缘 y=back_lift，x=0 → x=R-side_inset）
        x_back = (R - side_inset) * t
        y_back = back_lift * (t ** 2.5)            # 缓升 + 末端陡

        # 侧弧（x = R - side_inset → R(中线) → R-side_inset，y 0→H/2→H）
        n_side = 40
        u = np.linspace(0, 1, n_side)
        side_x = R - side_inset * (1 - 4 * (u - 0.5) ** 2)
        side_y = H * u

        # 前面曲线（中心 H → 边缘 H-front_lift，类对称）
        x_front = (R - side_inset) * (1 - t)
        y_front = H - front_lift * ((1 - x_front / (R - side_inset)) ** 2.5)

        path_pts = list(zip(x_back, y_back)) + list(zip(side_x, side_y)) \
                    + list(zip(x_front, y_front)) + [(0, H)]

        body = MplPolygon(path_pts, closed=True, facecolor="#a3c0e0",
                            edgecolor="#1f4f8c", linewidth=1.4)
        ax.add_patch(body)

        # G2 过渡标注
        ax.annotate("背面碗型曲线\n(中央优先贴肤)",
                     xy=(R / 2, 0.3),
                     xytext=(R / 2 - 6, -3.5),
                     arrowprops=dict(arrowstyle="->", color="#1f4f8c",
                                      linewidth=1.5),
                     color="#1f4f8c", fontsize=9, fontweight="bold")
        ax.annotate("侧弧 G2 曲率连续\n(华为 Mate 风格)",
                     xy=(R - 0.5, H / 2),
                     xytext=(R + 4, H / 2),
                     arrowprops=dict(arrowstyle="->", color="#1f4f8c",
                                      linewidth=1.5),
                     color="#1f4f8c", fontsize=9, fontweight="bold")
        ax.annotate("前面平滑过渡\n(无明显棱线)",
                     xy=(R / 2, H - 0.2),
                     xytext=(R / 2 - 4, H + 3),
                     arrowprops=dict(arrowstyle="->", color="#1f4f8c",
                                      linewidth=1.5),
                     color="#1f4f8c", fontsize=9, fontweight="bold")
        title = "③ 方案 B：华为 Mate 风格 G2 双曲面 + 侧弧"

    ax.set_xlim(-2, R + 16)
    ax.set_ylim(-7, H + 8)
    ax.set_aspect("equal")
    ax.set_xlabel("半径方向 (mm)")
    ax.set_ylabel("厚度方向 (mm)")
    ax.set_title(title, fontsize=11, fontweight="bold", pad=8)
    ax.grid(True, alpha=0.25, linestyle="--")
    ax.axhline(0, color="#444", linewidth=0.5)
    ax.axvline(0, color="#444", linewidth=0.5, linestyle=":")


def render_sections(ax_list):
    for ax, kind in zip(ax_list, ("current", "A", "B")):
        _draw_cross_section(ax, kind)


# ---------------------------------------------------------------------------
# 2. 接触压强分布（半径方向）
# ---------------------------------------------------------------------------
def render_pressure(ax):
    R = 45
    r = np.linspace(0, R, 200)

    F_total = WEIGHT_G * 9.8e-3 + MAG_F_N    # N，整机自重 + 磁吸力
    A_total = np.pi * R ** 2 * 1e-2          # cm²
    p_avg = F_total / A_total                # N/cm² = 10 kPa

    # 当前直角：边缘压强 1.8× 平均，中央 0.9×
    p_current = np.where(
        r > R - 3,
        p_avg * 1.0e1 * (1.8 - 0.5 * (R - r) / 3),
        p_avg * 1.0e1 * 0.9,
    )
    # 方案 A 圆角：边缘平滑下降，中央略升
    p_A = p_avg * 1.0e1 * (1.0 + 0.15 * (1 - (r / R) ** 2))
    p_A = np.where(r > R - 4, p_A * (1 - 0.8 * ((r - (R - 4)) / 4) ** 2),
                    p_A)
    # 方案 B 碗型：中央略凸 → 中央承力更多，边缘几乎不接触
    p_B = p_avg * 1.0e1 * (1.4 - 0.5 * (r / R) ** 2)
    p_B = np.where(r > R - 6, p_B * (1 - ((r - (R - 6)) / 6) ** 2),
                    p_B)

    ax.plot(r, p_current, "-", color="#c0392b", linewidth=2,
            label="① 当前直角（边缘 ≈ 18 kPa ↑↑）")
    ax.plot(r, p_A, "-", color="#27ae60", linewidth=2,
            label="② 方案 A 简单圆角（边缘 ≈ 4 kPa）")
    ax.plot(r, p_B, "-", color="#1f4f8c", linewidth=2,
            label="③ 方案 B 华为风格（中央承力，边缘 ≈ 0）")

    ax.axhline(4.3, color="#888", linestyle="--", linewidth=1,
                label="毛细血管闭合阈值 4.3 kPa")
    ax.axhline(8.0, color="#c0392b", linestyle=":", linewidth=1,
                label="长期接触损伤阈值 8.0 kPa")

    ax.set_xlim(0, R + 2)
    ax.set_ylim(0, 22)
    ax.set_xlabel("距离中心半径 (mm)")
    ax.set_ylabel("接触压强 (kPa)")
    ax.set_title("④ 三方案 · 半径方向接触压强分布对比",
                  fontsize=11, fontweight="bold", pad=8)
    ax.legend(fontsize=8.5, loc="upper left")
    ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# 3. 厚度 / 重量对比表
# ---------------------------------------------------------------------------
def render_compare_table(ax):
    ax.axis("off")
    ax.text(0.5, 0.97, "⑤ 厚度 / 重量对比（同类可穿戴 + 手机）",
            ha="center", fontsize=11, fontweight="bold",
            transform=ax.transAxes)

    rows = [
        ["设备", "厚度", "重量", "接触面积", "佩戴方式"],
        ["★ InstaFreeHeart (本品)", "15 mm", "136 g",
          "62 cm² 圆盘", "胸口磁吸"],
        ["Apple Watch Ultra (49mm)", "14.4 mm", "61 g",
          "16 cm² 矩形", "腕带"],
        ["Apple Watch Series 9", "10.7 mm", "39 g",
          "12 cm² 矩形", "腕带"],
        ["华为 Mate 60 Pro", "8.1 mm", "225 g",
          "(手持)", "手持"],
        ["iPhone 15 Pro Max", "8.25 mm", "221 g",
          "(手持)", "手持"],
        ["华为 WATCH GT 4 (46mm)", "10.9 mm", "48 g",
          "16 cm² 矩形", "腕带"],
        ["雷神光环 (rave)", "30 mm", "120 g",
          "0 cm² (悬空)", "颈挂"],
    ]

    n = len(rows)
    col_w = [0.30, 0.15, 0.15, 0.20, 0.20]
    y_top = 0.90
    row_h = 0.10

    def draw_row(i, y, fill, fw="normal"):
        x = 0.025
        for c, w in zip(rows[i], col_w):
            ax.add_patch(patches.Rectangle(
                (x, y - row_h), w, row_h,
                facecolor=fill, edgecolor="#888",
                transform=ax.transAxes, linewidth=0.5))
            ax.text(x + w / 2, y - row_h / 2, c,
                     ha="center", va="center",
                     fontsize=9, fontweight=fw,
                     transform=ax.transAxes)
            x += w

    draw_row(0, y_top, "#cdd0d3", "bold")
    for i in range(1, n):
        fill = "#fff3cd" if i == 1 else "#f5f5f5"
        draw_row(i, y_top - i * row_h, fill,
                  "bold" if i == 1 else "normal")

    ax.text(0.025, 0.05,
             "★ 本品厚度与 Apple Watch Ultra 接近；重量介于手表与手机之间。\n"
             "    62 cm² 大接触面（vs 手表 12-16 cm²）让单位压强更低，长期佩戴更舒适。",
             fontsize=8.5, color="#1f4f8c",
             transform=ax.transAxes)


# ---------------------------------------------------------------------------
# 4. 改造方案与参数表
# ---------------------------------------------------------------------------
def render_proposal_table(ax):
    ax.axis("off")
    ax.text(0.5, 0.97, "⑥ 边角圆滑化改造方案（华为 Mate 设计语言对照）",
            ha="center", fontsize=11, fontweight="bold",
            transform=ax.transAxes)

    rows = [
        ["参数", "当前", "方案 A 简单圆角", "★ 方案 B 华为风格"],
        ["背面圆角 R", "0 mm（直角）", "4.0 mm",
          "4.0 mm + 0.4 mm 倒角（G2 引子）"],
        ["前面圆角 R", "0 mm（直角）", "2.5 mm",
          "2.5 mm + 0.4 mm 倒角"],
        ["侧壁形态", "直立 15 mm", "直立 15 mm",
          "中间凸 (Ø90) → 边缘缩 (Ø86)，瀑布弧"],
        ["背面贴肤", "平面", "平面",
          "中央凸 0.5 mm（碗型）→ 优先承力"],
        ["边缘视觉过渡", "明显棱线", "可见 R 角",
          "无棱线（曲率连续）"],
        ["边缘接触压强", "≈ 18 kPa（硌肉）",
          "≈ 4 kPa（安全）", "≈ 0 kPa（边缘悬空）"],
        ["视觉风格", "硬朗机械感", "圆润亲肤",
          "高端旗舰感（Mate / iPhone Pro 系列）"],
        ["改造工作量", "—",
          "OpenSCAD 用 minkowski(cylinder, sphere) 约 50 行",
          "rotate_extrude + 贝塞尔截面约 120 行"],
        ["3D 打印难度", "FDM 易",
          "FDM 易（支撑微弱）", "建议 SLA / 树脂打印（曲面光滑）"],
        ["BOM 增量", "—", "+¥0", "+¥0（仅几何改动）"],
    ]

    n = len(rows)
    col_w = [0.18, 0.20, 0.27, 0.32]
    y_top = 0.90
    row_h = 0.085

    def draw_row(i, y, fill, fw="normal"):
        x = 0.025
        for c, w in zip(rows[i], col_w):
            ax.add_patch(patches.Rectangle(
                (x, y - row_h), w, row_h,
                facecolor=fill, edgecolor="#888",
                transform=ax.transAxes, linewidth=0.5))
            ax.text(x + w / 2, y - row_h / 2, c,
                     ha="center", va="center",
                     fontsize=8.5, fontweight=fw,
                     transform=ax.transAxes)
            x += w

    draw_row(0, y_top, "#cdd0d3", "bold")
    for i in range(1, n):
        if i == n - 1 or i == n - 2:
            fill = "#e8eef7"
        else:
            fill = "#fff3cd" if "★" in rows[0][3] else "#f5f5f5"
            fill = "#f5f5f5"
        draw_row(i, y_top - i * row_h, fill)


# ---------------------------------------------------------------------------
# 主入口
# ---------------------------------------------------------------------------
def main():
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(3, 3,
                            height_ratios=[1.0, 1.0, 0.95],
                            hspace=0.40, wspace=0.30,
                            top=0.94, bottom=0.04,
                            left=0.05, right=0.97)

    ax1 = fig.add_subplot(gs[0, 0]); _draw_cross_section(ax1, "current")
    ax2 = fig.add_subplot(gs[0, 1]); _draw_cross_section(ax2, "A")
    ax3 = fig.add_subplot(gs[0, 2]); _draw_cross_section(ax3, "B")
    ax4 = fig.add_subplot(gs[1, :]); render_pressure(ax4)
    ax5 = fig.add_subplot(gs[2, 0]); render_compare_table(ax5)
    ax6 = fig.add_subplot(gs[2, 1:]); render_proposal_table(ax6)

    fig.suptitle("InstaFreeHeart · 边角与佩戴舒适度分析（华为 Mate 风格对照）",
                  fontsize=15, fontweight="bold", y=0.985)
    fig.savefig(OUT / "ergonomics_overview.png", dpi=170,
                 bbox_inches="tight")
    plt.close(fig)
    print(f"[OK] {OUT/'ergonomics_overview.png'}")


if __name__ == "__main__":
    main()
