import flet as ft


text_style = ft.TextStyle(
    size=14,
    color=ft.Colors.ON_SURFACE,
    weight=ft.FontWeight.BOLD,
)

# Returns easy shadow for our text, with a given color, offset, and blur radius
class TextShadow(list):
    def __init__(self, color: ft.Colors = ft.Colors.BLACK, thickness: int=1, blur_radius: int=0):
        super().__init__([
            ft.BoxShadow(color=color, offset=ft.Offset(thickness, 0), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(-thickness, 0), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(0, thickness), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(0, -thickness), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(thickness, thickness), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(-thickness, thickness), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(thickness, -thickness), blur_radius=blur_radius),
            ft.BoxShadow(color=color, offset=ft.Offset(-thickness, -thickness), blur_radius=blur_radius),       
        ])