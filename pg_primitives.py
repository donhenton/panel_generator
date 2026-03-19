"""
primitives.py
Collection helpers and panel primitive factory.
"""

import bpy
from mathutils import Vector
from typing import Tuple, Optional


# ---------------------------------------------------------------------------
# Collection Helpers
# ---------------------------------------------------------------------------

def get_or_create_collection(name: str) -> bpy.types.Collection:
    """
    Return the named collection, creating and linking it to the scene
    if it does not already exist.
    """
    if name in bpy.data.collections:
        return bpy.data.collections[name]
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def link_to_collection(
    obj: bpy.types.Object,
    collection: bpy.types.Collection,
) -> None:
    """
    Link obj to collection, unlinking it from any collection it currently
    belongs to. Geometric parenting is unaffected.
    """
    for col in obj.users_collection:
        col.objects.unlink(obj)
    collection.objects.link(obj)


# ---------------------------------------------------------------------------
# Primitive Factory
# ---------------------------------------------------------------------------

def create_panel(
    width: float,
    height: float,
    thickness: float,
    location: Tuple[float, float, float],
    name: str,
    parent_obj: Optional[bpy.types.Object] = None,
    collection: Optional[bpy.types.Collection] = None,
) -> bpy.types.Object:
    """
    Create a single rectangular prism (cuboid) panel mesh.
    Uses primitive_cube_add scaled so X and Y are large relative to Z,
    forming a thin slab — a sci-fi surface panel.
    Origin is moved to the bottom-left-front corner so top face Z is
    unambiguously origin.z + thickness.

    Parameters
    ----------
    width      : X dimension
    height     : Y dimension
    thickness  : Z dimension (small relative to width and height)
    location   : World-space (x, y, z) of the panel
    name       : Blender object name
    parent_obj : Optional parent Blender object
    collection : Optional Blender collection to link this object into

    Returns
    -------
    bpy.types.Object
    """
    bpy.ops.mesh.primitive_cube_add(size=1.0, location=location)
    obj = bpy.context.active_object
    obj.name = name
    obj.data.name = name + "_mesh"
    obj.scale = (width, height, thickness)
    bpy.ops.object.transform_apply(scale=True)

    bpy.ops.object.select_all(action="DESELECT")
    obj.select_set(True)
    bpy.context.view_layer.objects.active = obj

    corner_local = Vector((
        min(v[0] for v in obj.bound_box),
        min(v[1] for v in obj.bound_box),
        min(v[2] for v in obj.bound_box),
    ))
    corner_world = obj.matrix_world @ corner_local

    saved_cursor = bpy.context.scene.cursor.location.copy()
    bpy.context.scene.cursor.location = corner_world
    bpy.ops.object.origin_set(type="ORIGIN_CURSOR")
    bpy.context.scene.cursor.location = saved_cursor

    if parent_obj is not None:
        obj.parent = parent_obj
        obj.matrix_parent_inverse = parent_obj.matrix_world.inverted()

    if collection is not None:
        link_to_collection(obj, collection)

    return obj
