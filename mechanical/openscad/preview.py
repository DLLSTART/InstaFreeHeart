"""InstaFreeHeart · 多视图预览生成器（Mark I 圆形特斯拉款）。

输出（写入 out/）：
    preview_top.png        顶视图（从 Z+ 看，4 同心环 + 8 灯柱 + 8 铜线圈 + Y 三支撑）
    preview_side.png       侧视图爆炸（沿 Z 方向 7 层结构）
    preview_back.png       背面视图（5 颗磁铁 + USB-C + 透气孔）
    preview_parts.png      9 件独立平铺图
    preview_overview.png   4 视图合并大图（推荐看这一张）
"""
from __future__ import annotations

import math
import re
from pathlib import Path

import matplotlib
import matplotlib.patches as patches
import matplotlib.pyplot as plt
from matplotlib.patches import Wedge

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


HERE = Path(__file__).resolve().parent
PARAMS_FILE = HERE / "parameters.scad"
OUT = HERE / "out"
OUT.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------------------------
# 1) 解析 parameters.scad
# ---------------------------------------------------------------------------
def load_params(scad_file: Path) -> dict[str, float]:
    pattern = re.compile(
        r"^\s*([A-Z][A-Z0-9_]+)\s*=\s*([-+]?\d+\.?\d*)\s*;",
        re.MULTILINE,
    )
    return {
        m.group(1): float(m.group(2))
        for m in pattern.finditer(scad_file.read_text())
    }


P = load_params(PARAMS_FILE)


# ---------------------------------------------------------------------------
# 2) 颜色常量
# ---------------------------------------------------------------------------
COL_FRONT     = "#cdd0d3"   # 银色金属
COL_BRACKET   = "#d8dadc"   # 高光银
COL_BLUE      = "#3ed1ff"   # Tesla 蓝
COL_BLUE_DK   = "#0e6c8c"   # 深蓝（边线）
COL_COPPER    = "#cd6f30"
COL_COPPER_DK = "#7a3f15"
COL_CENTER    = "#ffffff"   # 中央白光
COL_PCB       = "#0d8043"
COL_BAT       = "#5a5a5a"
COL_BACK      = "#1a1a1a"
COL_MAGNET    = "#a0a4ab"
COL_SILICON   = "#3c3c3c"
COL_USBC      = "#000"


# ---------------------------------------------------------------------------
# 3) 同心环绘制基元
# ---------------------------------------------------------------------------
def _ring(ax, od, id_, **kw):
    """画一个圆环（外径 od，内径 id_）。"""
    outer = patches.Circle((0, 0), od/2, **kw)
    ax.add_patch(outer)
    if id_ > 0:
        inner = patches.Circle((0, 0), id_/2,
                                facecolor="white", edgecolor="none")
        ax.add_patch(inner)


def _wedge(ax, od, id_, theta1, theta2, **kw):
    """画一个扇形环带（环 sector）。"""
    w = Wedge((0, 0), od/2, theta1, theta2, width=(od - id_)/2, **kw)
    ax.add_patch(w)


# ---------------------------------------------------------------------------
# 4) 各部件绘制
# ---------------------------------------------------------------------------
def _draw_outer_ring(ax):
    """⑴ 最外银色金属圈。"""
    _ring(ax, P["OUTER_RING_OD"], P["OUTER_RING_ID"],
           facecolor=COL_FRONT, edgecolor="#5a5d61", linewidth=1.2)


def _draw_outer_lights_and_brackets(ax):
    """⑵ 外圈：8 段蓝光灯柱 + 8 段银色金属夹板。"""
    n = int(P["OUTER_LIGHT_COUNT"])
    light_arc = P["OUTER_LIGHT_ARC"]
    bracket_arc = 360 / n - light_arc

    for i in range(n):
        # 灯柱（蓝光）
        center_angle = 360 * i / n
        l1 = center_angle - light_arc / 2
        l2 = center_angle + light_arc / 2
        _wedge(ax, P["OUTER_LIGHT_OD"], P["OUTER_LIGHT_ID"], l1, l2,
                facecolor=COL_BLUE, edgecolor=COL_BLUE_DK, linewidth=0.6,
                alpha=0.92)
        # 夹板（银色，凸起）
        b_center = center_angle + 360 / n / 2
        b1 = b_center - bracket_arc / 2
        b2 = b_center + bracket_arc / 2
        _wedge(ax, P["OUTER_LIGHT_OD"] + 0.5, P["OUTER_LIGHT_ID"] - 0.5,
                b1, b2,
                facecolor=COL_BRACKET, edgecolor="#5a5d61", linewidth=0.5)
        # 夹板上小铆钉
        knob_r = (P["OUTER_LIGHT_OD"] + P["OUTER_LIGHT_ID"]) / 4
        kx = knob_r * math.cos(math.radians(b_center))
        ky = knob_r * math.sin(math.radians(b_center))
        ax.add_patch(patches.Circle((kx, ky),
                                      P["OUTER_BRACKET_KNOB"]/2,
                                      facecolor="#222", edgecolor="#888",
                                      linewidth=0.4))


def _draw_inner_lights_and_brackets(ax):
    """⑶ 中央内圈灯（8 段蓝光 + 8 段银色骨架）。"""
    n = int(P["OUTER_LIGHT_COUNT"])
    arc = 36

    for i in range(n):
        # 内灯（蓝光）
        center_angle = 360 * i / n + 360 / n / 2
        l1 = center_angle - arc / 2
        l2 = center_angle + arc / 2
        _wedge(ax, P["INNER_LIGHT_OD"], P["INNER_LIGHT_ID"], l1, l2,
                facecolor=COL_BLUE, edgecolor=COL_BLUE_DK, linewidth=0.5,
                alpha=0.85)
        # 骨架
        b_center = 360 * i / n
        _wedge(ax, P["INNER_LIGHT_OD"] + 0.5, P["INNER_LIGHT_ID"] - 0.5,
                b_center - 9, b_center + 9,
                facecolor=COL_BRACKET, edgecolor="#5a5d61", linewidth=0.4)


def _draw_copper_coils(ax):
    """8 个铜色线圈（位于外灯柱之间银夹板的中心位置）。"""
    n = int(P["COIL_COUNT"])
    r = P["COIL_R"]
    coil_d = P["COIL_OD"]
    coil_id = P["COIL_ID"]

    for i in range(n):
        # 夹板中心角度 = 灯柱中心 + 22.5°
        a = 360 * i / n + 360 / n / 2
        cx = r * math.cos(math.radians(a))
        cy = r * math.sin(math.radians(a))
        # 外圈铜环
        ax.add_patch(patches.Circle((cx, cy), coil_d/2,
                                      facecolor=COL_COPPER,
                                      edgecolor=COL_COPPER_DK,
                                      linewidth=0.8))
        # 表面 4 圈纹理（同心圆环）
        for k in range(1, 4):
            rk = coil_d/2 * (1 - 0.18 * k)
            ax.add_patch(patches.Circle((cx, cy), rk,
                                          facecolor="none",
                                          edgecolor=COL_COPPER_DK,
                                          linewidth=0.4))
        # 中央孔
        ax.add_patch(patches.Circle((cx, cy), coil_id/2,
                                      facecolor="#3a3a3a",
                                      edgecolor="#222", linewidth=0.4))


def _draw_tri_supports(ax):
    """中央 Y 字 3 支撞（120° 放射）。"""
    for a_deg in (90, 210, 330):
        a = math.radians(a_deg)
        x0 = (P["CENTER_OD"]/2 - 1) * math.cos(a)
        y0 = (P["CENTER_OD"]/2 - 1) * math.sin(a)
        x1 = (P["CENTER_OD"]/2 - 1 + P["TRI_SUPPORT_LEN"]) * math.cos(a)
        y1 = (P["CENTER_OD"]/2 - 1 + P["TRI_SUPPORT_LEN"]) * math.sin(a)
        ax.plot([x0, x1], [y0, y1], color=COL_BRACKET,
                 linewidth=P["TRI_SUPPORT_W"] * 1.4,
                 solid_capstyle="round", zorder=8)
        # 末端铆钉
        ax.add_patch(patches.Circle((x1, y1), P["TRI_KNOB_D"]/2,
                                      facecolor="#222", edgecolor=COL_BRACKET,
                                      linewidth=0.4, zorder=9))


def _draw_center_lens(ax, label=True):
    """中央白亮圆 + 摄像头开窗。"""
    ax.add_patch(patches.Circle((0, 0), P["CENTER_OD"]/2,
                                  facecolor=COL_CENTER, edgecolor="#888",
                                  linewidth=0.6, zorder=6))
    # 摄像头开窗
    ax.add_patch(patches.Circle((0, 0), P["CAM_HOLE_D"]/2,
                                  facecolor="#1a1a1a",
                                  edgecolor="#000", linewidth=1.0, zorder=7))
    if label:
        ax.text(0, 0, "CAM", color="#fff", ha="center", va="center",
                fontsize=7, fontweight="bold", zorder=8)


def _draw_magnet_array(ax, dashed=False):
    style = dict(facecolor="none", edgecolor=COL_MAGNET,
                  linewidth=1.2,
                  linestyle="--" if dashed else "-")
    fill = dict(facecolor=COL_MAGNET, edgecolor="#5a5d61", linewidth=0.8)
    ax.add_patch(patches.Circle((0, 0), P["MAG_C_D"]/2,
                                  **(style if dashed else fill)))
    if not dashed:
        ax.text(0, 0, f"N52\nΦ{int(P['MAG_C_D'])}×{int(P['MAG_C_T'])}",
                ha="center", va="center", fontsize=7)
    for ang in (0, 90, 180, 270):
        cx = P["MAG_E_R"] * math.cos(math.radians(ang))
        cy = P["MAG_E_R"] * math.sin(math.radians(ang))
        ax.add_patch(patches.Circle((cx, cy), P["MAG_E_D"]/2,
                                      **(style if dashed else fill)))


def _draw_usbc_slot(ax):
    usbc_x = 18
    usbc_y = P["USBC_OFFSET_Y"]
    ax.add_patch(patches.Rectangle(
        (usbc_x - P["USBC_W"]/2, usbc_y - P["USBC_H"]/2),
        P["USBC_W"], P["USBC_H"],
        facecolor=COL_USBC, edgecolor=COL_USBC))


def _draw_vent_holes(ax):
    n = int(P["VENT_HOLE_COUNT"])
    for i in range(n):
        # 外圈
        a1 = math.radians(360 * i / n)
        ax.add_patch(patches.Circle(
            (P["VENT_HOLE_R2"] * math.cos(a1),
             P["VENT_HOLE_R2"] * math.sin(a1)),
            P["VENT_HOLE_D"]/2,
            facecolor="none", edgecolor="#888", linewidth=0.7))
        # 内圈（错位 15°）
        a2 = math.radians(360 * i / n + 15)
        ax.add_patch(patches.Circle(
            (P["VENT_HOLE_R1"] * math.cos(a2),
             P["VENT_HOLE_R1"] * math.sin(a2)),
            P["VENT_HOLE_D"]/2,
            facecolor="none", edgecolor="#888", linewidth=0.7))


def _draw_pcb_outline(ax):
    ax.add_patch(patches.Circle((0, 0), P["PCB_OD"]/2,
                                  facecolor=COL_PCB, alpha=0.55,
                                  edgecolor="#054924", linewidth=0.8))


def _draw_battery(ax):
    bw, bh = P["BAT_W"], P["BAT_H"]
    gap = P["BAT_GAP"]
    for sign in (-1, +1):
        x0 = sign * (bw/2 + gap/2) - bw/2
        ax.add_patch(patches.Rectangle((x0, -bh/2), bw, bh,
                                        facecolor=COL_BAT, alpha=0.85,
                                        edgecolor="#222"))
        ax.text(x0 + bw/2, 0, "1500\nmAh", color="#fff",
                ha="center", va="center", fontsize=7)


# ---------------------------------------------------------------------------
# 5) 顶视图（Z+ 朝外）
# ---------------------------------------------------------------------------
def render_top(ax):
    ax.set_aspect("equal")
    R = P["TOTAL_OD"] / 2 + 8
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)

    # 背景圆（暗色，让蓝光更突出）
    ax.add_patch(patches.Circle((0, 0), P["TOTAL_OD"]/2,
                                  facecolor="#222", edgecolor="none"))

    # ⑴ 最外银色金属圈
    _draw_outer_ring(ax)
    # ⑵ 外圈灯柱 + 银夹板
    _draw_outer_lights_and_brackets(ax)
    # ⑶ 内圈灯
    _draw_inner_lights_and_brackets(ax)
    # ⑷ 铜线圈
    _draw_copper_coils(ax)
    # ⑸ 中央亮圆 + Y 三支撞 + CAM
    _draw_tri_supports(ax)
    _draw_center_lens(ax)
    # ⑹ 透视：磁铁虚线 + USB-C
    _draw_magnet_array(ax, dashed=True)
    _draw_usbc_slot(ax)

    ax.set_title("① 顶视图（Z+ 朝观察者 · Mark I 圆形特斯拉款）",
                  fontsize=11, pad=8)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# 6) 侧视图爆炸（与之前一致 · 7 层结构）
# ---------------------------------------------------------------------------
def render_side_exploded(ax):
    layers = [
        ("① 前壳 + 铜线圈 + Y 三支撑",       COL_FRONT,    P["FRONT_SHELL_T"] + P["RING_BAND_T"], 2.5),
        ("② PMMA 扩散板",                    COL_BLUE,     P["DIFFUSER_T"],       3.0),
        ("③ LED 灯环 (16 颗双环)",           COL_CENTER,   P["LED_RING_T"],       2.5),
        ("④ 主控 PCB (圆形, 双麦+3NTC+ADS1115+SY8088)", COL_PCB,  P["PCB_T"],            2.5),
        ("⑤ 双 2000 mAh 电池 (4000 mAh 总)", COL_BAT,      P["BATTERY_T"],        2.0),
        ("⑤a ☆ TIM 导热硅胶垫 (k=5)",        "#f1c40f",    P["TIM_PAD_T"],        5.0),
        ("⑤b ☆ 25 μm 石墨烯散热膜 (k=1500)", "#2c3e50",    P["GRAPHENE_T"],     120.0),
        ("⑤c ☆ Gore-Tex 防风膜+PORON 海绵",  "#aaaaaa",    P["WIND_FOAM_T"] + 0.05, 5.0),
        ("⑥ 后壳 PETG + 5 颗磁铁 + 双麦孔",  COL_BACK,     P["BACK_SHELL_T"],     2.5),
        ("⑦ 0.5 mm 硅胶贴肤垫 (含麦孔)",     COL_SILICON,  P["SILICON_PAD_T"],    4.0),
    ]
    nominal_total = sum(t for _, _, t, _ in layers)

    # ---- 爆炸视图：累加间距 ----
    explode_gap = 6.0
    z_cursor = 0.0
    z_marks = []
    for label, color, t, vscale in layers:
        h = t * vscale
        z0 = z_cursor - h
        z_marks.append((label, z0, h, t, color))
        z_cursor = z0 - explode_gap

    # ---- 装配视图：紧贴 ×3 放大 ----
    SCALE = 3.0
    asm_top = (nominal_total * SCALE) / 2 + 2
    nominal_marks = []
    asm_cursor = asm_top
    for label, color, t, _ in layers:
        h = t * SCALE
        z0 = asm_cursor - h
        nominal_marks.append((label, z0, h, color))
        asm_cursor = z0

    max_w = P["TOTAL_OD"] / 2 + 5

    ax.set_aspect("auto")
    ax.set_xlim(-max_w - 36, max_w + 80)
    ax.set_ylim(z_marks[-1][1] - 10, 16)

    for label, z0, h, t_real, color in z_marks:
        ax.add_patch(patches.Rectangle(
            (-P["TOTAL_OD"]/2, z0), P["TOTAL_OD"], h,
            facecolor=color, edgecolor="#222", linewidth=0.7))
        ax.text(-P["TOTAL_OD"]/2 - 3, z0 + h/2, label,
                ha="right", va="center", fontsize=9)
        if t_real >= 0.1:
            t_str = f"{t_real:.2f} mm"
        else:
            t_str = f"{t_real * 1000:.0f} \u03bcm"
        ax.text(P["TOTAL_OD"]/2 + 3, z0 + h/2, t_str,
                ha="left", va="center", fontsize=8, color="#666")

    ax.text(0, 10, "爆炸视图（沿 Z 轴拆解 · 厚度按显示放大）",
            ha="center", va="center", fontsize=10, fontweight="bold")

    asm_x = max_w + 36
    asm_w = 24
    for label, z0, h, color in nominal_marks:
        ax.add_patch(patches.Rectangle(
            (asm_x, z0), asm_w, h,
            facecolor=color, edgecolor="#222", linewidth=0.5))

    asm_real_top = nominal_marks[0][1] + nominal_marks[0][2]
    asm_real_bot = nominal_marks[-1][1]
    ax.annotate("", xy=(asm_x + asm_w + 4, asm_real_top),
                xytext=(asm_x + asm_w + 4, asm_real_bot),
                arrowprops=dict(arrowstyle="<->", color="#444", lw=1))
    ax.text(asm_x + asm_w + 6, (asm_real_top + asm_real_bot) / 2,
            f"装配厚度\n≈ {nominal_total:.1f} mm",
            ha="left", va="center", fontsize=9)
    ax.text(asm_x + asm_w/2, asm_real_top + 2, "装配视图",
            ha="center", va="bottom", fontsize=10, fontweight="bold")

    ax.set_title("② 侧视图爆炸（Z+ 朝上 · 7 层叠层结构）",
                  fontsize=11, pad=10)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_visible(False)


# ---------------------------------------------------------------------------
# 7) 背视图
# ---------------------------------------------------------------------------
def render_back(ax):
    ax.set_aspect("equal")
    R = P["TOTAL_OD"] / 2 + 8
    ax.set_xlim(-R, R)
    ax.set_ylim(-R, R)

    # 后壳（黑色圆盘）
    ax.add_patch(patches.Circle((0, 0), P["TOTAL_OD"]/2,
                                  facecolor=COL_BACK,
                                  edgecolor="#000", linewidth=1.5))

    _draw_magnet_array(ax, dashed=False)
    _draw_usbc_slot(ax)
    ax.text(18 + 8, P["USBC_OFFSET_Y"], "USB-C", color="#fff",
            ha="left", va="center", fontsize=8)
    _draw_vent_holes(ax)
    ax.text(0, 36, "↓ 透气孔双圈阵列（Ø1.5 ×24）↓", color="#bbb",
            ha="center", va="center", fontsize=7)

    # ★ 双麦克风开孔 + 防风罩
    for label, pos_key in (("MIC_A", "MIC_A_POS"), ("MIC_B", "MIC_B_POS")):
        # 直接读取数组形式参数比较麻烦，硬编码相对位置
        pass
    for x, y, label in ((0, 28, "MIC_A\n(主)"), (0, -28, "MIC_B\n(副)")):
        # 防风罩外圈（Gore-Tex 区域）
        ax.add_patch(patches.Circle((x, y), P["WIND_FILM_D"]/2,
                                      facecolor="#ddd", edgecolor="#888",
                                      linewidth=0.8, alpha=0.5))
        # 实际开孔
        ax.add_patch(patches.Circle((x, y), P["MIC_HOLE_D"]/2,
                                      facecolor="#000", edgecolor="#444",
                                      linewidth=0.6))
        ax.text(x + 7, y, label, color="#fff", ha="left", va="center",
                fontsize=7)

    ax.add_patch(patches.Circle((0, 0), P["MAG_C_D"]/2 + 2,
                                  facecolor="none", edgecolor="#666",
                                  linestyle=":", linewidth=0.8))

    ax.text(0, 12, "中央：S 极朝外", ha="center", va="center",
            fontsize=7, color="#fff")
    for ang in (0, 90, 180, 270):
        cx = (P["MAG_E_R"] + 5) * math.cos(math.radians(ang))
        cy = (P["MAG_E_R"] + 5) * math.sin(math.radians(ang))
        ax.text(cx, cy, "N", fontsize=8, color="#fff",
                ha="center", va="center", fontweight="bold")

    ax.set_title("③ 背视图（Z- 朝观察者 · Halbach 磁吸 + USB-C + 透气孔）",
                  fontsize=11, pad=8)
    ax.set_xlabel("X (mm)")
    ax.set_ylabel("Y (mm)")
    ax.grid(True, alpha=0.3)


# ---------------------------------------------------------------------------
# 8) 9 件单件平铺
# ---------------------------------------------------------------------------
def _setup_part_axes(ax, title, w, h):
    ax.set_aspect("equal")
    ax.set_xlim(-w/2 - 4, w/2 + 4)
    ax.set_ylim(-h/2 - 4, h/2 + 4)
    ax.set_title(title, fontsize=9.5, pad=4)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#aaa")
        spine.set_linewidth(0.5)


def render_parts(fig):
    gs = fig.add_gridspec(3, 3, hspace=0.35, wspace=0.18)

    # ① 前壳（同心环骨架，无铜线圈/支撞）
    ax = fig.add_subplot(gs[0, 0])
    _setup_part_axes(ax, "① 前壳 (银色 ABS · 4 同心环骨架)",
                      P["TOTAL_OD"] + 4, P["TOTAL_OD"] + 4)
    ax.add_patch(patches.Circle((0, 0), P["TOTAL_OD"]/2,
                                  facecolor="#222"))
    _draw_outer_ring(ax)
    # 灯柱开窗（透色，仅看骨架）
    n = int(P["OUTER_LIGHT_COUNT"])
    for i in range(n):
        # 夹板
        b_center = 360 * i / n + 360 / n / 2
        bracket_arc = 360 / n - P["OUTER_LIGHT_ARC"]
        _wedge(ax, P["OUTER_LIGHT_OD"], P["OUTER_LIGHT_ID"],
                b_center - bracket_arc/2, b_center + bracket_arc/2,
                facecolor=COL_BRACKET, edgecolor="#5a5d61", linewidth=0.4)
        # 内骨架
        b2 = 360 * i / n
        _wedge(ax, P["INNER_LIGHT_OD"], P["INNER_LIGHT_ID"],
                b2 - 9, b2 + 9,
                facecolor=COL_BRACKET, edgecolor="#5a5d61", linewidth=0.4)
    # 中圈线圈底座
    _ring(ax, P["INNER_BAND_OD"], P["INNER_BAND_ID"],
           facecolor=COL_FRONT, edgecolor="#5a5d61", linewidth=0.6)
    ax.add_patch(patches.Circle((0, 0), P["CAM_HOLE_D"]/2,
                                  facecolor="white"))

    # ② PMMA 扩散板
    ax = fig.add_subplot(gs[0, 1])
    _setup_part_axes(ax, "② PMMA 蓝光扩散板（双环）",
                      P["OUTER_LIGHT_OD"] + 4, P["OUTER_LIGHT_OD"] + 4)
    _ring(ax, P["OUTER_LIGHT_OD"] - 1, P["OUTER_LIGHT_ID"] + 1,
           facecolor=COL_BLUE, edgecolor=COL_BLUE_DK,
           linewidth=0.5, alpha=0.7)
    _ring(ax, P["INNER_LIGHT_OD"] - 1, P["INNER_LIGHT_ID"] + 1,
           facecolor=COL_BLUE, edgecolor=COL_BLUE_DK,
           linewidth=0.5, alpha=0.7)

    # ③ 8 个铜线圈
    ax = fig.add_subplot(gs[0, 2])
    _setup_part_axes(ax, "③ 8 个铜线圈（特斯拉风格装饰）",
                      P["INNER_BAND_OD"] + 4, P["INNER_BAND_OD"] + 4)
    _ring(ax, P["INNER_BAND_OD"], P["INNER_BAND_ID"],
           facecolor="none", edgecolor="#888",
           linewidth=0.5, linestyle=":")
    _draw_copper_coils(ax)

    # ④ Y 字 3 支撞 + 中央亮圆
    ax = fig.add_subplot(gs[1, 0])
    _setup_part_axes(ax, "④ Y 字三支撞 + 中央 PMMA 亮圆",
                      P["INNER_LIGHT_OD"] + 8, P["INNER_LIGHT_OD"] + 8)
    _ring(ax, P["INNER_LIGHT_OD"], P["INNER_LIGHT_ID"],
           facecolor="none", edgecolor="#888",
           linewidth=0.5, linestyle=":")
    _draw_tri_supports(ax)
    _draw_center_lens(ax)

    # ⑤ LED 灯环（双同心环 16 颗）
    ax = fig.add_subplot(gs[1, 1])
    _setup_part_axes(ax, "⑤ LED 灯环 FPC（外8 + 内8 = 16 颗 WS2812B）",
                      P["OUTER_LIGHT_OD"] + 4, P["OUTER_LIGHT_OD"] + 4)
    ax.add_patch(patches.Circle((0, 0), P["OUTER_LIGHT_OD"]/2,
                                  facecolor="#f5f5f5", edgecolor="#666"))
    ax.add_patch(patches.Circle((0, 0), P["CAM_HOLE_D"]/2,
                                  facecolor="white", edgecolor="#666"))
    # 外圈 8 颗
    for i in range(int(P["LED_OUTER_COUNT"])):
        a = 2 * math.pi * i / P["LED_OUTER_COUNT"]
        x = P["LED_OUTER_R"] * math.cos(a)
        y = P["LED_OUTER_R"] * math.sin(a)
        ax.add_patch(patches.Rectangle(
            (x - P["LED_PIXEL_S"]/2, y - P["LED_PIXEL_S"]/2),
            P["LED_PIXEL_S"], P["LED_PIXEL_S"],
            facecolor="white", edgecolor="#888"))
    # 内圈 8 颗
    for i in range(int(P["LED_INNER_COUNT"])):
        a = 2 * math.pi * i / P["LED_INNER_COUNT"] + math.pi/8
        x = P["LED_INNER_R"] * math.cos(a)
        y = P["LED_INNER_R"] * math.sin(a)
        ax.add_patch(patches.Rectangle(
            (x - P["LED_PIXEL_S"]/2, y - P["LED_PIXEL_S"]/2),
            P["LED_PIXEL_S"], P["LED_PIXEL_S"],
            facecolor="white", edgecolor="#888"))

    # ⑥ 主控 PCB
    ax = fig.add_subplot(gs[1, 2])
    _setup_part_axes(ax, "⑥ 主控 PCB (Φ80 mm 圆形)",
                      P["PCB_OD"] + 6, P["PCB_OD"] + 6)
    _draw_pcb_outline(ax)
    ax.add_patch(patches.Circle((0, 0), 4.25,
                                  facecolor="#222", edgecolor="#000"))
    ax.text(0, 0, "OV5640", color="#fff", ha="center", va="center",
            fontsize=6.5)
    ax.add_patch(patches.Rectangle((-9, -12.75), 18, 25.5,
                                     facecolor="none", edgecolor="#888",
                                     linestyle="--"))
    ax.text(0, 0 - 18, "ESP32-S3\n(背面)", ha="center", va="center",
            fontsize=6.5)

    # ⑦ 双电池
    ax = fig.add_subplot(gs[2, 0])
    _setup_part_axes(ax, "⑦ 双 2000 mAh 锂聚（并联 = 4000 mAh）",
                      80, 60)
    _draw_battery(ax)

    # ⑧ 后壳 + 磁铁 + USB-C + 透气孔
    ax = fig.add_subplot(gs[2, 1])
    _setup_part_axes(ax, "⑧ 后壳 (PETG · 5 磁吸卡位 + USB-C + 24 透气孔)",
                      P["TOTAL_OD"] + 4, P["TOTAL_OD"] + 4)
    ax.add_patch(patches.Circle((0, 0), P["TOTAL_OD"]/2,
                                  facecolor=COL_BACK, edgecolor="#000"))
    _draw_magnet_array(ax, dashed=False)
    _draw_usbc_slot(ax)
    _draw_vent_holes(ax)

    # ⑨ 硅胶贴肤层
    ax = fig.add_subplot(gs[2, 2])
    _setup_part_axes(ax, "⑨ 0.5 mm 硅胶贴肤层",
                      P["TOTAL_OD"] + 4, P["TOTAL_OD"] + 4)
    ax.add_patch(patches.Circle((0, 0), (P["TOTAL_OD"] - 1)/2,
                                  facecolor=COL_SILICON, edgecolor="#000",
                                  alpha=0.7))
    _draw_magnet_array(ax, dashed=True)
    _draw_usbc_slot(ax)


# ---------------------------------------------------------------------------
# 9) 总览大图
# ---------------------------------------------------------------------------
def render_overview():
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.18, wspace=0.12,
                          top=0.94, bottom=0.04, left=0.04, right=0.97)

    ax_top = fig.add_subplot(gs[0, 0])
    render_top(ax_top)

    ax_back = fig.add_subplot(gs[0, 1])
    render_back(ax_back)

    ax_side = fig.add_subplot(gs[1, 0])
    render_side_exploded(ax_side)

    ax_info = fig.add_subplot(gs[1, 1])
    ax_info.axis("off")
    info_text = (
        "InstaFreeHeart · 方案 A · Mark I 圆形特斯拉款 (v2)\n"
        "─────────────────────────────────────────\n"
        f"  外形       :  Ø{int(P['TOTAL_OD'])} × "
        f"{int(P['TOTAL_THK'])} mm  (圆盘)\n"
        f"  整机重量    :  136 g  (含电池+散热+降噪辅件)\n"
        f"  ★ 电池     :  4000 mAh  (2× 2000 mAh 软包并联)\n"
        f"  电池保护    :  DW01A + 8205A\n"
        f"  ★ 3V3 电源 :  SY8088 Buck (η=92%, 取代 LDO)\n"
        f"  MCU        :  ESP32-S3-WROOM-1-N16R8\n"
        f"  ★ 摄像头   :  OV5640 (DVP 500W 像素 + 硬件 HDR)\n"
        f"  ★ 麦克风   :  双 INMP441 (立体声差分降噪)\n"
        f"  灯环        :  WS2812B-2020 × 16  (双同心环 8+8)\n"
        f"  铜线圈      :  8 颗 SLA 装饰件\n"
        f"  ☆ 温度采集 :  ADS1115 + 3× NTC 10K B3950\n"
        f"  ☆ 散热升级 :  石墨烯 25μm + 导热硅胶垫 0.5mm\n"
        f"  ☆ 降噪升级 :  Gore-Tex 防风膜 + PORON 海绵 + WebRTC NSx\n"
        f"  存储        :  microSD TF 卡\n"
        f"  接口        :  USB-C 充电 + 5V 输出\n"
        f"  磁吸        :  Halbach (Φ22 中央 + 4× Φ8 周边)\n"
        f"  贴衣拉力    :  ≈ 2.4 kg  (安全系数 2.2×)\n"
        f"  ★ 皮肤温度 :  正常 38℃ / 最坏 40.7℃  (限功率后)\n"
        f"  ★ 续航纯日记:  5.3-7.1 天连续\n"
        f"  ★ 续航高强度:  9.8-13 h 连续 (达 12h 目标)\n"
        f"  充手机      :  iPhone ~65% × 1 次\n"
        f"  整机 BOM   :  ≈ ¥133 / 台\n"
    )
    ax_info.text(0.02, 0.98, info_text,
                  fontsize=11, va="top", ha="left",
                  linespacing=1.55)
    ax_info.set_title("④ 整机参数速查", fontsize=11, pad=8, loc="left")

    fig.suptitle(
        "InstaFreeHeart · Mark I 圆形特斯拉款 · 4 视图设计预览",
        fontsize=15, fontweight="bold", y=0.985,
    )
    fig.savefig(OUT / "preview_overview.png", dpi=170,
                bbox_inches="tight")
    plt.close(fig)


# ---------------------------------------------------------------------------
# 10) 单独输出
# ---------------------------------------------------------------------------
def render_single(fname, render_fn, figsize=(9, 10)):
    fig, ax = plt.subplots(figsize=figsize)
    render_fn(ax)
    fig.savefig(OUT / fname, dpi=170, bbox_inches="tight")
    plt.close(fig)


def render_parts_grid():
    fig = plt.figure(figsize=(15, 14))
    fig.suptitle("InstaFreeHeart · Mark I 圆形 · 9 件拆解视图",
                  fontsize=14, fontweight="bold", y=0.985)
    render_parts(fig)
    fig.savefig(OUT / "preview_parts.png", dpi=170, bbox_inches="tight")
    plt.close(fig)


def main():
    render_single("preview_top.png", render_top, (10, 10))
    render_single("preview_back.png", render_back, (10, 10))
    render_single("preview_side.png", render_side_exploded, (12, 8))
    render_parts_grid()
    render_overview()
    print("[OK] 已生成：")
    for f in ("preview_overview.png", "preview_top.png", "preview_back.png",
              "preview_side.png", "preview_parts.png"):
        path = OUT / f
        print(f"  {path}  ({path.stat().st_size/1024:.0f} KB)")


if __name__ == "__main__":
    main()
