"""
materials.py
Procedural material creation for the sci-fi panel generator.
Combines cavity/AO darkening (Option 4) with faint emission on Level 3
and rivets (Option 5) for a clear visual hierarchy.

Each function builds a node tree from scratch — no UV maps, no external
assets. One material per level assigned via assign_level_materials().
"""

import sys
import os
import bpy

try:
    _dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _dir = os.path.dirname(
        os.path.abspath(bpy.context.space_data.text.filepath)
    )
if _dir not in sys.path:
    sys.path.append(_dir)

import random
from typing import Tuple, Optional

def _node(tree, node_type: str, location: Tuple[float, float]):
    n = tree.nodes.new(type=node_type)
    n.location = location
    return n


def _link(tree, from_node, from_socket: str, to_node, to_socket: str) -> None:
    tree.links.new(from_node.outputs[from_socket], to_node.inputs[to_socket])


def _clear(mat: bpy.types.Material) -> any:
    mat.use_nodes = True
    mat.node_tree.nodes.clear()
    return mat.node_tree


# ---------------------------------------------------------------------------
# Material Factories
# ---------------------------------------------------------------------------

def create_material_level1(
    name: str = "mat_level1",
    base_color: Tuple[float, float, float] = (0.08, 0.09, 0.10),
    roughness: float = 0.7,
    metallic: float = 0.85,
    ao_strength: float = 0.6,
) -> bpy.types.Material:
    """

import sys
import os
import bpy

try:
    _dir = os.path.dirname(os.path.abspath(__file__))
except NameError:
    _dir = os.path.dirname(
        os.path.abspath(bpy.context.space_data.text.filepath)
    )
if _dir not in sys.path:
    sys.path.append(_dir)

    Level 1 — dark steel base plate.
    Ambient occlusion node feeds into base color to darken cavities and
    scoring line grooves, giving depth without complex lighting.

    Node graph
    ----------
    AO ──► ColorRamp (dark→base) ──► Mix with base_color ──► Principled Base Color
    Principled BSDF ──► Output
    """
    mat  = bpy.data.materials.new(name=name)
    tree = _clear(mat)

    output      = _node(tree, "ShaderNodeOutputMaterial",  (600,   0))
    principled  = _node(tree, "ShaderNodeBsdfPrincipled",  (300,   0))
    mix_color   = _node(tree, "ShaderNodeMixRGB",          (  0, 100))
    ao          = _node(tree, "ShaderNodeAmbientOcclusion", (-300, 100))
    ao_ramp     = _node(tree, "ShaderNodeValToRGB",         (-100, 100))

    principled.inputs["Metallic"].default_value   = metallic
    principled.inputs["Roughness"].default_value  = roughness
    principled.inputs["Base Color"].default_value = (*base_color, 1.0)

    ao.inputs["Distance"].default_value = 0.5
    ao.samples = 8

    # AO ramp — maps 0 (occluded) to dark, 1 (open) to base color
    ao_ramp.color_ramp.elements[0].position = 0.0
    ao_ramp.color_ramp.elements[0].color    = (0.02, 0.02, 0.02, 1.0)
    ao_ramp.color_ramp.elements[1].position = 1.0
    ao_ramp.color_ramp.elements[1].color    = (*base_color, 1.0)

    mix_color.blend_type = "MIX"
    mix_color.inputs["Fac"].default_value        = ao_strength
    mix_color.inputs["Color1"].default_value     = (*base_color, 1.0)

    _link(tree, ao,         "AO",    ao_ramp,    "Fac")
    _link(tree, ao_ramp,    "Color", mix_color,  "Color2")
    _link(tree, mix_color,  "Color", principled, "Base Color")
    _link(tree, principled, "BSDF",  output,     "Surface")

    return mat


def create_material_level2(
    name: str = "mat_level2",
    base_color: Tuple[float, float, float] = (0.18, 0.20, 0.23),
    roughness: float = 0.55,
    metallic: float = 0.75,
    ao_strength: float = 0.5,
) -> bpy.types.Material:
    """
    Level 2 — mid-tone raised sub-panels.
    Noticeably lighter than Level 1. Same AO cavity darkening approach.
    Slightly lower roughness — reads as a machined finish vs cast plate.
    """
    mat  = bpy.data.materials.new(name=name)
    tree = _clear(mat)

    output     = _node(tree, "ShaderNodeOutputMaterial",   (600,   0))
    principled = _node(tree, "ShaderNodeBsdfPrincipled",   (300,   0))
    mix_color  = _node(tree, "ShaderNodeMixRGB",           (  0, 100))
    ao         = _node(tree, "ShaderNodeAmbientOcclusion", (-300, 100))
    ao_ramp    = _node(tree, "ShaderNodeValToRGB",         (-100, 100))

    principled.inputs["Metallic"].default_value   = metallic
    principled.inputs["Roughness"].default_value  = roughness
    principled.inputs["Base Color"].default_value = (*base_color, 1.0)

    ao.inputs["Distance"].default_value = 0.3
    ao.samples = 8

    ao_ramp.color_ramp.elements[0].position = 0.0
    ao_ramp.color_ramp.elements[0].color    = (0.04, 0.04, 0.05, 1.0)
    ao_ramp.color_ramp.elements[1].position = 1.0
    ao_ramp.color_ramp.elements[1].color    = (*base_color, 1.0)

    mix_color.blend_type = "MIX"
    mix_color.inputs["Fac"].default_value    = ao_strength
    mix_color.inputs["Color1"].default_value = (*base_color, 1.0)

    _link(tree, ao,         "AO",    ao_ramp,    "Fac")
    _link(tree, ao_ramp,    "Color", mix_color,  "Color2")
    _link(tree, mix_color,  "Color", principled, "Base Color")
    _link(tree, principled, "BSDF",  output,     "Surface")

    return mat


def create_material_level3(
    name: str = "mat_level3",
    base_color: Tuple[float, float, float] = (0.30, 0.33, 0.38),
    roughness: float = 0.45,
    metallic: float = 0.6,
    ao_strength: float = 0.4,
    emission_strength: float = 0.08,
    emission_color: Tuple[float, float, float] = (0.4, 0.7, 1.0),
) -> bpy.types.Material:
    """
    Level 3 — lighter detail panels with faint emission.
    The emission is subtle — not a glow, just enough energy to separate
    Level 3 from Level 2 under flat lighting. Cool blue-white tone.

    Node graph
    ----------
    AO ──► ColorRamp ──► Mix ──► Principled Base Color
    Emission (faint) ──► Add Shader ──► Output
    Principled BSDF  ──┘
    """
    mat  = bpy.data.materials.new(name=name)
    tree = _clear(mat)

    output     = _node(tree, "ShaderNodeOutputMaterial",   (800,   0))
    add_shader = _node(tree, "ShaderNodeAddShader",        (600,   0))
    principled = _node(tree, "ShaderNodeBsdfPrincipled",   (300,  80))
    emission   = _node(tree, "ShaderNodeEmission",         (300, -80))
    mix_color  = _node(tree, "ShaderNodeMixRGB",           (  0, 150))
    ao         = _node(tree, "ShaderNodeAmbientOcclusion", (-300, 150))
    ao_ramp    = _node(tree, "ShaderNodeValToRGB",         (-100, 150))

    principled.inputs["Metallic"].default_value   = metallic
    principled.inputs["Roughness"].default_value  = roughness
    principled.inputs["Base Color"].default_value = (*base_color, 1.0)

    emission.inputs["Color"].default_value    = (*emission_color, 1.0)
    emission.inputs["Strength"].default_value = emission_strength

    ao.inputs["Distance"].default_value = 0.15
    ao.samples = 8

    ao_ramp.color_ramp.elements[0].position = 0.0
    ao_ramp.color_ramp.elements[0].color    = (0.06, 0.07, 0.08, 1.0)
    ao_ramp.color_ramp.elements[1].position = 1.0
    ao_ramp.color_ramp.elements[1].color    = (*base_color, 1.0)

    mix_color.blend_type = "MIX"
    mix_color.inputs["Fac"].default_value    = ao_strength
    mix_color.inputs["Color1"].default_value = (*base_color, 1.0)

    _link(tree, ao,         "AO",    ao_ramp,    "Fac")
    _link(tree, ao_ramp,    "Color", mix_color,  "Color2")
    _link(tree, mix_color,  "Color", principled, "Base Color")
    _link(tree, principled, "BSDF",  add_shader, "Shader")
    _link(tree, emission,   "Emission", add_shader, "Shader_001")
    _link(tree, add_shader, "Shader",   output,     "Surface")

    return mat


def create_material_pipes(
    name: str = "mat_pipes",
    base_color: Tuple[float, float, float] = (0.12, 0.10, 0.07),
    roughness: float = 0.4,
    metallic: float = 0.9,
) -> bpy.types.Material:
    """
    Pipes — dark copper/bronze tone, high metallic, lower roughness.
    Distinct from all panel levels — reads immediately as a different
    material class (conduit vs structural panel).
    """
    mat  = bpy.data.materials.new(name=name)
    tree = _clear(mat)

    output     = _node(tree, "ShaderNodeOutputMaterial",  (400, 0))
    principled = _node(tree, "ShaderNodeBsdfPrincipled",  (100, 0))

    principled.inputs["Base Color"].default_value = (*base_color, 1.0)
    principled.inputs["Metallic"].default_value   = metallic
    principled.inputs["Roughness"].default_value  = roughness

    _link(tree, principled, "BSDF", output, "Surface")

    return mat


def create_material_rivets(
    name: str = "mat_rivets",
    base_color: Tuple[float, float, float] = (0.7, 0.72, 0.75),
    roughness: float = 0.25,
    metallic: float = 1.0,
    emission_strength: float = 0.15,
    emission_color: Tuple[float, float, float] = (0.8, 0.9, 1.0),
) -> bpy.types.Material:
    """
    Rivets — near-white polished metal with a faint cold emission.
    High contrast against the dark Level 3 panels. The emission gives
    them a slight active/powered feel — indicator lights or sensor nodules.
    """
    mat  = bpy.data.materials.new(name=name)
    tree = _clear(mat)

    output     = _node(tree, "ShaderNodeOutputMaterial",  (600,  0))
    add_shader = _node(tree, "ShaderNodeAddShader",       (400,  0))
    principled = _node(tree, "ShaderNodeBsdfPrincipled",  (100, 80))
    emission   = _node(tree, "ShaderNodeEmission",        (100,-80))

    principled.inputs["Base Color"].default_value = (*base_color, 1.0)
    principled.inputs["Metallic"].default_value   = metallic
    principled.inputs["Roughness"].default_value  = roughness

    emission.inputs["Color"].default_value    = (*emission_color, 1.0)
    emission.inputs["Strength"].default_value = emission_strength

    _link(tree, principled, "BSDF",     add_shader, "Shader")
    _link(tree, emission,   "Emission", add_shader, "Shader_001")
    _link(tree, add_shader, "Shader",   output,     "Surface")

    return mat


# ---------------------------------------------------------------------------
# Assignment
# ---------------------------------------------------------------------------

def assign_level_materials(
    collections: dict,
    mat_l1: bpy.types.Material,
    mat_l2: bpy.types.Material,
    mat_l3: bpy.types.Material,
    mat_pipes: bpy.types.Material,
    mat_rivets: bpy.types.Material,
) -> None:
    """
    Assign materials to all objects in each level collection.
    Object type is inferred from name prefix:
      panel_L1  -> mat_l1
      panel_L2  -> mat_l2
      panel_L3  -> mat_l3
      pipe_     -> mat_pipes
      rivet_    -> mat_rivets

    Parameters
    ----------
    collections : dict mapping level int to bpy.types.Collection
    mat_l1      : Level 1 panel material
    mat_l2      : Level 2 panel material
    mat_l3      : Level 3 panel material
    mat_pipes   : pipe material
    mat_rivets  : rivet material
    """
    name_to_mat = {
        "panel_L1": mat_l1,
        "panel_L2": mat_l2,
        "panel_L3": mat_l3,
        "pipe_":    mat_pipes,
        "rivet_":   mat_rivets,
    }

    all_collections = list(collections.values())

    for col in all_collections:
        for obj in col.objects:
            mat = None
            for prefix, m in name_to_mat.items():
                if obj.name.startswith(prefix):
                    mat = m
                    break
            if mat is not None and obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(mat)
