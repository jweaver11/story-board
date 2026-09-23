''' Our ft.textstyle to be passed into cv.text shapes on canvases '''

import flet as ft
from dataclasses import dataclass, field

@ft.observable
@dataclass
class TextSettings:
    size: int = 14
    weight: str = "normal"  # Options: None, w100, w200, w300, w400, w500, w600, w700, w800, w900, bold
    italic: bool = False
    decoration: str = None  # Options: none, underline, overline, line_through
    decoration_color: str = None
    decoration_thickness: int = 1
    decoration_style: str = "solid"    # options: solid, wavy, double, dotted, dashed
    font_family: str = None
    color: str = "#FFFFFF"  # Hex color folowed by opacity
    bgcolor: str = "#00000000"  # Background color for text shapes
    #shadow: dict = field(default_factory=lambda: {
        #'blur_radius': 0,
        #'blur_style': 'normal', # Options: normal, solid, outer, inner
        #'color': "#00000000",
        #'offset': (0, 0),
        #'spread_radius': 0,
    #})   # Boxshad values
    foreground: any = None # [list of gradients/color values] (ft.PaintLinearGradient, ft.PaintRadialGradient, ft.PaintGradient ft.PaintSweepGradient)
    letter_spacing: int = 0
    word_spacing: int = 0
    baseline: str = "alphabetic"  # How text is rendered - Options: alphabetic or ideographic