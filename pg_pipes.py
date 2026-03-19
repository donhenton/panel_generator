"""
pipes.py
L-shaped cylinder pipe connections between sibling panels.
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

import math
import random
from typing import List, Optional

from pg_primitives import link_to_collection

def add_pipes(
    parent_obj: bpy.types.Object,
    child_panels: List[bpy.types.Object],
    seed: int,
    radius: float = 0.012,
    pipe_probability: float = 0.4,
    collection: Optional[bpy.types.Collection] = None,
) -> List[bpy.types.Object]:
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

    Connect a random subset of sibling panels with L-shaped cylinder pipes.
    Each connection is two cylinder legs — one horizontal (X), one vertical
    (Y) — meeting at an elbow. Both legs parented to parent_obj.

    Parameters
    ----------
    parent_obj      : panel the pipes sit on
    child_panels    : sibling panels to connect
    seed            : random seed
    radius          : cylinder radius
    pipe_probability: probability any given pair gets connected
    collection      : Blender collection to link pipe objects into

    Returns
    -------
    List of created cylinder objects
    """
    if len(child_panels) < 2:
        return []

    rng = random.Random(seed + 9999)

    parent_top_z = parent_obj.matrix_world.translation.z + parent_obj.dimensions.z

    created = []
    pairs = [
        (child_panels[i], child_panels[j])
        for i in range(len(child_panels))
        for j in range(i + 1, len(child_panels))
    ]

    for panel_a, panel_b in pairs:
        if rng.random() > pipe_probability:
            continue

        loc_a = panel_a.matrix_world.translation
        loc_b = panel_b.matrix_world.translation
        dim_a = panel_a.dimensions
        dim_b = panel_b.dimensions

        ax = loc_a.x + dim_a.x / 2
        ay = loc_a.y + dim_a.y / 2
        bx = loc_b.x + dim_b.x / 2
        by = loc_b.y + dim_b.y / 2

        pipe_z  = parent_top_z + radius
        elbow_x = bx
        elbow_y = ay

        # Leg 1 — horizontal along X
        leg1_length = abs(bx - ax)
        if leg1_length > radius * 2:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=radius,
                depth=leg1_length,
                location=((ax + bx) / 2, ay, pipe_z),
            )
            leg1 = bpy.context.active_object
            leg1.name = f"pipe_{panel_a.name}_to_{panel_b.name}_leg1"
            leg1.rotation_euler = (math.pi / 2, 0.0, math.pi / 2)
            leg1.parent = parent_obj
            leg1.matrix_parent_inverse = parent_obj.matrix_world.inverted()
            if collection:
                link_to_collection(leg1, collection)
            created.append(leg1)

        # Leg 2 — vertical along Y
        leg2_length = abs(by - ay)
        if leg2_length > radius * 2:
            bpy.ops.mesh.primitive_cylinder_add(
                radius=radius,
                depth=leg2_length,
                location=(elbow_x, (ay + by) / 2, pipe_z),
            )
            leg2 = bpy.context.active_object
            leg2.name = f"pipe_{panel_a.name}_to_{panel_b.name}_leg2"
            leg2.rotation_euler = (math.pi / 2, 0.0, 0.0)
            leg2.parent = parent_obj
            leg2.matrix_parent_inverse = parent_obj.matrix_world.inverted()
            if collection:
                link_to_collection(leg2, collection)
            created.append(leg2)

    return created
