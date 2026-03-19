"""
rivets.py
UV sphere rivets embedded into Level 3 panel faces.
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
from typing import List, Optional, Tuple

from pg_primitives import link_to_collection

def add_rivets(
    panel_obj: bpy.types.Object,
    seed: int,
    count_range: Tuple[int, int] = (2, 5),
    radius_fraction: Tuple[float, float] = (0.04, 0.08),
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

    Place 2-5 UV spheres embedded into a Level 3 panel face.
    Sphere centres sit at the panel top face Z — half protrudes above,
    half is submerged. No BMesh needed.
    Radius is uniform random within radius_fraction * shorter panel dimension.
    Distance check prevents spheres overlapping.

    Parameters
    ----------
    panel_obj        : Level 3 panel object
    seed             : random seed
    count_range      : (min, max) rivets per panel
    radius_fraction  : (min, max) radius as fraction of shorter panel dimension
    collection       : Blender collection to link rivet objects into

    Returns
    -------
    List of created UV sphere objects
    """
    rng = random.Random(seed + 3333)

    loc     = panel_obj.matrix_world.translation
    dims    = panel_obj.dimensions
    min_dim = min(dims.x, dims.y)

    face_min_x = loc.x
    face_max_x = loc.x + dims.x
    face_min_y = loc.y
    face_max_y = loc.y + dims.y
    face_z     = loc.z + dims.z

    count   = rng.randint(*count_range)
    created = []
    placed  = []
    max_attempts = 100

    for i in range(count):
        radius = min_dim * rng.uniform(*radius_fraction)

        for _attempt in range(max_attempts):
            cx = rng.uniform(face_min_x + radius, face_max_x - radius)
            cy = rng.uniform(face_min_y + radius, face_max_y - radius)

            overlap = any(
                math.sqrt((cx - px) ** 2 + (cy - py) ** 2) < radius + pr
                for (px, py, pr) in placed
            )
            if not overlap:
                placed.append((cx, cy, radius))
                break
        else:
            continue

        name = f"rivet_L3_{panel_obj.name}_r{i}"
        bpy.ops.mesh.primitive_uv_sphere_add(
            radius=radius,
            segments=8,
            ring_count=5,
            location=(cx, cy, face_z),
        )
        obj = bpy.context.active_object
        obj.name = name
        obj.data.name = name + "_mesh"
        obj.parent = panel_obj
        obj.matrix_parent_inverse = panel_obj.matrix_world.inverted()

        if collection is not None:
            link_to_collection(obj, collection)

        created.append(obj)

    return created
