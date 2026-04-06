# Holds our custom hex colors that can be used in flet code
import flet as ft

colors_dict = {
    'light_blue': '#ADD8E6',
    'dark_blue': '#00008B',
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
    colors=[

        ft.Colors.with_opacity(0.6, ft.Colors.OUTLINE_VARIANT),
        ft.Colors.with_opacity(0.3, ft.Colors.OUTLINE_VARIANT),


        #ft.Colors.with_opacity(.8, ft.Colors.OUTLINE_VARIANT), ft.Colors.with_opacity(0.3, ft.Colors.OUTLINE_VARIANT),

        #ft.Colors.CYAN_400, ft.Colors.PURPLE_500   # Highlight colors
    ],
)