#!/usr/bin/env python3
"""Build a Q-version chibi blockout of 大肥鱼 in Blender.

This is a shape/colour exploration, not the final rigged model. It writes a
.blend file plus front / three-quarter / side preview renders.

Run with:

    /Applications/Blender.app/Contents/MacOS/Blender -b \
      --python toon3d/build_blockout.py -- \
      --blend /path/to/大肥鱼_blockout.blend \
      --preview-dir /path/to/preview
"""

from __future__ import annotations

import argparse
import math
import sys
from pathlib import Path

import bpy
from mathutils import Vector

CHARACTER = None
STUDIO = None


def parse_args():
    argv = sys.argv
    argv = argv[argv.index("--") + 1:] if "--" in argv else []
    parser = argparse.ArgumentParser()
    parser.add_argument("--blend", type=Path, required=True)
    parser.add_argument("--preview-dir", type=Path, required=True)
    return parser.parse_args(argv)


def collection(name: str):
    coll = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(coll)
    return coll


def move_to(obj, coll):
    for old in list(obj.users_collection):
        old.objects.unlink(obj)
    coll.objects.link(obj)


def apply_scale(obj):
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    obj.select_set(False)


def finish(obj, name, mat, smooth=True):
    obj.name = name
    if mat:
        obj.data.materials.append(mat)
    if smooth:
        bpy.ops.object.shade_smooth()
    move_to(obj, CHARACTER)
    return obj


def sphere(name, loc, scale, mat, segments=40, rings=20, rot=(0, 0, 0)):
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=segments, ring_count=rings, radius=1.0, location=loc
    )
    obj = bpy.context.object
    obj.scale = scale
    obj.rotation_euler = rot
    apply_scale(obj)
    return finish(obj, name, mat)


def cone(name, loc, radius1, radius2, depth, mat, rot=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cone_add(
        vertices=vertices, radius1=radius1, radius2=radius2,
        depth=depth, location=loc, rotation=rot,
    )
    obj = bpy.context.object
    return finish(obj, name, mat)


def cylinder(name, loc, radius, depth, mat, rot=(0, 0, 0), vertices=32):
    bpy.ops.mesh.primitive_cylinder_add(
        vertices=vertices, radius=radius, depth=depth,
        location=loc, rotation=rot,
    )
    obj = bpy.context.object
    return finish(obj, name, mat)


def torus(name, loc, major, minor, mat, rot=(0, 0, 0), major_segments=64, minor_segments=10):
    bpy.ops.mesh.primitive_torus_add(
        major_radius=major, minor_radius=minor,
        major_segments=major_segments, minor_segments=minor_segments,
        location=loc, rotation=rot,
    )
    obj = bpy.context.object
    return finish(obj, name, mat)


def curve(name, points, bevel, mat, cyclic=False, radii=None):
    data = bpy.data.curves.new(name + "Curve", type="CURVE")
    data.dimensions = "3D"
    data.resolution_u = 24
    data.bevel_depth = bevel
    data.bevel_resolution = 4
    spline = data.splines.new("POLY")
    spline.points.add(len(points) - 1)
    for index, (point, co) in enumerate(zip(spline.points, points)):
        point.co = (*co, 1.0)
        if radii:
            point.radius = radii[index]
    spline.use_cyclic_u = cyclic
    obj = bpy.data.objects.new(name, data)
    CHARACTER.objects.link(obj)
    obj.data.materials.append(mat)
    return obj


def capsule(name, a, b, radius, mat):
    a, b = Vector(a), Vector(b)
    vec = b - a
    mid = (a + b) * 0.5
    obj = cylinder(name, mid, radius, vec.length, mat)
    obj.rotation_euler = vec.to_track_quat("Z", "Y").to_euler()
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.transform_apply(location=False, rotation=True, scale=False)
    obj.select_set(False)
    for suffix, point in (("A", a), ("B", b)):
        sphere(name + suffix, point, (radius, radius, radius), mat, 24, 12)
    return obj


def srgb_channel(value: float) -> float:
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def srgb(rgb):
    return tuple(srgb_channel(value) for value in rgb)


def cut_face_opening(obj, loc, scale):
    """Carve a face opening into the hair cap so it frames the head."""
    bpy.ops.mesh.primitive_uv_sphere_add(
        segments=32, ring_count=18, radius=1.0, location=loc
    )
    cutter = bpy.context.object
    cutter.scale = scale
    apply_scale(cutter)
    modifier = obj.modifiers.new("FaceOpening", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.solver = "EXACT"
    modifier.object = cutter
    bpy.context.view_layer.objects.active = obj
    obj.select_set(True)
    bpy.ops.object.modifier_apply(modifier=modifier.name)
    obj.select_set(False)
    bpy.data.objects.remove(cutter, do_unlink=True)


def toon(name, base, shade, highlight=None):
    base = srgb(base)
    shade = srgb(shade)
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    nodes = mat.node_tree.nodes
    links = mat.node_tree.links
    nodes.clear()

    out = nodes.new("ShaderNodeOutputMaterial")
    diffuse = nodes.new("ShaderNodeBsdfDiffuse")
    diffuse.inputs["Color"].default_value = (1, 1, 1, 1)
    to_rgb = nodes.new("ShaderNodeShaderToRGB")
    ramp = nodes.new("ShaderNodeValToRGB")
    ramp.color_ramp.interpolation = "CONSTANT"
    ramp.color_ramp.elements[0].position = 0.0
    ramp.color_ramp.elements[0].color = (*shade, 1)
    ramp.color_ramp.elements[1].position = 0.48
    ramp.color_ramp.elements[1].color = (*base, 1)
    emission = nodes.new("ShaderNodeEmission")
    emission.inputs["Strength"].default_value = 1.0

    links.new(diffuse.outputs[0], to_rgb.inputs[0])
    links.new(to_rgb.outputs["Color"], ramp.inputs["Fac"])
    links.new(ramp.outputs["Color"], emission.inputs["Color"])
    links.new(emission.outputs[0], out.inputs["Surface"])

    mat.diffuse_color = (*base, 1)
    return mat


def studio_mat(name, color, rough=1.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    bsdf.inputs["Base Color"].default_value = (*color, 1)
    bsdf.inputs["Roughness"].default_value = rough
    return mat


def look_at(obj, target):
    direction = Vector(target) - obj.location
    obj.rotation_euler = direction.to_track_quat("-Z", "Y").to_euler()


def setup_scene():
    global CHARACTER, STUDIO
    bpy.ops.wm.read_factory_settings(use_empty=True)
    scene = bpy.context.scene

    CHARACTER = collection("Character")
    STUDIO = collection("Studio")

    scene.render.engine = "BLENDER_EEVEE_NEXT"
    scene.render.resolution_x = 900
    scene.render.resolution_y = 1200
    scene.render.resolution_percentage = 100
    scene.render.image_settings.file_format = "PNG"
    scene.render.image_settings.color_mode = "RGBA"
    scene.render.film_transparent = False
    scene.render.fps = 24
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.look = "None"
    scene.eevee.taa_render_samples = 32

    scene.world = bpy.data.worlds.new("StudioWorld")
    scene.world.use_nodes = True
    bg = scene.world.node_tree.nodes["Background"]
    bg.inputs["Color"].default_value = (0.88, 0.87, 0.84, 1)
    bg.inputs["Strength"].default_value = 0.8

    # Studio floor and back wall.
    mat = studio_mat("StudioPaper", (0.84, 0.83, 0.80))
    bpy.ops.mesh.primitive_plane_add(size=20, location=(0, 0, 0))
    floor = bpy.context.object
    floor.name = "StudioFloor"
    floor.data.materials.append(mat)
    move_to(floor, STUDIO)
    bpy.ops.mesh.primitive_plane_add(
        size=20, location=(0, 3.0, 5.0), rotation=(math.radians(90), 0, 0)
    )
    wall = bpy.context.object
    wall.name = "StudioWall"
    wall.data.materials.append(mat)
    move_to(wall, STUDIO)

    # Lights: one key sun and one soft fill.
    bpy.ops.object.light_add(type="SUN", location=(3.0, -4.0, 6.0))
    key = bpy.context.object
    key.name = "Key"
    key.data.energy = 3.2
    key.data.angle = math.radians(18)
    look_at(key, (0, 0, 0.8))
    move_to(key, STUDIO)

    bpy.ops.object.light_add(type="AREA", location=(-3.0, -2.0, 3.0))
    fill = bpy.context.object
    fill.name = "Fill"
    fill.data.energy = 80
    fill.data.shape = "DISK"
    fill.data.size = 5
    look_at(fill, (0, 0, 0.9))
    move_to(fill, STUDIO)

    return scene


def build_character():
    skin = toon("Skin", (0.98, 0.78, 0.68), (0.96, 0.61, 0.55), (1.0, 0.88, 0.80))
    skin_dark = toon("SkinShade", (0.95, 0.68, 0.62), (0.86, 0.48, 0.48))
    blue = toon("HairBlue", (0.12, 0.35, 0.78), (0.05, 0.16, 0.42), (0.22, 0.52, 0.95))
    blue_light = toon("HairLight", (0.28, 0.55, 0.92), (0.10, 0.27, 0.62), (0.45, 0.70, 1.0))
    navy = toon("DressNavy", (0.055, 0.10, 0.24), (0.02, 0.04, 0.12), (0.10, 0.18, 0.36))
    navy_light = toon("DressNavyLight", (0.10, 0.18, 0.36), (0.03, 0.06, 0.16))
    white = toon("ApronWhite", (0.96, 0.94, 0.90), (0.73, 0.71, 0.70), (1.0, 0.99, 0.96))
    white_shade = toon("FrillShade", (0.88, 0.85, 0.82), (0.65, 0.63, 0.65))
    pink = toon("Blush", (0.96, 0.52, 0.60), (0.78, 0.30, 0.42))
    eye_dark = toon("EyeDark", (0.03, 0.06, 0.16), (0.01, 0.02, 0.08))
    iris = toon("IrisBlue", (0.16, 0.52, 0.95), (0.05, 0.22, 0.58), (0.40, 0.72, 1.0))
    pupil = toon("Pupil", (0.01, 0.02, 0.08), (0.005, 0.01, 0.04))
    highlight = toon("EyeHighlight", (1, 1, 1), (0.90, 0.94, 1.0))
    mouth = toon("Mouth", (0.72, 0.20, 0.28), (0.45, 0.08, 0.16))
    ribbon = toon("RibbonBlue", (0.12, 0.32, 0.72), (0.04, 0.12, 0.34), (0.25, 0.48, 0.92))
    gold = toon("Gold", (0.82, 0.62, 0.24), (0.45, 0.28, 0.08), (1.0, 0.82, 0.42))

    # Head and neck.
    sphere("Head", (0, 0, 1.15), (0.46, 0.43, 0.45), skin, 48, 28)
    cylinder("Neck", (0, 0.01, 0.72), 0.09, 0.16, skin_dark, vertices=24)

    # Hair cap sits slightly behind the face so the face stays visible.
    hair_cap = sphere("HairCap", (0, 0.075, 1.18), (0.48, 0.44, 0.48), blue, 48, 28)
    cut_face_opening(hair_cap, (0, -0.32, 1.12), (0.32, 0.29, 0.34))
    sphere("HairTopFront", (0, -0.18, 1.43), (0.38, 0.15, 0.12), blue, 40, 20)
    # Back hair mass.
    sphere("HairBack", (0, 0.18, 1.00), (0.38, 0.26, 0.46), blue, 40, 24)

    # Soft bang locks: tapered curves, one silhouette each.
    bang_specs = [
        (-0.28, 0.085, 1.23),
        (-0.14, 0.095, 1.20),
        (0.00, 0.100, 1.22),
        (0.14, 0.095, 1.20),
        (0.28, 0.085, 1.23),
    ]
    for index, (x, width, tip_z) in enumerate(bang_specs):
        curve(
            f"Bang{index}",
            [
                (x * 0.90, -0.32, 1.56),
                (x * 1.00, -0.37, 1.44),
                (x * 1.06, -0.40, 1.33),
                (x * 1.10, -0.415, tip_z),
            ],
            width, blue, radii=[1.0, 0.95, 0.70, 0.28],
        )

    # Wavy side locks: one continuous tapered curve per lock.
    for side in (-1, 1):
        curve(
            f"SideLockOuter{side}",
            [
                (side * 0.46, 0.02, 1.28),
                (side * 0.50, 0.00, 1.06),
                (side * 0.47, -0.02, 0.84),
                (side * 0.51, -0.03, 0.61),
                (side * 0.46, -0.05, 0.37),
                (side * 0.40, -0.06, 0.16),
            ],
            0.105, blue, radii=[1.0, 0.98, 0.86, 0.68, 0.42, 0.10],
        )
        curve(
            f"SideLockInner{side}",
            [
                (side * 0.40, -0.10, 1.26),
                (side * 0.43, -0.10, 1.06),
                (side * 0.40, -0.12, 0.85),
                (side * 0.44, -0.13, 0.63),
                (side * 0.38, -0.14, 0.41),
                (side * 0.34, -0.15, 0.25),
            ],
            0.065, blue_light, radii=[1.0, 0.90, 0.78, 0.60, 0.34, 0.08],
        )
        # Side ribbon bow.
        sphere(f"SideBowL{side}", (side * 0.41, -0.19, 1.29), (0.060, 0.030, 0.042), ribbon, 24, 12)
        sphere(f"SideBowR{side}", (side * 0.49, -0.19, 1.29), (0.060, 0.030, 0.042), ribbon, 24, 12)
        sphere(f"SideBowKnot{side}", (side * 0.45, -0.205, 1.29), (0.030, 0.022, 0.036), blue_light, 20, 10)
    # Ahoge.
    curve(
        "Ahoge",
        [
            (0, 0.0, 1.62), (-0.01, 0.0, 1.68), (0.02, 0.0, 1.74),
            (0.02, 0.0, 1.79), (-0.03, 0.0, 1.81), (-0.07, 0.0, 1.79),
        ],
        0.018, blue_light,
    )

    # Maid headband arc, no floating ruffles in the blockout.
    band_points = []
    for i in range(21):
        t = i / 20
        x = -0.34 + 0.68 * t
        z = 1.43 + 0.15 * math.sin(math.pi * t)
        band_points.append((x, -0.12, z))
    curve("Headband", band_points, 0.034, white)

    # Face.
    for side in (-1, 1):
        x = side * 0.16
        sphere(f"EyeOutline{side}", (x, -0.426, 1.15), (0.095, 0.018, 0.13), eye_dark, 32, 16)
        sphere(f"Iris{side}", (x, -0.441, 1.15), (0.070, 0.010, 0.100), iris, 32, 16)
        sphere(f"Pupil{side}", (x, -0.448, 1.15), (0.036, 0.008, 0.062), pupil, 24, 12)
        sphere(f"Highlight{side}", (x - side * 0.025, -0.454, 1.19), (0.022, 0.006, 0.030), highlight, 20, 10)
        sphere(f"HighlightSmall{side}", (x + side * 0.025, -0.454, 1.11), (0.010, 0.004, 0.014), highlight, 16, 8)
        sphere(f"Blush{side}", (side * 0.29, -0.375, 1.05), (0.065, 0.010, 0.028), pink, 24, 12)
    sphere("Mouth", (0, -0.443, 1.01), (0.055, 0.008, 0.035), mouth, 24, 12)

    # Body.
    sphere("Torso", (0, 0, 0.57), (0.235, 0.16, 0.27), navy, 32, 20)
    cone("Skirt", (0, 0, 0.33), 0.47, 0.22, 0.38, navy, vertices=64)
    torus("Hem", (0, 0, 0.15), 0.44, 0.024, white, major_segments=64, minor_segments=8)
    torus("Waist", (0, 0, 0.535), 0.235, 0.026, navy_light, major_segments=48, minor_segments=8)

    # Apron plane with a bevel.
    mesh = bpy.data.meshes.new("ApronMesh")
    verts = [
        (-0.13, -0.335, 0.53), (0.13, -0.335, 0.53),
        (0.20, -0.395, 0.18), (-0.20, -0.395, 0.18),
    ]
    faces = [(0, 1, 2, 3)]
    mesh.from_pydata(verts, [], faces)
    mesh.update()
    apron = bpy.data.objects.new("Apron", mesh)
    CHARACTER.objects.link(apron)
    apron.data.materials.append(white)
    solid = apron.modifiers.new("Solidify", "SOLIDIFY")
    solid.thickness = 0.012
    bev = apron.modifiers.new("Bevel", "BEVEL")
    bev.width = 0.012
    bev.segments = 2

    # Whale emblem on the apron.
    sphere("WhaleBody", (0, -0.403, 0.30), (0.045, 0.006, 0.025), blue, 24, 12)
    for side in (-1, 1):
        cone(
            f"WhaleTail{side}", (side * 0.055, -0.402, 0.315),
            0.022, 0.005, 0.045, blue, (0, math.radians(side * 55), math.radians(90)),
        )

    # Collar and chest bow.
    torus("Collar", (0, 0, 0.745), 0.135, 0.032, white, major_segments=48, minor_segments=8)
    sphere("ChestBowL", (-0.065, -0.225, 0.735), (0.065, 0.025, 0.040), ribbon, 24, 12)
    sphere("ChestBowR", (0.065, -0.225, 0.735), (0.065, 0.025, 0.040), ribbon, 24, 12)
    sphere("ChestKnot", (0, -0.245, 0.735), (0.035, 0.022, 0.038), blue_light, 20, 10)

    # Sleeves, arms and hands.
    for side in (-1, 1):
        sphere(f"Sleeve{side}", (side * 0.29, 0.0, 0.66), (0.13, 0.12, 0.15), navy, 28, 16)
        capsule(
            f"Arm{side}",
            (side * 0.29, -0.02, 0.61),
            (side * 0.255, -0.20, 0.44),
            0.048, skin,
        )
        sphere(f"Hand{side}", (side * 0.25, -0.205, 0.43), (0.060, 0.058, 0.060), skin, 24, 12)
        torus(
            f"Cuff{side}", (side * 0.285, -0.10, 0.51),
            0.055, 0.018, white_shade,
            rot=(math.radians(90), 0, 0), major_segments=32, minor_segments=8,
        )

    # Legs, socks and shoes.
    for side in (-1, 1):
        cylinder(f"Leg{side}", (side * 0.125, 0, 0.155), 0.052, 0.16, skin, vertices=24)
        cylinder(f"Sock{side}", (side * 0.125, 0, 0.105), 0.060, 0.10, white, vertices=24)
        sphere(f"Shoe{side}", (side * 0.125, -0.045, 0.045), (0.090, 0.15, 0.060), navy, 24, 12)
        sphere(f"ShoeTop{side}", (side * 0.125, -0.07, 0.085), (0.075, 0.095, 0.038), navy_light, 20, 10)

    # A tiny gold trim on the skirt.
    torus("GoldTrim", (0, 0, 0.165), 0.42, 0.008, gold, major_segments=64, minor_segments=6)


def setup_camera(scene):
    bpy.ops.object.camera_add()
    camera = bpy.context.object
    camera.name = "Camera"
    camera.data.type = "ORTHO"
    camera.data.ortho_scale = 2.0
    camera.data.lens = 50
    camera.location = (0, -6.0, 1.05)
    look_at(camera, (0, 0, 0.90))
    scene.camera = camera
    move_to(camera, STUDIO)
    return camera


def render_view(scene, camera, loc, target, path, ortho=2.0, transparent=False):
    camera.location = loc
    camera.data.ortho_scale = ortho
    look_at(camera, target)
    scene.render.film_transparent = transparent
    if transparent:
        for obj in STUDIO.objects:
            obj.hide_render = True
    else:
        for obj in STUDIO.objects:
            obj.hide_render = False
    scene.render.filepath = str(path)
    bpy.ops.render.render(write_still=True)


def setup_freestyle(scene):
    scene.render.use_freestyle = True
    view_layer = scene.view_layers[0]
    view_layer.use_freestyle = True
    lineset = view_layer.freestyle_settings.linesets[0]
    lineset.select_silhouette = True
    lineset.select_border = True
    lineset.select_crease = False
    lineset.select_material_boundary = False
    lineset.select_by_collection = True
    lineset.collection = CHARACTER
    if lineset.linestyle is None:
        lineset.linestyle = bpy.data.linestyles.new("ToonLine")
    lineset.linestyle.color = (0.02, 0.03, 0.08)
    lineset.linestyle.thickness = 1.5


def main():
    args = parse_args()
    args.blend.parent.mkdir(parents=True, exist_ok=True)
    args.preview_dir.mkdir(parents=True, exist_ok=True)

    scene = setup_scene()
    build_character()
    setup_freestyle(scene)
    camera = setup_camera(scene)

    # Save the scene before rendering so it opens with the preview camera.
    bpy.ops.wm.save_as_mainfile(filepath=str(args.blend))

    render_view(
        scene, camera, (0, -6.0, 1.05), (0, 0, 0.90),
        args.preview_dir / "正面.png", 2.0,
    )
    render_view(
        scene, camera, (2.2, -5.8, 1.35), (0, 0, 0.90),
        args.preview_dir / "三分之四.png", 2.0,
    )
    render_view(
        scene, camera, (5.0, -1.4, 1.15), (0, 0, 0.90),
        args.preview_dir / "侧面.png", 2.0,
    )
    render_view(
        scene, camera, (0, -6.0, 1.05), (0, 0, 0.90),
        args.preview_dir / "透明正面.png", 2.0, transparent=True,
    )

    print("BLEND", args.blend)
    for path in sorted(args.preview_dir.glob("*.png")):
        print("PREVIEW", path)


if __name__ == "__main__":
    main()
