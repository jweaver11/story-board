''' Tree View Control for folders that appears as an expansion tile in the UI '''

import flet as ft
from models.views.story import Story
import os
import json
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.snack_bar import SnackBar
from utils.new_canvas import new_canvas_dlg
from models.isolated_controls.expansion_tile import IsolatedExpansionTile
import asyncio


# Called when we need to reload this directory tile
@ft.component
def RailFolderView(folder_data: dict, story: Story) -> ft.GestureDetector:

    # Switch between expanded and not in data
    def toggle_expand(e=None):
        folder_data['is_expanded'] = not folder_data.get('is_expanded', False)
    

    in_base_dir, _ = ft.use_state(folder_data.get('full_path', "") != story.content_directory_path)

    leading_control = ft.Container(
        ft.Icon(ft.Icons.FOLDER_OUTLINED, color=folder_data.get('color')),
        border=ft.Border.only(left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)) if not in_base_dir else None,   # Give left border if in sub folder
        padding=ft.Padding.only(left=6)
    )

    expansion_tile = ft.ExpansionTile(
        title=ft.Row([
            leading_control, 
            ft.Text(value=f"{folder_data.get('name')}", weight=ft.FontWeight.BOLD, text_align="left", expand=True, overflow=ft.TextOverflow.ELLIPSIS)], 
            expand=True, spacing=6
        ),
        dense=True,
        collapsed_shape=ft.RoundedRectangleBorder(radius=4),
        visual_density=ft.VisualDensity.COMPACT,
        expanded=folder_data.get('is_expanded'),
        tile_padding=ft.Padding(0, 0, 6, 0),
        icon_color=folder_data.get('color'),
        controls_padding=ft.Padding(10, 0, 0, 0),       # Keeps all sub children indented
        expanded_cross_axis_alignment=ft.CrossAxisAlignment.START,
        adaptive=True, bgcolor=ft.Colors.TRANSPARENT,
        shape=ft.RoundedRectangleBorder(radius=4),
        on_change=toggle_expand,
    )

    # Wrap in all in a drag target so we can drag to move widgets into different folders
    drag_target = ft.DragTarget(
        group="widgets",
        #on_accept=rail_folder.on_drag_accept,
        content=expansion_tile,
    )
    
    # Set the content
    return ft.GestureDetector(
        content=drag_target,
        mouse_cursor=ft.MouseCursor.CLICK,
        #on_secondary_tap=lambda _: rail_folder.story.open_menu(rail_folder.get_menu_options()),
        expand=True,
    )
