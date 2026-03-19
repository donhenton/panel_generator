"""
recursive.py
Recursive panel placement — generates Level 2 and Level 3 panels,
pipes, and rivets.
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
from typing import Callable, List, Tuple, Optional

from pg_primitives import create_panel, link_to_collection
from pg_distribution import distribute_panels
from pg_pipes import add_pipes
from pg_rivets import add_rivets

def generate_child_panels(
    parent_obj: bpy.types.Object,
    level: int,
    distribution_fn: Callable,
    rng: Optional[random.Random] = None,
    thickness: float = 0.05,
    count_range: Tuple[int, int] = (3, 4),
    child_area_fraction: float = 0.18,
    max_level: int = 3,
    z_bias_factor: float = 0.1,
    collections: Optional[dict] = None,
    pipe_radius: float = 0.012,
    pipe_probability: float = 0.4,
    rivet_count_range: Tuple[int, int] = (2, 5),
    rivet_radius_fraction: Tuple[float, float] = (0.04, 0.08),
    **dist_kwargs,
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

    Recursively place child panels on the face of parent_obj.
    At Level 3, rivets are added to every panel.
    After each level's panels are placed, pipes connect siblings.

    Parameters
    ----------
    parent_obj            : parent Blender panel object
    level                 : current level (call with 2 to start)
    distribution_fn       : placement distribution callable
    rng                   : seeded random.Random instance
    thickness             : Z thickness applied to all panels at all levels
    count_range           : (min, max) children to place per parent
    child_area_fraction   : fraction of parent face area per child
    max_level             : recursion stops when level exceeds this
    z_bias_factor         : child bottom face lifted by thickness * z_bias_factor
    collections           : dict mapping level int to bpy.types.Collection
    pipe_radius           : cylinder radius for pipes
    pipe_probability      : probability any panel pair gets a pipe connection
    rivet_count_range     : (min, max) rivets per Level 3 panel
    rivet_radius_fraction : (min, max) rivet radius as fraction of shorter dim
    **dist_kwargs         : forwarded to distribution_fn

    Recursion
    ---------
    level > max_level  ->  base case, return []
    level == 2         ->  children placed on the Level 1 base plate
    level == 3         ->  children placed on each Level 2 panel
    """
    if level > max_level:
        return []

    if rng is None:
        rng = random.Random()

    col = collections.get(level) if collections else None

    placements = distribute_panels(
        parent_obj=parent_obj,
        count=rng.randint(*count_range),
        distribution_fn=distribution_fn,
        child_area_fraction=child_area_fraction,
        rng=rng,
        **dist_kwargs,
    )

    z_bias       = thickness * z_bias_factor
    parent_top_z = parent_obj.matrix_world.translation.z + thickness + z_bias

    created: List[bpy.types.Object] = []
    this_level_panels: List[bpy.types.Object] = []

    for i, (cx, cy, cw, ch) in enumerate(placements):
        name  = f"panel_L{level}_{parent_obj.name}_c{i}"
        child = create_panel(
            width=cw,
            height=ch,
            thickness=thickness,
            location=(cx, cy, parent_top_z),
            name=name,
            parent_obj=parent_obj,
            collection=col,
        )
        created.append(child)
        this_level_panels.append(child)

        if level == 3:
            rivets = add_rivets(
                panel_obj=child,
                seed=rng.randint(0, 999999),
                count_range=rivet_count_range,
                radius_fraction=rivet_radius_fraction,
                collection=col,
            )
            created.extend(rivets)

        created.extend(
            generate_child_panels(
                parent_obj=child,
                level=level + 1,
                distribution_fn=distribution_fn,
                rng=rng,
                thickness=thickness,
                count_range=count_range,
                child_area_fraction=child_area_fraction,
                max_level=max_level,
                z_bias_factor=z_bias_factor,
                collections=collections,
                pipe_radius=pipe_radius,
                pipe_probability=pipe_probability,
                rivet_count_range=rivet_count_range,
                rivet_radius_fraction=rivet_radius_fraction,
                **dist_kwargs,
            )
        )

    if len(this_level_panels) >= 2:
        pipes = add_pipes(
            parent_obj=parent_obj,
            child_panels=this_level_panels,
            seed=rng.randint(0, 999999),
            radius=pipe_radius,
            pipe_probability=pipe_probability,
            collection=col,
        )
        created.extend(pipes)

    return created
