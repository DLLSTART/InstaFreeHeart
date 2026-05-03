#!/usr/bin/env bash
# =============================================================================
# InstaFreeHeart · STL 批量导出（OpenSCAD CGAL 渲染 → 可送切片器）
# -----------------------------------------------------------------------------
# 输出（写入 stl/）：
#   front_shell.stl   ← FDM 银色 PETG / ABS（外壳主体，含 8 段灯柱开窗）
#   back_shell.stl    ← FDM 黑色 PETG（含磁铁卡位、USB-C 槽、麦孔、透气孔）
#   tri_supports.stl  ← 可与前壳合并打印；这里作为单独件预备
#   copper_coil.stl   ← SLA 树脂 + 喷涂铜色（单颗，下单 8 份）
#
# 不在此处导出（采购件 / 注塑件 / 软体件 / PCB）：
#   center_lens / diffuser  ← PMMA 注塑（透明，FDM 难做）
#   led_ring / main_pcb     ← 嘉立创 PCB 下单
#   battery / magnets       ← 采购件
#   silicon_pad             ← 0.5 mm 硅胶片裁切
#   graphene_film / tim_pad ← 散热辅料裁切
# -----------------------------------------------------------------------------
# 用法：
#   bash mechanical/openscad/export_stl.sh
# =============================================================================
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
SCAD="$HERE/instafreeheart.scad"
STL_DIR="$HERE/stl"

mkdir -p "$STL_DIR"

# 单个零件导出函数
# $1 = PART 变量值
# $2 = 输出文件名（不含路径）
export_part() {
    local part="$1"
    local out_name="$2"
    local out_path="$STL_DIR/$out_name"
    echo "[export] PART=$part → $out_name"
    openscad -o "$out_path" -D "PART=\"$part\"" \
        --export-format=binstl "$SCAD" 2>&1 \
        | grep -E "(rendering time|elements|ERROR|WARNING)" || true
    if [ -f "$out_path" ]; then
        local sz
        sz=$(stat -f '%z' "$out_path" 2>/dev/null || stat -c '%s' "$out_path")
        echo "         ✓ $((sz/1024)) KB"
    else
        echo "         ✗ 失败！"
        exit 1
    fi
}

echo "=========================================================="
echo "  InstaFreeHeart · OpenSCAD STL 批量导出"
echo "=========================================================="

export_part "front"   "front_shell.stl"
export_part "back"    "back_shell.stl"
export_part "tri"     "tri_supports.stl"
export_part "coil"    "copper_coil_x1.stl"

echo "----------------------------------------------------------"
echo "  全部导出完成。可直接拖入切片器（PrusaSlicer / Bambu"
echo "  Studio / Lychee 等）。打印参数请见："
echo "    mechanical/3d_print_guide.md"
echo "=========================================================="
ls -la "$STL_DIR/"
