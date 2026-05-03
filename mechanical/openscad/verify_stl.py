"""
快速校验 STL 文件：
  - 文件可读、binary STL 头部合法
  - 三角面数
  - 轴对齐包围盒（AABB）尺寸 → 验证打印床/打印料盘尺寸
  - 估算实体体积（带符号体积法）→ 估算打印材料用量与重量
"""
from __future__ import annotations

import struct
import sys
from pathlib import Path


HERE = Path(__file__).resolve().parent
STL_DIR = HERE / "stl"

# 材料密度 (g/cm³)，用于体积 → 重量估算
DENSITY = {
    "front_shell.stl":      1.27,   # PETG  ~1.27
    "back_shell.stl":       1.27,   # PETG
    "tri_supports.stl":     1.27,   # PETG
    "copper_coil_x1.stl":   1.18,   # 标准 SLA 树脂
}


def read_stl_binary(p: Path):
    with p.open("rb") as f:
        header = f.read(80)
        n = struct.unpack("<I", f.read(4))[0]
        verts_min = [float("inf")] * 3
        verts_max = [float("-inf")] * 3
        signed_volume = 0.0
        for _ in range(n):
            f.read(12)  # 法向量
            tri = struct.unpack("<9f", f.read(36))
            f.read(2)   # attribute byte count
            v0 = tri[0:3]; v1 = tri[3:6]; v2 = tri[6:9]
            for v in (v0, v1, v2):
                for i in range(3):
                    if v[i] < verts_min[i]: verts_min[i] = v[i]
                    if v[i] > verts_max[i]: verts_max[i] = v[i]
            # 带符号四面体体积（顶点对原点）
            signed_volume += (
                v0[0] * (v1[1] * v2[2] - v2[1] * v1[2])
                - v1[0] * (v0[1] * v2[2] - v2[1] * v0[2])
                + v2[0] * (v0[1] * v1[2] - v1[1] * v0[2])
            ) / 6.0
        return n, verts_min, verts_max, abs(signed_volume)


def fmt_bbox(lo, hi):
    return (f"X[{lo[0]:7.2f} → {hi[0]:7.2f}]  Y[{lo[1]:7.2f} → {hi[1]:7.2f}]  "
            f"Z[{lo[2]:7.2f} → {hi[2]:7.2f}]")


def main():
    if not STL_DIR.exists():
        sys.exit(f"STL 目录不存在：{STL_DIR}")

    print("=" * 92)
    print(f"  InstaFreeHeart · STL 校验报告 ({STL_DIR})")
    print("=" * 92)
    print(f"  {'文件':<22}{'三角面':>8}  {'尺寸 (mm)':<60}{'体积':>10}{'重量*':>9}")
    print("-" * 92)

    total_w = 0.0
    for stl in sorted(STL_DIR.glob("*.stl")):
        n, lo, hi, vol_mm3 = read_stl_binary(stl)
        sx = hi[0] - lo[0]
        sy = hi[1] - lo[1]
        sz = hi[2] - lo[2]
        vol_cm3 = vol_mm3 / 1000.0
        density = DENSITY.get(stl.name, 1.27)
        # 100% 填充估算（FDM 默认 15-25% 填充时实际重量约为此值的 30%）
        weight_solid = vol_cm3 * density
        total_w += weight_solid
        print(f"  {stl.name:<22}{n:>8}  "
              f"Ø{max(sx, sy):5.1f} × {sz:5.1f}  ({sx:5.1f} × {sy:5.1f} × {sz:5.1f})"
              f"   {vol_cm3:>6.2f} cm³  {weight_solid:>5.1f} g")

    print("-" * 92)
    print(f"  * 重量按 100% 填充估算；FDM 实际打印（15% gyroid 填充）≈ 该值 × 0.30")
    print(f"    SLA 树脂打印（100% 实心）≈ 该值")
    print()
    print(f"  100% 实心总重：{total_w:.1f} g")
    print(f"  典型 FDM (15% 填充) 总重 ≈ {total_w * 0.30 + 6.0:.1f} g  "
          f"（含线圈 8× 实心）")
    print("=" * 92)


if __name__ == "__main__":
    main()
