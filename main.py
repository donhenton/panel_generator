"""
main.py
Sci-Fi Panel Generator — Blender 4.x Python API
Entry point. Run from Blender's scripting workspace.

All parameters are in the if __name__ == "__main__" block at the bottom.
"""

import sys
import os
import bpy

# Resolve the package directory from the active text block filepath.
_dir = os.path.dirname(bpy.context.space_data.text.filepath)
if _dir not in sys.path:
    sys.path.append(_dir)
import random
from typing import Callable, Tuple

from pg_primitives import create_panel, get_or_create_collection
from pg_distribution import distribution_weighted_corner
from pg_scoring import add_scoring_lines
from pg_recursive import generate_child_panels
from pg_materials import (
    create_material_level1,
    create_material_level2,
    create_material_level3,
    create_material_pipes,
    create_material_rivets,
    assign_level_materials,
)


# ---------------------------------------------------------------------------
# Scene Entry Point
# ---------------------------------------------------------------------------

def build_scene(
    base_width: float,
    base_height: float,
    thickness: float,
    seed: int,
    distribution_fn: Callable,
    count_range: Tuple[int, int],
    child_area_fraction: float,
    score_depth_fraction: float = 0.3,
    score_width_fraction: float = 0.01,
    pipe_radius: float = 0.012,
    pipe_probability: float = 0.4,
    rivet_count_range: Tuple[int, int] = (2, 5),
    rivet_radius_fraction: Tuple[float, float] = (0.04, 0.08),
    **dist_kwargs,
) -> None:
    """
    Clear the scene and build the full panel hierarchy, then assign
    procedural materials to all objects.

    Parameters
    ----------
    base_width            : X dimension of the Level 1 base plate
    base_height           : Y dimension of the Level 1 base plate
    thickness             : Z thickness shared by all panels at all levels
    seed                  : random seed for reproducible layouts
    distribution_fn       : placement function
    count_range           : (min, max) child panels per parent
    child_area_fraction   : fraction of parent face area each child occupies
    score_depth_fraction  : scoring groove depth as fraction of thickness
    score_width_fraction  : scoring groove width as fraction of shorter dimension
    pipe_radius           : cylinder radius for pipes
    pipe_probability      : probability any sibling pair gets a pipe connection
    rivet_count_range     : (min, max) rivets per Level 3 panel
    rivet_radius_fraction : (min, max) rivet radius as fraction of shorter dim
    **dist_kwargs         : forwarded to distribution_fn
    """
    # --- Clear scene ---
    bpy.ops.object.select_all(action="SELECT")
    bpy.ops.object.delete(use_global=False)

    for mat in list(bpy.data.materials):
        bpy.data.materials.remove(mat)

    for col_name in ["Level_1", "Level_2", "Level_3"]:
        if col_name in bpy.data.collections:
            bpy.data.collections.remove(bpy.data.collections[col_name])

    # --- Collections ---
    collections = {
        1: get_or_create_collection("Level_1"),
        2: get_or_create_collection("Level_2"),
        3: get_or_create_collection("Level_3"),
    }

    rng = random.Random(seed)

    # --- Level 1 base plate ---
    base = create_panel(
        width=base_width,
        height=base_height,
        thickness=thickness,
        location=(0.0, 0.0, 0.0),
        name="panel_L1_base",
        collection=collections[1],
    )

    add_scoring_lines(
        panel_obj=base,
        seed=seed,
        depth_fraction=score_depth_fraction,
        width_fraction=score_width_fraction,
    )

    # --- Levels 2 and 3 ---
    generate_child_panels(
        parent_obj=base,
        level=2,
        distribution_fn=distribution_fn,
        rng=rng,
        thickness=thickness,
        count_range=count_range,
        child_area_fraction=child_area_fraction,
        max_level=3,
        collections=collections,
        pipe_radius=pipe_radius,
        pipe_probability=pipe_probability,
        rivet_count_range=rivet_count_range,
        rivet_radius_fraction=rivet_radius_fraction,
        **dist_kwargs,
    )

    # --- Materials ---
    mat_l1     = create_material_level1()
    mat_l2     = create_material_level2()
    mat_l3     = create_material_level3()
    mat_pipes  = create_material_pipes()
    mat_rivets = create_material_rivets()

    assign_level_materials(
        collections=collections,
        mat_l1=mat_l1,
        mat_l2=mat_l2,
        mat_l3=mat_l3,
        mat_pipes=mat_pipes,
        mat_rivets=mat_rivets,
    )

    print(
        f"[017_panel_generator] done — "
        f"seed={seed}  base={base_width}x{base_height}x{thickness}  "
        f"dist={distribution_fn.__name__}  kwargs={dist_kwargs}"
    )


# ---------------------------------------------------------------------------
# Main — Demo Parameters
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    # Random seed from OS entropy — note the printed seed to reproduce a result
    seed = random.randint(0, 999999)

    build_scene(
        base_width=4.0,
        base_height=2.0,
        thickness=0.05,
        seed=seed,
        distribution_fn=distribution_weighted_corner,
        count_range=(3, 4),
        child_area_fraction=0.08,
        score_depth_fraction=0.3,
        score_width_fraction=0.01,
        pipe_radius=0.012,
        pipe_probability=0.4,
        rivet_count_range=(2, 5),
        rivet_radius_fraction=(0.04, 0.08),
        # distribution_weighted_corner parameters
        attractor_count=2,
        power=2.0,
    )
