''' Overlay, generally for storiess'''

import flet as ft
import asyncio
from dataclasses import dataclass, field

@ft.observable
@dataclass
class Overlay:

    # Visibility states
    blocker_visible: bool = False
    menu_visible: bool = False

    # Options for the menu
    menu_position: ft.Offset = field(default_factory=lambda: ft.Offset(0, 0))
    menu_options: list[ft.Control] = None

    
    def hide_menu(self):
        self.menu_visible = False
    async def unblock_page(self):
        self.blocker_visible = False
    async def block_page(self):
        self.blocker_visible = True
        await asyncio.sleep(0.1)  # give the updates scheduler a turn to flush this patch before we continue

   

    def show_menu(self, position: ft.Offset, menu_options: list[ft.Control]):
        self.menu_position = position
        self.menu_options = menu_options
        self.menu_visible = True
    


@ft.component
def Blocker(overlay: Overlay):
    ''' A small spinning ring to block interactions with the page while demanding calculations happen '''
    return ft.Container(
        ft.Row([
            ft.ProgressRing(width=100, height=100)
        ], alignment=ft.MainAxisAlignment.CENTER), 
        expand=True, 
        visible=overlay.blocker_visible, 
        blur=5, left=0, right=0, top=0, bottom=0,
        key="blocker"
    )


''' The control returned when opening a menu. Has a GD sit under it to close the menu so multiple can't be opened at once, and give it nice behavior '''
@ft.component
def Menu(overlay: Overlay):
    return ft.Stack([
        ft.GestureDetector(
            expand=True, 
            visible=overlay.menu_visible,
            on_tap_down=overlay.hide_menu,
            on_secondary_tap_down=overlay.hide_menu,
        ),
        ft.Container(
            left=overlay.menu_position.x, 
            top=overlay.menu_position.y,   # Positions the menu at the mouse location
            visible=overlay.menu_visible,
            border_radius=4, 
            bgcolor=ft.Colors.SURFACE_CONTAINER,
            width=200, #border=ft.Border.all(1, ft.Colors.OUTLINE_VARIANT),
            shadow=ft.BoxShadow(0, 1, offset=ft.Offset(0, 1)),
            content=ft.Column(
                spacing=0,
                controls=overlay.menu_options if overlay.menu_options else [ft.Text("Menu options")]
            ),
            on_click=overlay.hide_menu,
        )

    ], expand=True, key="menu")