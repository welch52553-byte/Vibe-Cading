// 示例：带圆孔的长方体外壳
// 用于演示几何标注功能
// 单位：mm

wall_thickness = 3;
width = 80;
depth = 60;
height = 20;
hole_diameter = 8;

difference() {
    // 主体
    cube([width, depth, height], center=true);

    // 顶面中心孔
    translate([0, 0, height/2 - wall_thickness])
        cylinder(h = wall_thickness + 1, d = hole_diameter, center = false, $fn = 32);

    // 前面 USB 口开孔
    translate([0, -depth/2, 0])
        rotate([90, 0, 0])
        translate([0, 0, -1])
        cylinder(h = wall_thickness + 2, d = 6, center = false, $fn = 32);
}
