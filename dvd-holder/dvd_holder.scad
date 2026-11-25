// DVD / CD spindle holder ("cake box") with a twist-lock cap.
// Two prints: base (flange + spindle) and cap. All dimensions in mm.
//
// Render one part at a time:
//   openscad -D 'part="base"' -o base.stl dvd_holder.scad
//   openscad -D 'part="cap"'  -o cap.stl  dvd_holder.scad
// Both come out in print orientation: base flange-down, cap top-down.

/* [What to render] */
part = "assembly"; // [assembly, exploded, section, base, cap]
// Show the cap twisted into the locked position (assembly / section only)
locked = true;
// Include the click detent (flex arms + bumps)
detent = true;

/* [Overall size] */
// Overall height with the cap locked on (7 in)
total_h = 177.8;
// Inside diameter of the cap (discs are 120)
cap_id = 124;
// Spindle diameter (disc hole is 15)
spindle_d = 14.2;

/* [Walls] */
cap_wall = 1.2;
cap_top_t = 1.6;
flange_t = 3;
plinth_wall = 2.4;
// Height of the locking ring above the flange
plinth_h = 8;
// Diameter of the hub the bottom disc rests on (inside the data area)
hub_d = 40;

/* [Fit] */
// Radial gap between cap and locking ring. Raise to 0.4 if the cap is tight.
clear = 0.3;
// Vertical play of the locked cap
ax_clear = 0.4;

/* [Twist lock] */
n_lugs = 4;
// Degrees of twist from drop-on to locked
twist = 30;
lug_ang = 9;
slot_ang = 12;
groove_depth = 2.4;
// Solid rim left under each locking track
retain_h = 3;
lug_flat = 2.0;

/* [Click detent] */
// How far the bump has to be pushed in to turn the cap
bump_bite = 0.5;
bump_r = 2.0;
bump_len = 5;
// Angle of each bump, measured from a lug
bump_ang = 45;
// Length of the flex arm, in degrees of arc
arm_ang = 28;
slit_w = 1.2;

/* [Grip] */
n_ribs = 48;
rib_h = 1.2;
band_h = 13;

/* [Hidden] */
$fn = 180;
eps = 0.01;

cap_ir = cap_id / 2;
body_r = cap_ir + cap_wall;
groove_r = cap_ir + groove_depth;
band_r = groove_r + 1.8;
grip_r = band_r + rib_h;
flange_r = grip_r + 1.8;

rim_z = flange_t;                       // the cap rim sits on the flange
ceil_z = total_h - cap_top_t;           // inside face of the cap top
band_top = rim_z + band_h;

plinth_r = cap_ir - clear;
plinth_top = flange_t + plinth_h;
seat_z = plinth_top + 0.5;              // discs rest on the hub, just clear of the ring
hub_r = hub_d / 2;

spindle_r = spindle_d / 2;
spindle_top = ceil_z - 1;
tip_h = 8;
tip_r = 4.5;

// Lug and track faces are 45 degrees so both parts print without supports.
lug_proj = groove_depth - 0.2;
lug_r = plinth_r + lug_proj;
track_z0 = rim_z + retain_h;                        // track floor at the cap's inner face
lug_z0 = track_z0 + ax_clear - (cap_ir - plinth_r); // lug underside at its root
lug_top = lug_z0 + lug_proj + lug_flat;
track_top = lug_top + 0.5;
track_end = twist + lug_ang / 2 + 1;

bump_h = clear + bump_bite;
notch_r = bump_r + 0.6;
notch_depth = bump_h;
notch_len = bump_len + 1.5;
bump_angles = [for (i = [0 : 1]) bump_ang + i * 180];

arm_r0 = plinth_r - plinth_wall;        // inner face of the flex arm
arm_r1 = cap_ir + 1.2;                  // outer edge of the arm's foot
arm_free = 3.5;                         // arm continues this far past the bump

sock_ir = spindle_r + 0.6;
sock_or = sock_ir + 2.8;
sock_z0 = ceil_z - 6;

max_stack = sock_z0 - 0.5 - seat_z;
echo(str("Disc stack height available: ", max_stack, " mm (about ",
         floor(max_stack / 1.2), " discs at 1.2 mm each)"));

module sector(r0, r1, a0, a1, z0, z1) {
    rotate([0, 0, a0]) rotate_extrude(angle = a1 - a0)
        polygon([[r0, z0], [r1, z0], [r1, z1], [r0, z1]]);
}

// ---------------------------------------------------------------- base

module lug() {
    rotate([0, 0, -lug_ang / 2]) rotate_extrude(angle = lug_ang)
        polygon([[plinth_r - 1.2, lug_z0],
                 [plinth_r, lug_z0],
                 [lug_r, lug_z0 + lug_proj],
                 [lug_r, lug_top],
                 [plinth_r - 1.2, lug_top]]);
}

module bump() {
    intersection() {
        translate([plinth_r + bump_h - bump_r, 0, flange_t - eps]) {
            cylinder(r = bump_r, h = bump_len - 1 + eps, $fn = 48);
            translate([0, 0, bump_len - 1])
                cylinder(r1 = bump_r, r2 = bump_r - 1, h = 1, $fn = 48);
        }
        sector(plinth_r - 1, plinth_r + 5, -10, 10, 0, plinth_top);
    }
}

// Slits that free a tangential arm of the locking ring so the bump can spring inward.
module arm_slits() {
    a0 = -arm_free;
    a1 = a0 + arm_ang;
    h = plinth_top + 2;
    // free end: through the ring wall and the flange
    rotate([0, 0, a0]) translate([arm_r0 - slit_w, -slit_w, -1])
        cube([arm_r1 - arm_r0 + 2 * slit_w, slit_w, h]);
    // inside and outside of the arm's foot: through the flange only
    sector(arm_r0 - slit_w, arm_r0, a0 - 0.5, a1, -1, flange_t + eps);
    sector(arm_r1, arm_r1 + slit_w, a0 - 0.5, a1, -1, flange_t + 1);
    for (r = [arm_r0 - slit_w / 2, arm_r1 + slit_w / 2])
        rotate([0, 0, a1]) translate([r, 0, -1])
            cylinder(d = slit_w, h = flange_t + 1 + eps, $fn = 24);
}

module base() {
    rib_t = 2.4;
    difference() {
        union() {
            // flange
            rotate_extrude()
                polygon([[0, 0], [flange_r - 0.6, 0], [flange_r, 0.6],
                         [flange_r, flange_t - 0.4], [flange_r - 0.4, flange_t],
                         [0, flange_t]]);
            // locking ring
            rotate_extrude()
                polygon([[arm_r0, flange_t - eps], [plinth_r, flange_t - eps],
                         [plinth_r, plinth_top - 1], [plinth_r - 1, plinth_top],
                         [arm_r0, plinth_top]]);
            // hub and spindle
            rotate_extrude()
                polygon([[0, flange_t - eps], [hub_r, flange_t - eps],
                         [hub_r, seat_z - 0.6], [hub_r - 0.6, seat_z],
                         [spindle_r, seat_z], [spindle_r, spindle_top - tip_h],
                         [tip_r, spindle_top], [0, spindle_top]]);
            // ribs from the hub out to each lug
            for (i = [0 : n_lugs - 1]) rotate([0, 0, i * 360 / n_lugs])
                translate([hub_r - 1, -rib_t / 2, flange_t - eps])
                    cube([arm_r0 - hub_r + 2, rib_t, plinth_h - 1]);
            for (i = [0 : n_lugs - 1]) rotate([0, 0, i * 360 / n_lugs]) lug();
            if (detent) for (a = bump_angles) rotate([0, 0, a]) bump();
        }
        if (detent) for (a = bump_angles) rotate([0, 0, a]) arm_slits();
    }
}

// ----------------------------------------------------------------- cap

module grip_profile() {
    circle(r = band_r, $fn = 240);
    for (i = [0 : n_ribs - 1]) rotate(i * 360 / n_ribs)
        translate([band_r, 0]) circle(r = rib_h, $fn = 20);
}

module cap_shell() {
    difference() {
        intersection() {
            rotate_extrude($fn = 240)
                polygon([[0, rim_z], [grip_r - 0.6, rim_z], [grip_r, rim_z + 0.6],
                         [grip_r, band_top],
                         [body_r, band_top + grip_r - body_r],
                         [body_r, total_h - 1.2], [body_r - 1.2, total_h],
                         [0, total_h]]);
            union() {
                linear_extrude(height = band_top + grip_r - body_r + 1) grip_profile();
                translate([0, 0, band_top]) cylinder(r = band_r, h = total_h);
            }
        }
        // cavity, with a lead-in chamfer at the rim
        rotate_extrude($fn = 240)
            polygon([[0, rim_z - 1], [cap_ir + 1.5, rim_z - 1],
                     [cap_ir, rim_z + 0.5], [cap_ir, ceil_z], [0, ceil_z]]);
    }
    // socket that steadies the spindle tip
    rotate_extrude()
        polygon([[sock_ir + 0.8, sock_z0], [sock_or, sock_z0],
                 [sock_or, ceil_z + eps], [sock_ir, ceil_z + eps],
                 [sock_ir, sock_z0 + 0.8]]);
}

// L-shaped track: straight down over the lug, then a quarter-twist under the rim.
module track() {
    rotate([0, 0, -slot_ang / 2]) rotate_extrude(angle = slot_ang)
        polygon([[cap_ir - 0.5, rim_z - 1], [groove_r, rim_z - 1],
                 [groove_r, track_top], [cap_ir - 0.5, track_top]]);
    rotate_extrude(angle = track_end)
        polygon([[cap_ir - 0.5, track_z0 - 0.5],
                 [groove_r, track_z0 + groove_depth],
                 [groove_r, track_top], [cap_ir - 0.5, track_top]]);
}

module notch() {
    translate([cap_ir + notch_depth - notch_r, 0, rim_z - 1])
        cylinder(r = notch_r, h = notch_len + 1, $fn = 48);
}

// Modelled in the drop-on position, standing on the base.
module cap() {
    difference() {
        cap_shell();
        for (i = [0 : n_lugs - 1]) rotate([0, 0, i * 360 / n_lugs]) {
            track();
            if (detent) for (a = [bump_ang, bump_ang + twist])
                rotate([0, 0, a]) notch();
        }
    }
}

// -------------------------------------------------------------- output

module assembly() {
    color("DimGray") base();
    color("SteelBlue", 0.55) rotate([0, 0, locked ? -twist : 0]) cap();
}

if (part == "base") base();
else if (part == "cap") translate([0, 0, total_h]) rotate([180, 0, 0]) cap();
else if (part == "section") difference() {
    assembly();
    translate([-200, -400, -1]) cube([400, 400, 400]);
}
else if (part == "exploded") {
    color("DimGray") base();
    color("SteelBlue") translate([0, 0, 150]) cap();
}
else assembly();
