"""
将 OpenSCAD 渲染出的 5 张 PNG 拼接成一张总览大图。
布局（2×2）：
   ┌─────────────────┬─────────────────┐
   │  ① 等距装配     │  ② 顶视图        │
   ├─────────────────┼─────────────────┤
   │  ③ 爆炸视图     │  ④ 侧视图 + 背视 │
   └─────────────────┴─────────────────┘
"""
from __future__ import annotations

from pathlib import Path

import matplotlib
import matplotlib.image as mpimg
import matplotlib.pyplot as plt

for f in ("PingFang SC", "Songti SC", "Heiti SC", "STHeiti",
          "Hiragino Sans GB", "Arial Unicode MS"):
    try:
        matplotlib.font_manager.findfont(f, fallback_to_default=False)
        matplotlib.rcParams["font.sans-serif"] = [f] + matplotlib.rcParams[
            "font.sans-serif"]
        matplotlib.rcParams["axes.unicode_minus"] = False
        break
    except Exception:
        continue


HERE = Path(__file__).resolve().parent
OUT = HERE / "out"


def add_panel(ax, img_path, title, dark_bg=False):
    img = mpimg.imread(img_path)
    ax.imshow(img)
    ax.set_title(title, fontsize=13, fontweight="bold",
                  color="#1a1a1a", pad=6)
    ax.set_xticks([])
    ax.set_yticks([])
    for spine in ax.spines.values():
        spine.set_color("#888" if not dark_bg else "#444")
        spine.set_linewidth(0.8)


def main():
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(2, 2, hspace=0.10, wspace=0.05,
                          top=0.92, bottom=0.04, left=0.02, right=0.98)

    add_panel(fig.add_subplot(gs[0, 0]),
              OUT / "render_iso.png",
              "① 等距装配视图（透视，Tomorrow Night 配色）",
              dark_bg=True)
    add_panel(fig.add_subplot(gs[0, 1]),
              OUT / "render_top.png",
              "② 顶视图（正交，Z+ 朝外，Mark I 圆形特斯拉款）",
              dark_bg=True)
    add_panel(fig.add_subplot(gs[1, 0]),
              OUT / "render_explode.png",
              "③ 爆炸视图（EXPLODE=8，Z 方向 7 层叠层）")
    add_panel(fig.add_subplot(gs[1, 1]),
              OUT / "render_side.png",
              "④ 侧视图（正交，X+ 朝外，整机厚度 15 mm）")

    fig.suptitle(
        "InstaFreeHeart · OpenSCAD 整体预览（Mark I 圆形 · Ø90 × 15 mm · 136 g · 4000 mAh）",
        fontsize=17, fontweight="bold", y=0.975)

    out_path = OUT / "render_overview_4view.png"
    fig.savefig(out_path, dpi=120, bbox_inches="tight",
                facecolor="white")
    plt.close(fig)
    print(f"[OK] {out_path}  ({out_path.stat().st_size / 1024:.0f} KB)")


if __name__ == "__main__":
    main()
