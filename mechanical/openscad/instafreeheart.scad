// =============================================================================
// InstaFreeHeart · OpenSCAD 主装配文件（方案 A · Mark I 圆形特斯拉款）
// -----------------------------------------------------------------------------
// 参考图：../898b908eeca3d8b0d72bd0f4745d17cf.jpeg
//
// 用法：
//   1) 在 OpenSCAD 中打开本文件 → F5 预览 / F6 渲染
//   2) 修改 parameters.scad 改尺寸；本文件无需改
//   3) 单独导出某个零件 → 见文件末尾「单件导出」一节
//   4) 切换装配/爆炸视图 → 修改 parameters.scad 中 EXPLODE
// =============================================================================
include <parameters.scad>


// =============================================================================
// 1. 基础几何辅助
// =============================================================================

// 圆环（外半径，内半径，高度）
module ring(od, id, h) {
    linear_extrude(height=h)
        difference() {
            circle(d=od);
            circle(d=id);
        }
}

// 扇形环带（OD/ID/起始角/扫过角度/高度）
module pie_ring(od, id, start_angle, sweep_angle, h) {
    n = max(20, ceil(sweep_angle));
    linear_extrude(height=h)
        polygon(points = concat(
            // 外缘弧
            [for (i = [0 : n])
                let (a = start_angle + sweep_angle * i / n)
                [od/2 * cos(a), od/2 * sin(a)]],
            // 内缘弧（反向）
            [for (i = [0 : n])
                let (a = start_angle + sweep_angle * (n - i) / n)
                [id/2 * cos(a), id/2 * sin(a)]]
        ));
}


// =============================================================================
// 2. 前壳（最外银色金属圈 + 内部各环骨架）
// =============================================================================
module front_shell() {
    color(COLOR_FRONT)
    difference() {
        // 主体：圆盘
        cylinder(d=OUTER_RING_OD, h=FRONT_SHELL_T);

        // ⑴ 中央摄像头开窗
        translate([0, 0, -0.1])
            cylinder(d=CAM_HOLE_D, h=FRONT_SHELL_T + 0.2);

        // ⑵ 8 段外圈灯柱开窗（让蓝光透出）
        for (i = [0 : OUTER_LIGHT_COUNT - 1]) {
            angle = 360 * i / OUTER_LIGHT_COUNT - OUTER_LIGHT_ARC/2;
            translate([0, 0, -0.1])
                pie_ring(OUTER_LIGHT_OD, OUTER_LIGHT_ID,
                          angle, OUTER_LIGHT_ARC,
                          FRONT_SHELL_T + 0.2);
        }

        // ⑶ 8 段内圈灯开窗（中央亮圆周围）
        for (i = [0 : OUTER_LIGHT_COUNT - 1]) {
            angle = 360 * i / OUTER_LIGHT_COUNT
                    + 360 / OUTER_LIGHT_COUNT / 2 - 18;
            translate([0, 0, -0.1])
                pie_ring(INNER_LIGHT_OD, INNER_LIGHT_ID,
                          angle, 36,
                          FRONT_SHELL_T + 0.2);
        }
    }

    // ⑷ 8 个外圈银色金属夹板（在灯柱之间凸起 1.5 mm，营造立体感）
    for (i = [0 : OUTER_LIGHT_COUNT - 1]) {
        bracket_center = 360 * i / OUTER_LIGHT_COUNT
                          + 360 / OUTER_LIGHT_COUNT / 2;
        color(COLOR_BRACKET)
            translate([0, 0, FRONT_SHELL_T])
                pie_ring(OUTER_LIGHT_OD, OUTER_LIGHT_ID,
                          bracket_center - OUTER_BRACKET_ARC/2,
                          OUTER_BRACKET_ARC,
                          RING_BAND_T);
    }

    // ⑸ 中央内圈骨架（隔开 8 段内灯）
    for (i = [0 : OUTER_LIGHT_COUNT - 1]) {
        bracket_center = 360 * i / OUTER_LIGHT_COUNT;
        color(COLOR_BRACKET)
            translate([0, 0, FRONT_SHELL_T])
                pie_ring(INNER_LIGHT_OD, INNER_LIGHT_ID,
                          bracket_center - 9, 18, RING_BAND_T);
    }

    // ⑹ 中圈线圈带骨架（铜线圈底座）
    color(COLOR_FRONT)
        translate([0, 0, FRONT_SHELL_T])
            ring(INNER_BAND_OD, INNER_BAND_ID, RING_BAND_T * 0.6);
}


// =============================================================================
// 3. 铜色线圈（特斯拉风格装饰）
// -----------------------------------------------------------------------------
//   one_coil()      : 单颗（用于 SLA 树脂打印 + 喷涂铜色，下单 8 份）
//   copper_coils()  : 8 颗按外圈分布（仅用于装配预览，非打印）
// =============================================================================
module one_coil() {
    color(COLOR_COPPER)
        difference() {
            cylinder(d=COIL_OD, h=COIL_HEIGHT);
            translate([0, 0, -0.1])
                cylinder(d=COIL_ID, h=COIL_HEIGHT + 0.2);
            // 线圈表面 4 圈环纹（视觉细节）
            for (k = [1 : 4])
                translate([0, 0, k * COIL_HEIGHT/5])
                    ring(COIL_OD - 0.3, COIL_OD - 0.6, 0.2);
        }
}

module copper_coils() {
    // 8 个铜线圈位于「8 段外灯柱之间的银夹板」中心位置
    for (i = [0 : COIL_COUNT - 1]) {
        // 夹板中心角度 = 灯柱中心 + 360/8/2 = i*45 + 22.5
        angle = 360 * i / COIL_COUNT + 360 / COIL_COUNT / 2;
        x = COIL_R * cos(angle);
        y = COIL_R * sin(angle);
        translate([x, y, FRONT_SHELL_T + RING_BAND_T])
            one_coil();
    }
}


// =============================================================================
// 4. Y 字 3 支撞（中央放射臂）
// =============================================================================
module tri_supports() {
    color(COLOR_BRACKET)
    for (a = [0, 120, 240]) {
        rotate([0, 0, a + 90])
            translate([-TRI_SUPPORT_W/2, CENTER_OD/2 - 1,
                        FRONT_SHELL_T + RING_BAND_T])
                cube([TRI_SUPPORT_W, TRI_SUPPORT_LEN, RING_BAND_T * 0.7]);
        // 末端铆钉
        rotate([0, 0, a + 90])
            translate([0, CENTER_OD/2 - 1 + TRI_SUPPORT_LEN - 1.5,
                        FRONT_SHELL_T + RING_BAND_T])
                cylinder(d=TRI_KNOB_D, h=RING_BAND_T);
    }
}


// =============================================================================
// 5. 中央白亮圆（PMMA 半球面镜片 + 后方 LED 透出）
// =============================================================================
module center_lens() {
    color(COLOR_CENTER)
        translate([0, 0, FRONT_SHELL_T - 0.1])
            difference() {
                cylinder(d=CENTER_OD, h=RING_BAND_T * 1.4);
                translate([0, 0, -0.2])
                    cylinder(d=CAM_HOLE_D, h=RING_BAND_T * 1.4 + 0.4);
            }
}


// =============================================================================
// 6. PMMA 蓝光扩散板（由两个同心环扩散区组成）
// =============================================================================
module diffuser() {
    color(COLOR_DIFFUSER) {
        // 外圈扩散板（覆盖 8 段灯柱区域）
        ring(OUTER_LIGHT_OD - 1, OUTER_LIGHT_ID + 1, DIFFUSER_T);
        // 内圈扩散板（覆盖 8 段内灯区域）
        ring(INNER_LIGHT_OD - 1, INNER_LIGHT_ID + 1, DIFFUSER_T);
    }
}


// =============================================================================
// 7. LED 灯环 PCB（圆形 FPC + 16 颗 WS2812B 双同心环排列）
// =============================================================================
module led_ring() {
    color(COLOR_LED_PCB) {
        // 圆形 FPC 板
        difference() {
            cylinder(d=OUTER_LIGHT_OD, h=0.6);
            translate([0, 0, -0.1])
                cylinder(d=CAM_HOLE_D, h=0.8);
        }
        // 外圈 8 颗 LED
        for (i = [0 : LED_OUTER_COUNT - 1]) {
            angle = 360 * i / LED_OUTER_COUNT;
            r = LED_OUTER_R;
            translate([r * cos(angle), r * sin(angle), 0.6])
                color([1, 1, 1, 1])
                    translate([-LED_PIXEL_S/2, -LED_PIXEL_S/2, 0])
                        cube([LED_PIXEL_S, LED_PIXEL_S, 1.0]);
        }
        // 内圈 8 颗 LED
        for (i = [0 : LED_INNER_COUNT - 1]) {
            angle = 360 * i / LED_INNER_COUNT + 22.5;
            r = LED_INNER_R;
            translate([r * cos(angle), r * sin(angle), 0.6])
                color([1, 1, 1, 1])
                    translate([-LED_PIXEL_S/2, -LED_PIXEL_S/2, 0])
                        cube([LED_PIXEL_S, LED_PIXEL_S, 1.0]);
        }
    }
}


// =============================================================================
// 8. 主控 PCB（圆形板 + 摄像头模组）
// =============================================================================
module main_pcb() {
    color(COLOR_PCB) {
        cylinder(d=PCB_OD, h=PCB_T);
        // OV5640 摄像头模组居中（板顶面）
        translate([0, 0, PCB_T])
            cylinder(d=8.5, h=4.5);
        // ESP32-S3 模组（板底面，向下凸出）
        translate([-9, -12.75, -2.5])
            cube([18, 25.5, 2.5]);
    }
}


// =============================================================================
// 9. 双锂电池（左右对称布局，弧线适配圆形 PCB 下方空间）
// =============================================================================
module battery() {
    color(COLOR_BATTERY)
        cube([BAT_W, BAT_H, BATTERY_T]);
}

module battery_pack() {
    translate([-(BAT_W + BAT_GAP/2), -BAT_H/2, 0])
        battery();
    translate([BAT_GAP/2, -BAT_H/2, 0])
        battery();
}


// =============================================================================
// 10. Halbach 磁铁组（中央 Φ22 + 4 颗 Φ8 周边）
// =============================================================================
module magnet_central() {
    color(COLOR_MAGNET)
        cylinder(d=MAG_C_D, h=MAG_C_T);
}

module magnet_edge() {
    color(COLOR_MAGNET)
        cylinder(d=MAG_E_D, h=MAG_E_T);
}

module magnet_array() {
    magnet_central();
    for (a = [0, 90, 180, 270])
        rotate([0, 0, a])
            translate([MAG_E_R, 0, 0])
                magnet_edge();
}


// =============================================================================
// 11. 后壳（圆形 + 5 个磁铁卡位 + USB-C 开槽 + 透气孔）
// =============================================================================
module back_shell() {
    color(COLOR_BACK)
    difference() {
        cylinder(d=OUTER_RING_OD, h=BACK_SHELL_T);

        // 中央磁铁卡位
        translate([0, 0, -0.1])
            cylinder(d=MAG_C_D + MAG_CLEARANCE, h=BACK_SHELL_T + 0.2);

        // 4 颗周边磁铁卡位
        for (a = [0, 90, 180, 270])
            rotate([0, 0, a])
                translate([MAG_E_R, 0, -0.1])
                    cylinder(d=MAG_E_D + MAG_CLEARANCE,
                             h=BACK_SHELL_T + 0.2);

        // USB-C 开槽
        translate([USBC_SIDE == "right" ? 18 : -18,
                    USBC_OFFSET_Y, -0.1])
            cube([USBC_W, USBC_H, BACK_SHELL_T + 0.2], center=true);

        // 透气孔阵列（双圈圆周分布，避开磁铁正下方）
        for (i = [0 : VENT_HOLE_COUNT - 1]) {
            // 内圈
            angle = 360 * i / VENT_HOLE_COUNT + 15;
            translate([VENT_HOLE_R1 * cos(angle),
                        VENT_HOLE_R1 * sin(angle), -0.1])
                cylinder(d=VENT_HOLE_D, h=BACK_SHELL_T + 0.2);
            // 外圈
            angle2 = 360 * i / VENT_HOLE_COUNT;
            translate([VENT_HOLE_R2 * cos(angle2),
                        VENT_HOLE_R2 * sin(angle2), -0.1])
                cylinder(d=VENT_HOLE_D, h=BACK_SHELL_T + 0.2);
        }

        // ★ 双麦克风开孔（与 INMP441 上下对齐，贴 Gore-Tex 防风膜+海绵）
        translate([MIC_A_POS[0], MIC_A_POS[1], -0.1])
            cylinder(d=MIC_HOLE_D, h=BACK_SHELL_T + 0.2);
        translate([MIC_B_POS[0], MIC_B_POS[1], -0.1])
            cylinder(d=MIC_HOLE_D, h=BACK_SHELL_T + 0.2);
    }

    // 中央磁铁背面补强环
    color(COLOR_BACK)
    translate([0, 0, BACK_SHELL_T])
        difference() {
            cylinder(d=MAG_C_D + 4, h=MAG_C_T - BACK_SHELL_T + 0.5);
            translate([0, 0, -0.1])
                cylinder(d=MAG_C_D + MAG_CLEARANCE,
                         h=MAG_C_T - BACK_SHELL_T + 0.7);
        }
}


// =============================================================================
// 11.5 散热升级 ① 石墨烯导热膜（25 μm，贴在后壳内壁，横向均温）
// =============================================================================
module graphene_film() {
    color(COLOR_GRAPHENE)
    difference() {
        cylinder(d=OUTER_RING_OD - 5, h=GRAPHENE_T);
        // 中央磁铁开孔
        translate([0, 0, -0.05])
            cylinder(d=MAG_C_D + 1, h=GRAPHENE_T + 0.1);
        // 4 颗周边磁铁开孔
        for (a = [0, 90, 180, 270])
            rotate([0, 0, a])
                translate([MAG_E_R, 0, -0.05])
                    cylinder(d=MAG_E_D + 1, h=GRAPHENE_T + 0.1);
        // USB-C 让位
        translate([USBC_SIDE == "right" ? 18 : -18,
                    USBC_OFFSET_Y, -0.05])
            cube([USBC_W + 2, USBC_H + 2, GRAPHENE_T + 0.1], center=true);
    }
}


// =============================================================================
// 11.6 散热升级 ② 导热硅胶垫（贴芯片顶面 → 后壳内壁）
// =============================================================================
module tim_pad() {
    color(COLOR_TIM) {
        // ① IP5306 顶面 TIM
        translate([NTC_PMU_POS[0] - TIM_BAT_W/2,
                    NTC_PMU_POS[1] - TIM_BAT_H/2, 0])
            cube([TIM_BAT_W, TIM_BAT_H, TIM_PAD_T]);
        // ② ESP32-S3 顶面 TIM（更大）
        translate([-TIM_MCU_W/2,
                    NTC_MCU_POS[1] - TIM_MCU_H/2, 0])
            cube([TIM_MCU_W, TIM_MCU_H, TIM_PAD_T]);
    }
}


// =============================================================================
// 11.7 散热升级 ③ 3 颗 NTC（贴片元件可视化）
// =============================================================================
module ntc_dots() {
    color(COLOR_NTC) {
        for (pos = [NTC_BAT_POS, NTC_PMU_POS, NTC_MCU_POS])
            translate([pos[0], pos[1], 0])
                cylinder(d=NTC_PAD_D, h=0.5);
    }
}


// =============================================================================
// 11.8 双 INMP441 麦克风（贴在主控 PCB 顶面）
// =============================================================================
module mic_chips() {
    color("#222") {
        for (pos = [MIC_A_POS, MIC_B_POS])
            translate([pos[0] - 1.88, pos[1] - 2.36, 0])
                cube([3.76, 4.72, 1.0]);
    }
}


// =============================================================================
// 11.9 ★ 防风罩组件（Gore-Tex 0.05 mm + PORON 0.5 mm 海绵）
//      贴在后壳麦克风开孔的内侧（朝向 PCB 一面）
// =============================================================================
module wind_filter() {
    for (pos = [MIC_A_POS, MIC_B_POS]) {
        // PORON 海绵（深灰）
        color([0.25, 0.25, 0.25, 0.95])
            translate([pos[0], pos[1], 0])
                cylinder(d=WIND_FILM_D, h=WIND_FOAM_T);
        // Gore-Tex 膜（白色透明）
        color([0.92, 0.92, 0.92, 0.6])
            translate([pos[0], pos[1], WIND_FOAM_T])
                cylinder(d=WIND_FILM_D, h=0.05);
    }
}


// =============================================================================
// 12. 0.5 mm 硅胶贴肤层
// =============================================================================
module silicon_pad() {
    color(COLOR_SILICON)
    difference() {
        cylinder(d=OUTER_RING_OD - 1, h=SILICON_PAD_T);
        translate([0, 0, -0.1])
            cylinder(d=MAG_C_D + 1, h=SILICON_PAD_T + 0.2);
        for (a = [0, 90, 180, 270])
            rotate([0, 0, a])
                translate([MAG_E_R, 0, -0.1])
                    cylinder(d=MAG_E_D + 1, h=SILICON_PAD_T + 0.2);
        translate([USBC_SIDE == "right" ? 18 : -18,
                    USBC_OFFSET_Y, -0.1])
            cube([USBC_W + 2, USBC_H + 2, SILICON_PAD_T + 0.2], center=true);
        // ★ 麦克风开孔（与后壳孔对齐，让声音穿过硅胶垫）
        translate([MIC_A_POS[0], MIC_A_POS[1], -0.1])
            cylinder(d=WIND_FILM_D, h=SILICON_PAD_T + 0.2);
        translate([MIC_B_POS[0], MIC_B_POS[1], -0.1])
            cylinder(d=WIND_FILM_D, h=SILICON_PAD_T + 0.2);
    }
}


// =============================================================================
// 13. 总装配
// -----------------------------------------------------------------------------
// 沿 Z 轴自上而下叠层（Z+ 朝外/朝向观察者）：
//   ① 前壳 + 铜线圈 + Y 三支撑 + 中央亮圆      Z = 0+
//   ② PMMA 扩散板                              下方
//   ③ LED 灯环                                 下方
//   ④ 主控 PCB                                 下方
//   ⑤ 双电池                                   下方
//   ⑥ 后壳 + 磁铁                              下方
//   ⑦ 硅胶垫                                   最底
// =============================================================================
module assembly() {
    e = EXPLODE;

    // ① 前壳（包含 8 段灯柱开窗、夹板凸起、内圈骨架、线圈底座）
    translate([0, 0, e * 1.0])
        front_shell();

    // 铜线圈（位于前壳的中圈带上）
    translate([0, 0, e * 1.2])
        copper_coils();

    // Y 字 3 支撞（位于中央内圈灯之上）
    translate([0, 0, e * 1.0])
        tri_supports();

    // 中央亮圆（PMMA 镜片）
    translate([0, 0, e * 1.0])
        center_lens();

    // ② PMMA 扩散板
    translate([0, 0, -DIFFUSER_T - e * 0.6])
        diffuser();

    // ③ LED 灯环
    translate([0, 0, -DIFFUSER_T - LED_RING_T - e * 1.0])
        led_ring();

    // ④ 主控 PCB
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - e * 1.4])
        rotate([180, 0, 0])
            main_pcb();

    // ⑤ 双电池
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - e * 1.8])
        battery_pack();

    // ⑤.4 双 INMP441 麦克风（贴在主控 PCB 顶面）
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - 1.0 - e * 1.4])
        mic_chips();

    // ⑤.5 NTC 贴片元件（贴在主控 PCB 顶面热源附近）
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - 0.5 - e * 1.5])
        ntc_dots();

    // ⑤.6 导热硅胶垫（覆盖 IP5306/ESP32 → 后壳）
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - e * 1.9])
        tim_pad();

    // ⑤.7 石墨烯散热膜（贴在后壳内壁，TIM 之下、后壳之上）
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - GRAPHENE_T - e * 2.05])
        graphene_film();

    // ★ 防风罩（贴在后壳麦孔内侧）
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - GRAPHENE_T
                       - WIND_FOAM_T - e * 2.15])
        wind_filter();

    // ⑥ 后壳
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - GRAPHENE_T
                       - WIND_FOAM_T - 0.05 - BACK_SHELL_T - e * 2.2])
        back_shell();

    // 磁铁
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - GRAPHENE_T
                       - WIND_FOAM_T - 0.05 - BACK_SHELL_T - e * 2.6])
        magnet_array();

    // ⑦ 硅胶贴肤层
    translate([0, 0, -DIFFUSER_T - LED_RING_T - PCB_T - PCB_COMP_BOT
                       - BATTERY_T - TIM_PAD_T - GRAPHENE_T
                       - WIND_FOAM_T - 0.05 - BACK_SHELL_T - SILICON_PAD_T
                       - e * 3.0])
        silicon_pad();
}


// =============================================================================
// 14. 入口 — PART 选择器
// -----------------------------------------------------------------------------
//   命令行用法（覆盖 PART 变量，导出对应零件 STL）：
//     openscad -o front_shell.stl -D 'PART="front"' instafreeheart.scad
//     openscad -o back_shell.stl  -D 'PART="back"'  instafreeheart.scad
//     openscad -o copper_coil.stl -D 'PART="coil"'  instafreeheart.scad
//     openscad -o tri_supports.stl -D 'PART="tri"'  instafreeheart.scad
//     openscad -o assembly.stl    -D 'PART="all"'   instafreeheart.scad
//
//   渲染预览（默认 assembly）：
//     openscad instafreeheart.scad
// =============================================================================
PART = "all";    // "all" | "front" | "back" | "coil" | "tri"

if      (PART == "all")   assembly();
else if (PART == "front") front_shell();
else if (PART == "back")  back_shell();
else if (PART == "coil")  one_coil();
else if (PART == "tri")   tri_supports();
else                      assembly();
