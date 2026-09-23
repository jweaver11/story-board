import flet as ft
import json
from dataclasses import dataclass, field

@ft.observable
@dataclass
class PaintSettings:
    color: str = "#FFFFFFFF"     # Hex color folowed by opacity
    stroke_width: int = 3          # Size of the strokees
    style: str = "stroke"          # style of the strokes. Either stroke or fill
    stroke_cap: str = "round"      # Each end of the strokes shape
    stroke_join: str = "round"     # How corners between strokes are drawn
    stroke_miter_limit: int = 10
    stroke_dash_pattern: list = None         # If we should use dashed lines, and the pattern for them
    anti_alias: bool = True     # Use anti aliasing for smoother strokes or not
    blur_image: int = 0        # How much blur to apply to the stroke
    blend_mode: str = None     # Any blend mode to apply to the stroke, or None for normal
