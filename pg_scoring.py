"""
scoring.py
Scoring line geometry — cuts shallow grooves into the Level 1 panel face.
"""

import bpy
import bmesh
import random
from mathutils import Vector
from typing import List, Tuple


def add_scoring_lines(
    panel_obj: bpy.types.Object,
    seed: int,
    depth_fraction: float = 0.3,
    width_fraction: float = 0.01,
) -> None:
    """
    Cut 1-3 shallow grooves into the top face of panel_obj via BMesh.
    Call immediately after create_panel() for Level 1, before child panels.
    Each groove independently picks horizontal or vertical orientation.
    Uses bmesh.ops.bisect_plane to correctly cut the existing top face.

    Parameters
    ----------
    panel_obj      : Blender mesh object to score (Level 1 base plate)
    seed           : random seed
    depth_fraction : groove depth as fraction of panel thickness
    width_fraction : groove width as fraction of panel's shorter dimension
    """
    rng = random.Random(seed)

    dims         = panel_obj.dimensions
    width        = dims.x
    height       = dims.y
    thickness    = dims.z
    groove_depth = thickness * depth_fraction
    groove_width = min(width, height) * width_fraction
    line_count   = rng.randint(1, 3)
    edge_margin  = 0.1

    lines: List[Tuple[str, float]] = []
    for _ in range(line_count):
        orientation = rng.choice(["horizontal", "vertical"])
        span        = height if orientation == "horizontal" else width
        pos         = rng.uniform(span * edge_margin, span * (1.0 - edge_margin))
        lines.append((orientation, pos))

    me = panel_obj.data
    bm = bmesh.new()
    bm.from_mesh(me)

    for orientation, pos in lines:
        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        top_face = max(bm.faces, key=lambda f: f.calc_center_median().z)
        face_z   = top_face.calc_center_median().z

        if orientation == "horizontal":
            co_lo  = Vector((0.0, pos - groove_width / 2, face_z))
            co_hi  = Vector((0.0, pos + groove_width / 2, face_z))
            normal = Vector((0.0, 1.0, 0.0))
        else:
            co_lo  = Vector((pos - groove_width / 2, 0.0, face_z))
            co_hi  = Vector((pos + groove_width / 2, 0.0, face_z))
            normal = Vector((1.0, 0.0, 0.0))

        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=co_lo,
            plane_no=normal,
            clear_inner=False,
            clear_outer=False,
        )

        bm.faces.ensure_lookup_table()
        bm.verts.ensure_lookup_table()
        bm.edges.ensure_lookup_table()

        bmesh.ops.bisect_plane(
            bm,
            geom=bm.verts[:] + bm.edges[:] + bm.faces[:],
            plane_co=co_hi,
            plane_no=normal,
            clear_inner=False,
            clear_outer=False,
        )

        bm.faces.ensure_lookup_table()

        if orientation == "horizontal":
            groove_faces = [
                f for f in bm.faces
                if (abs(f.calc_center_median().z - face_z) < groove_depth * 0.5
                    and pos - groove_width / 2 <= f.calc_center_median().y <= pos + groove_width / 2)
            ]
        else:
            groove_faces = [
                f for f in bm.faces
                if (abs(f.calc_center_median().z - face_z) < groove_depth * 0.5
                    and pos - groove_width / 2 <= f.calc_center_median().x <= pos + groove_width / 2)
            ]

        if groove_faces:
            result    = bmesh.ops.extrude_face_region(bm, geom=groove_faces)
            new_verts = [v for v in result["geom"] if isinstance(v, bmesh.types.BMVert)]
            bmesh.ops.translate(bm, verts=new_verts, vec=(0.0, 0.0, -groove_depth))
            bmesh.ops.delete(bm, geom=groove_faces, context="FACES")

    bmesh.ops.recalc_face_normals(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()
    me.update()
