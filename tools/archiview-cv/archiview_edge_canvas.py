#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Edge-stretch canvas fill for Archiview time-layer exports (4200×2452)."""

from archiview_cv import (
    TIME_LAYER_HEIGHT,
    TIME_LAYER_WIDTH,
    AlignMode,
    contain_fit_size,
    edge_stretch_summary,
    edge_stretch_to_canvas,
    placement_offset,
)

__all__ = [
    "TIME_LAYER_WIDTH",
    "TIME_LAYER_HEIGHT",
    "AlignMode",
    "contain_fit_size",
    "placement_offset",
    "edge_stretch_to_canvas",
    "edge_stretch_summary",
]

if __name__ == "__main__":
    import numpy as np

    sample = np.zeros((800, 1200, 3), dtype=np.uint8)
    sample[:, :400] = (40, 40, 40)
    sample[:, 400:800] = (180, 170, 160)
    sample[:, 800:] = (90, 90, 90)
    out = edge_stretch_to_canvas(sample)
    assert out.shape == (TIME_LAYER_HEIGHT, TIME_LAYER_WIDTH, 3)
    print(edge_stretch_summary(1200, 800))
    print("edge_stretch_to_canvas OK", out.shape)
