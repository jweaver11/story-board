# Custom made icons (drawn in a flet canvas), that can be used in replacement of a flet icon

import flet as ft
import flet.canvas as cv


arc_icon = ft.Container(
    cv.Canvas(
        width=24, height=24,
    ),
    #shape=ft.BoxShape.CIRCLE,
)

dungeon_icon = ft.Container()