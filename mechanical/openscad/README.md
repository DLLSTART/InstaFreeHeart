# InstaFreeHeart · OpenSCAD 3D 模型

参数化的 3D 模型，配合 `mechanical/3d_design.md` 中的设计思路。

## 顶视图预览

![InstaFreeHeart 顶视图](out/preview.png)

> 上图由 `preview.py` 用 matplotlib 直接从 `parameters.scad` 读参数生成，
> 无需 OpenSCAD 也能先看到设计效果。
>
> 调整 `parameters.scad` 后，重跑 `python3 preview.py` 即可刷新这张图。

## 文件清单

| 文件 | 作用 |
|------|------|
| `parameters.scad` | 全局参数（尺寸、颜色、爆炸系数）— 调整这里就能改全机 |
| `instafreeheart.scad` | 全部模块定义 + 总装配（main entry，OpenSCAD 打开此文件） |
| `preview.py` | 用 matplotlib 把外形/磁铁/灯环画成顶视图 PNG/SVG（不需要 OpenSCAD） |
| `out/preview.png` `out/preview.svg` | preview.py 的输出 |
| `out/*.stl`（OpenSCAD F6 后生成） | 3D 打印用 STL |
| `README.md` | 当前文件 |

## 安装 OpenSCAD（macOS）

任选其一：

```bash
# 1. 官网安装包（推荐）
open https://openscad.org/downloads.html
# 下载 OpenSCAD-2021.01.dmg → 拖到 /Applications/

# 2. Homebrew Cask（如果 brew 可用）
brew install --cask openscad

# 3. 启用 CLI（命令行渲染需要）
echo 'export PATH="/Applications/OpenSCAD.app/Contents/MacOS:$PATH"' >> ~/.zshrc
source ~/.zshrc
openscad --version
```

## 快速预览

```bash
# 用 OpenSCAD 桌面应用打开
open -a OpenSCAD instafreeheart.scad

# 在 OpenSCAD 中：
#   F5  → 快速预览
#   F6  → 完整渲染（可导出 STL）
#   File → Export → Export as STL...
```

## 命令行批量渲染

```bash
# 渲染装配体的等轴侧视图
openscad -o out/assembly.png \
  --imgsize 1600,1200 \
  --camera 0,0,0,55,0,25,250 \
  --colorscheme=Tomorrow \
  instafreeheart.scad

# 导出整机 STL（用于 3D 打印）
openscad -o out/instafreeheart_assembly.stl instafreeheart.scad
```

## 单件导出（每个零件单独打印）

编辑 `instafreeheart.scad` 文件末尾的「单件导出」一节：

```scad
// ----- 把这一行注释掉 -----
// assembly();

// ----- 启用要导出的零件 -----
front_shell();        // 前壳（SLA / FDM 高精度）
// crown();           // 顶冠
// back_shell();      // 后壳（FDM PETG）
// diffuser();        // 扩散板（CNC PMMA）
// led_ring();        // 灯环 PCB（仅可视化，实际下嘉立创）
// main_pcb();        // 主控 PCB（仅可视化）
// silicon_pad();     // 硅胶垫（CNC 切割）
```

然后：`F6 → File → Export → STL`。

## 切换爆炸视图

修改 `parameters.scad`：

```scad
EXPLODE = 0;     // 0 = 装配体（默认）
EXPLODE = 8;     // 中等爆炸
EXPLODE = 18;    // 完全分散，便于看每个零件
```

## 设计要点速览（对应 `mechanical/3d_design.md`）

```
Z+ (朝外)
   ┌──────────────┐
   │  ① 前壳       │  色: 银  · linear_extrude(diamond) - grid - hex_pattern
   │  + 顶冠       │  色: 金
   ├──────────────┤
   │  ② 扩散板     │  色: 半透蓝
   │  ③ LED 灯环   │  16 颗 ws2812B 圆周等分
   │  ④ 主控 PCB   │  色: 嘉立创深绿，顶面有摄像头模组
   │  ⑤ 双电池     │  左右对称，中间留 PCB 元件区
   │  ⑥ 后壳       │  色: 黑，含 5 颗磁铁卡位 + USB-C 开槽 + 透气孔
   │  ⑦ 硅胶垫     │  色: 半透黑，按外形冲切
   └──────────────┘
Z- (贴胸)
```

## 已实现的几何特征

- ✅ 钻石外形（17 顶点 polygon，可视化贴近参考图）
- ✅ 内部主十字 + 4 条对角支撑格栅
- ✅ 蜂窝纹理凹刻（hex pattern，0.6 mm 深）
- ✅ 中央 I 字形扩散区（参考图蓝光形状）
- ✅ LED 灯环 16 颗等距分布 + 中央摄像头开窗
- ✅ Halbach 磁吸阵列（中央 Φ22 + 4× Φ8 周边）
- ✅ USB-C 底尖侧方开槽
- ✅ 后壳透气孔阵列（避开磁铁正下方）
- ✅ 中央磁铁背面补强环
- ✅ 全部模块独立 module，可单独导出 STL

## 常见调整示例

```scad
// 改电池方案为 4000 mAh（方案 B）
BATTERY_T = 8.0;        // 电池厚度 +2mm
TOTAL_THK = 16;         // 整机厚度 +2mm

// 改磁吸为单中心磁铁（方案 C）
MAG_E_R = 0;           // 周边磁铁半径置零（重叠到中心，等于不存在）
// 或者修改 magnet_array() 删除 for 循环

// 调整钻石形比例（更扁/更长）
BODY_W = 100;           // 横向 +10
BODY_H = 60;            // 纵向 -5
```

## 后续可加的细节（按需）

- [ ] 主板上的 USB-C 沉板让位（PCB 边缘倒角）
- [ ] 顶冠的金色铆钉细节（小圆柱浮雕）
- [ ] 扩散板边缘抛光斜角（45° chamfer）
- [ ] 后壳 R200 球面贴胸曲率（用 `sphere(r=200)` intersection）
- [ ] 螺丝柱（M2 沉头螺丝定位）
