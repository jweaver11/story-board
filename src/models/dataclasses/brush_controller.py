''' Class and data for all our text options for canvases '''

import flet as ft
from dataclasses import dataclass, field


# Source of truth. The data for the textcontroller stored here
@ft.observable
@dataclass
class BrushController:
    size: int = 14
    color: str = "#FFFFFF"
    