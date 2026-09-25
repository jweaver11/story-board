''' Our ft.textstyle to be passed into cv.text shapes on canvases '''

import flet as ft
from dataclasses import dataclass, field, asdict
import os
import json
from contexts.constants import APP_DATA_PATH, TEXT_SETTINGS_FILE_PATH

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

    async def save_file(self):
        ''' Saves our current data to the json file '''

        try:
            os.makedirs(APP_DATA_PATH, exist_ok=True)
            # Save the data to the file (creates file if doesnt exist)
            with open(TEXT_SETTINGS_FILE_PATH, "w", encoding='utf-8') as f:   
                json.dump(asdict(self), f, indent=4)   # asdict() strips observable bookkeeping, unlike self.__dict__
        
        except Exception as e:
            print(f"Error saving settings to {TEXT_SETTINGS_FILE_PATH}: {e}")