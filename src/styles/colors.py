# Holds our custom hex colors that can be used in flet code
import flet as ft

colors_dict = {
    'light_blue': '#ADD8E6',
    'dark_blue': '#00008B',
}

theme_colors = {
    "default": "#A0CAFD",
    "red": "red",
    "orange": "orange",
    "yellow": "yellow",
    "green": "green",
    "cyan": "cyan",
    "blue": "blue",
    "purple": "purple",
    "pink": "pink",
    "brown": "brown",
}

colors = [
    "primary",
    "red",
    "orange",
    "yellow",
    "green",
    "cyan",
    "blue",
    "purple",
    "pink",
    "brown",
    "white",
    "grey",
    "black",
]

dark_gradient = ft.LinearGradient(
    begin=ft.Alignment.TOP_CENTER,
    end=ft.Alignment.BOTTOM_CENTER,
    tile_mode=ft.GradientTileMode.REPEATED,
    stops=[0.8, 1.0],
    colors=[
        #ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
        #ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
        ft.Colors.with_opacity(0.5, ft.Colors.OUTLINE_VARIANT),
        ft.Colors.with_opacity(0.2, ft.Colors.OUTLINE_VARIANT),
    ],
)