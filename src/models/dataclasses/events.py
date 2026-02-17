# Simple class for organizing our events on our plotlines (plot point, arcs, markers)
from dataclasses import dataclass

@dataclass
class Event:
    tag: str  # 'plot_point', 'arc_start', 'arc_end', 'marker'
    left: int
    title: str
    color: str = "secondary"
