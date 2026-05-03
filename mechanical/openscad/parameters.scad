// =============================================================================
// InstaFreeHeart · 全局参数（方案 A · Mark I 圆形特斯拉款）
// =============================================================================
// 参考图：../898b908eeca3d8b0d72bd0f4745d17cf.jpeg
// 同心结构（从外到内）：
//   ⑴ 最外银色金属圈
//   ⑵ 外圈：8 段蓝光灯柱 + 8 段银色金属夹板
//   ⑶ 中圈：8 个铜色线圈（特斯拉风格装饰） + 8 段内蓝光
//   ⑷ 中央白亮圆 + Y 字 3 支撞
// 改动只需要修改本文件，所有模块通过 include 该文件的方式共享参数。
// 单位：毫米（mm）。
// =============================================================================

// ----- 渲染品质 -----
$fa = 1;
$fs = 0.4;
$fn = 0;

// ----- 整机外形 -----
TOTAL_OD        = 90;     // 整机外径
TOTAL_THK       = 15;     // 整机厚度（v2 升级 14→15 mm，电池 6→7 mm 容纳 4000 mAh）

// ----- 同心环径向尺寸（半径制） -----
OUTER_RING_OD   = 90;     // 最外银色金属圈外径
OUTER_RING_ID   = 80;     // 最外金属圈内径

OUTER_LIGHT_OD  = 78;     // 外圈灯柱外径
OUTER_LIGHT_ID  = 60;     // 外圈灯柱内径

INNER_BAND_OD   = 58;     // 中圈线圈带外径
INNER_BAND_ID   = 30;     // 中圈线圈带内径

INNER_LIGHT_OD  = 28;     // 中央内圈灯外径
INNER_LIGHT_ID  = 20;     // 内圈灯内径

CENTER_OD       = 18;     // 中央白亮圆直径

// ----- 8 段灯柱 / 银夹板 -----
OUTER_LIGHT_COUNT  = 8;            // 8 段蓝光灯柱
OUTER_LIGHT_ARC    = 30;           // 单段灯柱占角（°），剩 15° 留给夹板
OUTER_BRACKET_ARC  = 15;           // 单个银色夹板占角（°），8×(30+15)=360
OUTER_BRACKET_KNOB = 1.5;          // 夹板上凸起小铆钉直径

// ----- 8 个铜线圈（特斯拉风格 · 位于 8 段外灯柱之间的银夹板上） -----
COIL_COUNT      = 8;
COIL_OD         = 8;      // 单个铜线圈外径
COIL_ID         = 3;      // 内孔
COIL_HEIGHT     = 2.5;    // 凸起高度
COIL_R          = 34.5;   // = (OUTER_LIGHT_OD + OUTER_LIGHT_ID) / 4，正好在外灯柱半径中间

// ----- Y 字 3 支撞（中央放射臂） -----
TRI_SUPPORT_W   = 2.5;    // 支撞宽度
TRI_SUPPORT_LEN = 14;     // 从中央向外延伸长度
TRI_KNOB_D      = 2.0;    // 支撞末端铆钉直径

// ----- 摄像头开窗 -----
CAM_HOLE_D      = 12;
CAM_HOLE_BEZEL  = 1.0;

// ----- 各层厚度 -----
FRONT_SHELL_T   = 1.5;     // 前壳基础厚度
RING_BAND_T     = 2.5;     // 同心环刻面凸起高度（金属感）
DIFFUSER_T      = 1.0;     // PMMA 扩散板
LED_RING_T      = 1.6;     // LED PCB + 灯珠
PCB_T           = 1.6;     // 主控 PCB 板厚
PCB_COMP_TOP    = 3.0;
PCB_COMP_BOT    = 4.0;
BATTERY_T       = 7.0;     // v2: 6 → 7 mm，单芯 1500 → 2000 mAh，双芯 = 4000 mAh
TIM_PAD_T       = 0.5;     // ☆ 散热升级：导热硅胶垫（贴芯片→后壳）k=5
BACK_SHELL_T    = 2.0;
GRAPHENE_T      = 0.025;   // ☆ 散热升级：石墨烯导热膜（贴在后壳内壁）k=1500
SILICON_PAD_T   = 0.5;

// ----- LED 布局（双同心环 = 16 颗 WS2812B-2020） -----
LED_OUTER_COUNT = 8;       // 外圈 8 颗（对齐 8 段灯柱中央）
LED_INNER_COUNT = 8;       // 内圈 8 颗（对齐 8 段内灯）
LED_OUTER_R     = 35;      // 外圈半径
LED_INNER_R     = 12;      // 内圈半径
LED_PIXEL_S     = 2.0;     // 单颗 WS2812B 封装边长

// ----- 主控 PCB（圆盘形以贴合外壳） -----
PCB_OD          = 80;

// ----- 双锂电池布局（左右对称放在 PCB 下方） -----
BAT_W           = 28;
BAT_H           = 50;
BAT_GAP         = 6;       // 两颗电池中心距 = BAT_W + BAT_GAP

// ----- USB-C 开槽（位于圆盘底部边缘） -----
USBC_W          = 9.0;
USBC_H          = 4.0;
USBC_OFFSET_Y   = -42;     // 接近圆盘底边
USBC_SIDE       = "right"; // "right" | "left"

// ----- 磁吸（Halbach 阵列） -----
MAG_C_D         = 22;
MAG_C_T         = 4;
MAG_E_D         = 8;
MAG_E_T         = 2;
MAG_E_R         = 30;      // 周边磁铁布置半径
MAG_CLEARANCE   = 0.2;

// ----- 透气孔阵列 -----
VENT_HOLE_D     = 1.5;
VENT_HOLE_R1    = 18;      // 内圈布孔半径
VENT_HOLE_R2    = 25;      // 外圈布孔半径
VENT_HOLE_COUNT = 12;      // 每圈孔数

// ----- ★ 双麦克风开孔（贴 Gore-Tex 防风膜 + PORON 海绵） -----
MIC_HOLE_D      = 3.0;     // 麦孔直径（比常规透气孔大，便于贴防风膜）
MIC_A_POS       = [0, 28];   // 主麦：靠近用户口部一侧（PCB 顶部）
MIC_B_POS       = [0, -28];  // 副麦：远离用户口部一侧（PCB 底部）
WIND_FILM_D     = 10;       // Gore-Tex 防风膜直径
WIND_FOAM_T     = 0.5;      // PORON 海绵厚度

// ----- 散热增强：3 颗 NTC 位置（仅用于装配可视化） -----
NTC_COUNT       = 3;
NTC_PAD_D       = 1.6;     // NTC 0805 焊盘可视化直径
NTC_BAT_POS     = [-22, 0];   // 贴电池正极极耳
NTC_PMU_POS     = [22, -8];   // 贴 IP5306 顶面
NTC_MCU_POS     = [0, 18];    // 贴 ESP32-S3 模组旁

// ----- 散热增强：导热硅胶垫覆盖 IP5306 + ESP32 的位置 -----
TIM_BAT_W       = 14;
TIM_BAT_H       = 14;
TIM_MCU_W       = 18;
TIM_MCU_H       = 26;

// ----- 颜色（仅装配视觉） -----
COLOR_FRONT       = [0.78, 0.80, 0.82, 0.95];   // 银色金属
COLOR_BRACKET     = [0.85, 0.86, 0.88, 1.00];   // 高光银
COLOR_BLUE_LIGHT  = [0.30, 0.85, 1.00, 0.95];   // Tesla 蓝
COLOR_COPPER      = [0.85, 0.45, 0.20, 1.00];   // 铜色
COLOR_CENTER      = [0.95, 0.98, 1.00, 0.95];   // 中央白光
COLOR_DIFFUSER    = [0.30, 0.85, 1.00, 0.55];   // 透蓝扩散
COLOR_LED_PCB     = [1.00, 1.00, 1.00, 1.00];   // 白
COLOR_PCB         = [0.00, 0.50, 0.20, 0.95];
COLOR_BATTERY     = [0.30, 0.30, 0.30, 0.95];
COLOR_BACK        = [0.10, 0.10, 0.10, 0.95];
COLOR_MAGNET      = [0.55, 0.55, 0.60, 1.00];
COLOR_SILICON     = [0.20, 0.20, 0.20, 0.85];
COLOR_GRAPHENE    = [0.15, 0.15, 0.15, 1.00];   // 石墨烯黑灰色（金属光泽）
COLOR_TIM         = [0.95, 0.85, 0.20, 0.85];   // 导热硅胶垫常见的明黄色
COLOR_NTC         = [0.20, 0.20, 0.20, 1.00];

// ----- 装配模式 -----
EXPLODE         = 0;
