#!/usr/bin/env bash
# =============================================================================
# InstaFreeHeart · OpenSCAD 整体预览渲染（OpenSCAD 2021.01 命令行）
# -----------------------------------------------------------------------------
# 输出（写入 out/）：
#   render_iso.png       等距视图（60°/0°/30°）— 整机装配
#   render_top.png       正视图（顶面，Z+ 朝外）
#   render_back.png      背视图（Z- 朝外）
#   render_side.png      侧视图（X+ 方向）
#   render_explode.png   等距爆炸视图（EXPLODE=8 mm）
#   render_grid.png      由 ImageMagick 拼接的 4 视图大图
# -----------------------------------------------------------------------------
# camera 参数格式（gimbal）：
#   --camera=tx,ty,tz,rx,ry,rz,dist
#     tx/ty/tz : 视点平移
#     rx/ry/rz : 绕坐标轴旋转（°）
#     dist     : 摄像机距离
# =============================================================================
set -euo pipefail

HERE=$(cd "$(dirname "$0")" && pwd)
OUT="$HERE/out"
SCAD="$HERE/instafreeheart.scad"
SIZE=1600,1200
DARK="Tomorrow Night"
LIGHT="Cornfield"

mkdir -p "$OUT"

# tx,ty,tz,rx,ry,rz,dist
CAM_ISO="0,0,-15,55,0,25,260"     # 等距俯视
CAM_TOP="0,0,0,0,0,0,260"          # 顶视（Z+ 朝外）
CAM_BACK="0,0,-15,180,0,0,260"     # 背视（Z- 朝外，下移 15 让结构居中）
CAM_SIDE="0,0,-15,90,0,0,260"      # 侧视（X+ 朝外）
CAM_EXPLODE="0,0,-30,55,0,25,420"  # 爆炸视图距离更远

echo "[1/5] 等距装配视图（暗背景）..."
openscad -o "$OUT/render_iso.png" \
    --imgsize=$SIZE --projection=p \
    --camera=$CAM_ISO --colorscheme="$DARK" \
    "$SCAD"

echo "[2/5] 顶视图（暗背景，蓝光更突出）..."
openscad -o "$OUT/render_top.png" \
    --imgsize=$SIZE --projection=o \
    --camera=$CAM_TOP --colorscheme="$DARK" \
    "$SCAD"

echo "[3/5] 背视图（亮背景，黑后壳更清晰）..."
openscad -o "$OUT/render_back.png" \
    --imgsize=$SIZE --projection=o \
    --camera=$CAM_BACK --colorscheme="$LIGHT" \
    "$SCAD"

echo "[4/5] 侧视图（亮背景，看 7 层叠层结构）..."
openscad -o "$OUT/render_side.png" \
    --imgsize=$SIZE --projection=o \
    --camera=$CAM_SIDE --colorscheme="$LIGHT" \
    "$SCAD"

echo "[5/5] 爆炸视图（亮背景，看分层装配）..."
openscad -o "$OUT/render_explode.png" \
    -D 'EXPLODE=8' \
    --imgsize=$SIZE --projection=p \
    --camera=$CAM_EXPLODE --colorscheme="$LIGHT" \
    "$SCAD"

echo "[OK] 已生成："
for f in render_iso.png render_top.png render_back.png render_side.png render_explode.png; do
    p="$OUT/$f"
    sz=$(stat -f '%z' "$p" 2>/dev/null || stat -c '%s' "$p")
    echo "  $p  ($((sz/1024)) KB)"
done
