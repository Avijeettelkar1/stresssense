"""Shared figure style. Owner: C — everyone imports this so all plots in the report match.

    from src.recommender.figures import use_style
    use_style()
"""
from __future__ import annotations


def use_style():
    """Apply the shared matplotlib style. TODO(C): finalise palette/fonts in week 1."""
    import matplotlib.pyplot as plt

    plt.rcParams.update(
        {
            "figure.dpi": 120,
            "savefig.dpi": 200,
            "figure.figsize": (7, 4),
            "axes.grid": True,
            "grid.alpha": 0.3,
            "axes.spines.top": False,
            "axes.spines.right": False,
            "font.size": 11,
        }
    )
