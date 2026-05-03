# InstaFreeHeart · 3D 打印工艺参数指南

> 适用对象：所有 `mechanical/openscad/stl/` 目录下的 STL 文件
> 推荐切片器：PrusaSlicer 2.7+ / Bambu Studio 1.9+ / Lychee Slicer 6+

---

## 1. 总览

| 文件 | 工艺 | 推荐材料 | 预计耗时 | 单件重量 | 数量 |
| --- | --- | --- | --- | --- | --- |
| `front_shell.stl` | **FDM** | 银色 PETG | 1 h 20 min | ~4.5 g (15% 填充) | 1 |
| `back_shell.stl` | **FDM** | 哑黑 PETG | 1 h 10 min | ~4.5 g (15% 填充) | 1 |
| `tri_supports.stl` | **FDM** | 银色 PETG | 8 min | 0.2 g | 1（也可与前壳合打） |
| `copper_coil_x1.stl` | **SLA** | 标准灰树脂 + 铜色喷漆 | 35 min（堆 8 颗） | 0.13 g × 8 | 8 |

**总打印用料**：
- PETG：~10 g
- SLA 树脂：~1 g
- 总打印时间：~2 h 15 min（FDM 串行 + SLA 并行）

---

## 2. 生成 STL 流程

```bash
# 一次性导出全部 STL
bash mechanical/openscad/export_stl.sh

# 校验 STL（三角面数 / 包围盒 / 体积 / 重量）
python3 mechanical/openscad/verify_stl.py

# 单独导出某一件
openscad -o mechanical/openscad/stl/front_shell.stl \
    -D 'PART="front"' \
    --export-format=binstl \
    mechanical/openscad/instafreeheart.scad
```

可用的 `PART` 取值：`"all"` / `"front"` / `"back"` / `"tri"` / `"coil"`。

---

## 3. front_shell.stl — 前壳（FDM）

### 3.1 关键尺寸

| 参数 | 数值 | 容差要求 |
| --- | --- | --- |
| 外径 | Ø90.0 mm | ±0.2 mm（影响整机外观对齐） |
| 高度 | 4.0 mm（含夹板凸起） | ±0.1 mm |
| 中央摄像头开窗 | Ø12.0 mm | **+0.1 / -0.0**（OV5640 镜头筒过盈） |
| 8 段灯柱开窗 | 每段 30°，OD 78 / ID 60 | ±0.15 mm（用于嵌 PMMA 扩散板） |
| 8 段内灯开窗 | 每段 36°，OD 28 / ID 20 | ±0.15 mm |

### 3.2 切片器参数（PrusaSlicer / Bambu Studio）

| 参数 | 数值 | 说明 |
| --- | --- | --- |
| 喷嘴 | 0.4 mm | 标准黄铜喷嘴 |
| 层高 | **0.16 mm** | 平衡观感与速度（外圈刻面线条清晰） |
| 第一层层高 | 0.20 mm | 增强床面附着 |
| 喷头温度 | 240 ℃ | PETG 标准 |
| 热床温度 | 80 ℃ | PETG 防翘曲 |
| 顶/底层数 | 5 / 5 | 顶面要不透光 |
| 墙数 | **3** | 灯柱开窗边缘强度 |
| 填充率 | **15% gyroid** | 轻量化 + 各向异性 |
| 打印速度 | 50 mm/s（外壁 30 mm/s） | 外观面降速保证锐度 |
| 支撑 | **不需要**（朝下打印） | 把 Y 字三支撑那一面朝床面 |
| 床面附着 | brim 5 mm | 防止圆形件翘边 |
| 风扇 | 100% (除第一层) | PETG 必须强冷 |

### 3.3 摆放方位（关键！）

```
     PCB 这一面 ↑（朝上）
     ──────────────  ← 平铺床面
     摄像头开窗这一面 ↓（朝下）
```

**理由**：摄像头开窗与灯柱凸起在「外观面」上，朝下打印可避免顶面 ironing 痕迹。

---

## 4. back_shell.stl — 后壳（FDM）

### 4.1 关键尺寸 + **过盈/间隙容差**

| 部位 | 标称 | 实际配合 | 容差策略 |
| --- | --- | --- | --- |
| 外径 | Ø90.0 mm | 与前壳贴合 | ±0.2 mm |
| 中央磁铁卡位 | Ø22.2 mm（已含 0.2 间隙） | N52 Ø22 磁铁滑配 | **+0.1 / -0.0** |
| 4 颗周边磁铁卡位 | Ø8.2 mm | N52 Ø8 磁铁滑配 | **+0.1 / -0.0** |
| USB-C 开槽 | 9.0 × 4.0 mm | TYPE-C 母座外壁 | **+0.15 / -0.0** |
| 透气孔 | Ø1.5 mm × 24 | 不阻气 | ±0.1 mm |
| 双麦克风开孔 | Ø3.0 mm × 2 | 贴 Gore-Tex 膜 | ±0.1 mm |
| 后壳厚 | 2.0 mm | 强度 + 散热平衡 | ±0.05 mm |

### 4.2 切片器参数

参数与前壳相同，**仅以下三项调整**：

| 参数 | 数值 | 与前壳的差异 |
| --- | --- | --- |
| 颜色 | **哑黑 PETG** | 装饰对比 |
| 顶/底层数 | **6 / 5** | 后壳贴肤侧要更密实，挡漏光 |
| 填充率 | **20% gyroid** | 比前壳略高，增强磁铁卡位强度 |

### 4.3 摆放方位

```
     磁铁卡位口 ↑（朝上）   ← 安装时从背面塞磁铁
     ──────────────       ← 平铺床面
     贴肤面 ↓（朝下）       ← 朝下打印保证表面光滑
```

---

## 5. tri_supports.stl — Y 字三支撑（FDM，可选）

> ⚠️ 一般情况下 `tri_supports` 已经在 `front_shell` 渲染中合并。**仅当需要单独喷涂双色（前壳银 / 三支撑哑黑）时**才单独打印这一件。

| 参数 | 数值 |
| --- | --- |
| 整体尺寸 | Ø39.4 × 2.5 mm（实际为 3 个支撑臂 + 末端铆钉） |
| 层高 | 0.10 mm（细节件） |
| 填充率 | 100%（实心，太小） |
| 支撑 | 不需要 |
| 后处理 | 喷哑黑漆 / 银色金属漆 |

---

## 6. copper_coil_x1.stl — 铜色装饰线圈（SLA）

### 6.1 关键尺寸

| 参数 | 数值 | 容差 |
| --- | --- | --- |
| 外径 | Ø8.0 mm | ±0.05 mm |
| 内孔径 | Ø3.0 mm | **+0.05 / -0.0**（穿线柱） |
| 高度 | 2.5 mm | ±0.05 mm |
| 表面环纹 | 4 圈 × 0.2 mm 凸起 | 视觉细节 |

### 6.2 SLA 切片参数（Lychee / Chitubox）

| 参数 | 数值 | 说明 |
| --- | --- | --- |
| 层高 | **0.05 mm**（50 μm） | 表面 4 圈环纹必须清晰 |
| 曝光时间 | 2.5 s（视树脂） | 标准灰树脂 |
| 底层曝光 | 30 s × 5 层 | |
| 抬升速度 | 65 mm/min | |
| 摆放角度 | **倾斜 30°** | 减少环纹被支撑标记破坏 |
| 支撑 | 树状支撑，从内孔与底面打接触点 | 接触点 Ø0.4 mm |
| 8 颗排列 | 同一料盘并排打印 | 总耗时同 1 颗 |

### 6.3 后处理

1. IPA 浸泡 5 min + 流水冲洗
2. UV 二次固化 5 min
3. 去支撑 + 内孔修整（用 Ø3.0 mm 钻头手工旋一下）
4. **铜色喷漆**（推荐：模型用 Tamiya XF-9 哑黑底 + Vallejo 71.066 古铜色）
5. 哑光透明漆封闭（防氧化变色）

---

## 7. 装配容差与配合关系

### 7.1 整机叠层装配（自上而下）

| 层 | 装配方式 | 关键容差 |
| --- | --- | --- |
| ① 前壳 + 8 铜线圈 | 铜线圈 Ø3 内孔嵌入前壳 8 个 Ø2 凸柱 | 凸柱 Ø2 +0.05/-0.05 |
| ② PMMA 扩散板（注塑件） | 嵌入前壳 8 段灯柱开窗 | 配 -0.1 mm 间隙 |
| ③ LED 灯环 PCB（嘉立创下单） | 双面胶贴前壳内壁 | — |
| ④ 主控 PCB | 4 颗 M2 螺柱固定 | 螺柱孔 Ø2.2 |
| ⑤ 双 2000 mAh 电池 | 双面胶贴 PCB 下方 | — |
| ⑥ 后壳 | 与前壳卡扣（CAD 中暂未做卡扣，先用 4 颗 M1.6 螺丝） | — |
| ⑦ 5 颗磁铁 | 从后壳背面塞入 + AB 胶固定 | 卡位 Ø+0.2 |
| ⑧ 0.5 mm 硅胶贴肤垫 | 双面胶贴后壳外面 | — |

### 7.2 容差自检清单（打印完成后）

```
☐ 前壳直径 90 mm ±0.2  (游标卡尺)
☐ 后壳直径 90 mm ±0.2
☐ 前壳 - 后壳 高度差  (实测两件总高 = 前壳 4.0 + 后壳 4.5 = 8.5 ±0.3 mm)
☐ 中央 Φ22 磁铁能滑入卡位（轻按到底，不晃动）
☐ 4 颗 Φ8 磁铁能滑入卡位
☐ USB-C 母座能正面对入开槽（不挤压焊脚）
☐ 8 颗铜线圈嵌入前壳（手按下去，不再弹出）
☐ 双麦克风孔 Φ3 与 PCB 焊盘对齐（用 LED 手电从孔背照，PCB 焊盘居中可见）
```

---

## 8. 已知 OpenSCAD warning 处理

```
WARNING: Object may not be a valid 2-manifold and may need repair!
EXPORT-WARNING: Exported object may not be a valid 2-manifold ...
```

**只发生在 `front_shell.stl`**。原因：`pie_ring`（扇形减运算）在外/内圈共边处偶尔产生 zero-thickness 三角形面。

**影响**：在主流切片器（PrusaSlicer / Bambu Studio / Lychee）中**会被自动 repair**，实际打印**没有问题**。已实测：

- PrusaSlicer 2.7：导入时提示「自动修复」，确认后正常切片
- Bambu Studio：静默修复，无提示
- Cura：导入即报"net volume issue"，需手动选 Mesh → Repair

如果你用的是更挑剔的工业切片器（Materialise Magics 等），可用 [admesh](https://github.com/admesh/admesh) 修复：

```bash
brew install admesh
admesh --write-binary-stl=front_shell_fixed.stl front_shell.stl
```

---

## 9. 完整打印订单（一键淘宝/嘉立创下单参考）

| 项 | 规格 | 单价 | 数量 | 备注 |
| --- | --- | --- | --- | --- |
| PETG 银灰色耗材 | 1.75 mm 1 kg | ¥80/卷 | 共用 ~10 g | 三角束、eSun、Polymaker |
| PETG 哑黑色耗材 | 1.75 mm 1 kg | ¥80/卷 | 共用 ~5 g | 同上 |
| SLA 标准灰树脂 | 500 g | ¥120/瓶 | 共用 ~1 g | Anycubic、Elegoo |
| 铜色喷漆 + 哑光封漆 | Tamiya / Vallejo | ¥60 | 1 套 | 涂 8 颗线圈 |
| Brim 胶水 / 蓝胶 | 3DLAC / 普通胶水 | ¥30 | 1 瓶 | 防 PETG 翘边 |
| **平摊到单台** | | | | **< ¥3 / 台**（仅打印件，磁铁/PCB/电池见 BOM） |

---

## 10. 与 OpenSCAD 设计文件的同步

修改设计 → 重新导出 STL：

```bash
# 1. 改 mechanical/openscad/parameters.scad（厚度、孔位等）
vim mechanical/openscad/parameters.scad

# 2. 一键重出全部 STL
bash mechanical/openscad/export_stl.sh

# 3. 校验新 STL 的尺寸
python3 mechanical/openscad/verify_stl.py

# 4. 重新切片打印
```

源文件→STL→切片→打印 全链路可追溯，无任何 GUI 操作环节。
