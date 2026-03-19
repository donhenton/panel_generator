"""
distribution.py
Panel placement distribution functions and dispatcher.

All distribution functions share the signature:
    fn(bounds, count, **kwargs) -> List[Placement]
making them interchangeable in distribute_panels().
"""

import math
import random
from mathutils import Vector
from typing import Callable, List, Tuple, Optional
import bpy


Bounds    = Tuple[float, float, float, float]   # (min_x, max_x, min_y, max_y)
Placement = Tuple[float, float, float, float]   # (cx, cy, width, height)


# ---------------------------------------------------------------------------
# Distribution Functions
# ---------------------------------------------------------------------------

def distribution_random(
    bounds: Bounds,
    count: int,
    child_area_fraction: float = 0.18,
    aspect_range: Tuple[float, float] = (0.8, 2.2),
    max_attempts: int = 200,
    rng: Optional[random.Random] = None,
    **kwargs,
) -> List[Placement]:
    """
    Uniform-random non-overlapping placement of child panels within bounds.
    """
    if rng is None:
        rng = random.Random()

    min_x, max_x, min_y, max_y = bounds
    parent_w    = max_x - min_x
    parent_h    = max_y - min_y
    parent_area = parent_w * parent_h
    margin      = min(parent_w, parent_h) * 0.05
    gap         = min(parent_w, parent_h) * 0.04

    placements: List[Placement] = []

    for _ in range(count):
        for _attempt in range(max_attempts):
            aspect  = rng.uniform(*aspect_range)
            area    = parent_area * child_area_fraction
            child_w = min(math.sqrt(area * aspect),  parent_w - 2 * margin)
            child_h = min(math.sqrt(area / aspect),  parent_h - 2 * margin)

            cx = rng.uniform(min_x + margin + child_w / 2,
                             max_x - margin - child_w / 2)
            cy = rng.uniform(min_y + margin + child_h / 2,
                             max_y - margin - child_h / 2)

            overlap = any(
                abs(cx - px) < (child_w + pw) / 2 + gap and
                abs(cy - py) < (child_h + ph) / 2 + gap
                for (px, py, pw, ph) in placements
            )

            if not overlap:
                placements.append((cx, cy, child_w, child_h))
                break

    return placements


def distribution_grid_vertices(
    bounds: Bounds,
    count: int,
    child_area_fraction: float = 0.18,
    rng: Optional[random.Random] = None,
    **kwargs,
) -> List[Placement]:
    """
    Snap child panel centres to a random subset of nine candidate points
    derived from the parent face (corners, edge midpoints, centre).
    Includes AABB overlap check.
    """
    if rng is None:
        rng = random.Random()

    min_x, max_x, min_y, max_y = bounds
    parent_w = max_x - min_x
    parent_h = max_y - min_y
    mx, my   = (min_x + max_x) / 2, (min_y + max_y) / 2
    ox = parent_w * 0.3
    oy = parent_h * 0.3

    candidates = [
        (min_x + ox, min_y + oy), (mx, min_y + oy), (max_x - ox, min_y + oy),
        (min_x + ox, my),         (mx, my),          (max_x - ox, my),
        (min_x + ox, max_y - oy), (mx, max_y - oy), (max_x - ox, max_y - oy),
    ]
    rng.shuffle(candidates)

    area    = parent_w * parent_h * child_area_fraction
    child_w = math.sqrt(area * 1.4)
    child_h = math.sqrt(area / 1.4)
    gap     = min(parent_w, parent_h) * 0.04

    placements: List[Placement] = []

    for (cx, cy) in candidates:
        if len(placements) >= count:
            break
        if (cx - child_w / 2 < min_x or cx + child_w / 2 > max_x or
                cy - child_h / 2 < min_y or cy + child_h / 2 > max_y):
            continue
        overlap = any(
            abs(cx - px) < (child_w + pw) / 2 + gap and
            abs(cy - py) < (child_h + ph) / 2 + gap
            for (px, py, pw, ph) in placements
        )
        if not overlap:
            placements.append((cx, cy, child_w, child_h))

    return placements


def distribution_weighted_corner(
    bounds: Bounds,
    count: int,
    child_area_fraction: float = 0.18,
    aspect_range: Tuple[float, float] = (0.8, 2.2),
    attractor_count: int = 2,
    power: float = 2.0,
    max_attempts: int = 400,
    rng: Optional[random.Random] = None,
    **kwargs,
) -> List[Placement]:
    """
    Power-law corner-attractor placement.
    Panels cluster near randomly chosen attractor corners, thinning toward
    the opposite side. Self-similar across recursion levels — reads as fractal.

    Parameters
    ----------
    attractor_count : 1 = single corner bias, 2 = dual corner pull
    power           : falloff exponent — 1.5 loose / 2.0 medium / 3.5+ tight
    """
    if rng is None:
        rng = random.Random()

    min_x, max_x, min_y, max_y = bounds
    parent_w    = max_x - min_x
    parent_h    = max_y - min_y
    parent_area = parent_w * parent_h
    margin      = min(parent_w, parent_h) * 0.05
    gap         = min(parent_w, parent_h) * 0.04

    corners = [
        (min_x, min_y), (max_x, min_y),
        (min_x, max_y), (max_x, max_y),
    ]
    attractor_count = max(1, min(attractor_count, 4))
    attractors = rng.sample(corners, attractor_count)

    def attraction_weight(cx: float, cy: float) -> float:
        total = 0.0
        for (ax, ay) in attractors:
            dist = math.sqrt((cx - ax) ** 2 + (cy - ay) ** 2)
            dist = max(dist, 1e-6)
            total += 1.0 / (dist ** power)
        return total

    def inset_point(ax: float, ay: float) -> Tuple[float, float]:
        ix = ax + margin if ax <= (min_x + max_x) / 2 else ax - margin
        iy = ay + margin if ay <= (min_y + max_y) / 2 else ay - margin
        return ix, iy

    max_weight = max(
        attraction_weight(*inset_point(ax, ay))
        for (ax, ay) in attractors
    )

    placements: List[Placement] = []

    for _ in range(count):
        for _attempt in range(max_attempts):
            aspect  = rng.uniform(*aspect_range)
            area    = parent_area * child_area_fraction
            child_w = min(math.sqrt(area * aspect), parent_w - 2 * margin)
            child_h = min(math.sqrt(area / aspect), parent_h - 2 * margin)

            cx = rng.uniform(min_x + margin + child_w / 2,
                             max_x - margin - child_w / 2)
            cy = rng.uniform(min_y + margin + child_h / 2,
                             max_y - margin - child_h / 2)

            w = attraction_weight(cx, cy)
            if rng.random() > w / max_weight:
                continue

            overlap = any(
                abs(cx - px) < (child_w + pw) / 2 + gap and
                abs(cy - py) < (child_h + ph) / 2 + gap
                for (px, py, pw, ph) in placements
            )

            if not overlap:
                placements.append((cx, cy, child_w, child_h))
                break

    return placements


# ---------------------------------------------------------------------------
# Dispatcher
# ---------------------------------------------------------------------------

def distribute_panels(
    parent_obj: bpy.types.Object,
    count: int,
    distribution_fn: Callable,
    child_area_fraction: float = 0.18,
    rng: Optional[random.Random] = None,
    **dist_kwargs,
) -> List[Placement]:
    """
    Derive parent face bounds from the Blender object and delegate to
    distribution_fn to compute child placements.
    """
    loc  = parent_obj.matrix_world.translation
    dims = parent_obj.dimensions

    bounds: Bounds = (
        loc.x,
        loc.x + dims.x,
        loc.y,
        loc.y + dims.y,
    )

    return distribution_fn(
        bounds,
        count,
        child_area_fraction=child_area_fraction,
        rng=rng,
        **dist_kwargs,
    )
