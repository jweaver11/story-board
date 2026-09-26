''' Tree View Control for files that appears as an item in the rail '''

import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.colors import colors
from styles.text_fields import TextField
import os
import asyncio
import math
from styles.snack_bar import SnackBar
from dataclasses import dataclass

    
# Called when this item is right clicked
def get_menu_options(self) -> list[ft.Control]:
    ''' Pops open a column of the menu options for this tree view item'''
    return

    async def handle_rename(e=None):
        await self.widget.story.close_menu()
        self.edit_title_tf.visible = True
        self.title_text.visible = False
        self.update()
        await self.edit_title_tf.focus()

    async def handle_delete(e=None):
        
        async def _delete_confirmed(_=ft.Event):
            ''' Deletes the widget after confirmation '''

            # Delete file, remove from dict
            if await self.widget.delete_file():
                self.widget.story.widgets.pop(self.widget.data.get('id', ''), None)   # Remove ourselves from the story's widgets
            else:
                self.page.pop_dialog()
                self.page.show_dialog(SnackBar("Error deleting file. Please try again."))
                return

            if self.widget.data.get('visible', False) == True:
                await self.widget.story.workspace.remove_widget_from_workspace(self.widget)  # Remove ourselves from the workspace if we were visible

            self.parent.controls.remove(self)  # Remove ourselves from the rail
            self.parent.update()

            self.page.pop_dialog()

        

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.widget.data.get('title', '')} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda: self.page.pop_dialog(), style=ft.ButtonStyle(mouse_cursor="click")),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR, mouse_cursor="click")),
            ]
        )

        await self.widget.story.close_menu()
        self.page.show_dialog(dlg)
        await self.widget.story.close_menu()

    file_path = os.path.join(
        self.widget.data.get('directory_path', ''),
        f"{self.widget.data.get('id', '')}.json",
    )

    return [
        MenuOptionStyle(
            on_click=handle_rename,
            content=ft.Row([
                ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.widget.data.get('color', 'primary'),),
                ft.Text(
                    f"Rename {self.widget.data.get('title')}",
                    weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS, expand=True
                ), 
            ]),
        ),
        ft.MenuItemButton(
            leading=ft.Icon(ft.Icons.DOWNLOAD_OUTLINED, ft.Colors.PRIMARY), content="Export Widget",
            on_click=self.widget.story.handle_export, close_on_click=True,
            style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
            tooltip="Export this part of your story.", data=file_path
        ),
        MenuOptionStyle(
            ft.SubmenuButton(
                ft.Row([
                    ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.widget.data.get('color', "primary")), 
                    ft.Text("Color", weight=ft.FontWeight.BOLD, expand=True),
                    ft.Icon(ft.Icons.ARROW_RIGHT),
                ], expand=True),
                self.widget.get_color_options(), 
                menu_style=ft.MenuStyle(alignment=ft.Alignment.TOP_RIGHT, padding=ft.Padding.all(0)),
                style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=4), mouse_cursor="click"),
                tooltip="Change this widget's color"
            ),
            no_padding=True, no_effects=True
        ),
        MenuOptionStyle(
            on_click=self.widget.delete_clicked,
            content=ft.Row([
                ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                ft.Text(f"Delete {self.widget.data.get('title')}", weight=ft.FontWeight.BOLD, overflow=ft.TextOverflow.ELLIPSIS, expand=True),
            ]),
        )
    ]

    


# Called to reload our tree view file display
@ft.component
def RailFile(widget: dataclass, story):
    
    match widget.tag:
        case "manuscript": icon = ft.Icons.DESCRIPTION_OUTLINED
        case "canvas": icon = ft.Icons.BRUSH_OUTLINED
        case "canvas_board": icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
        case "note": icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
        case "character": icon = ft.Icons.PERSON_OUTLINED
        case "plotline": icon = ft.Icons.TIMELINE_OUTLINED
        case "map": icon = ft.Icons.MAP_OUTLINED
        case "world": icon = ft.Icons.PUBLIC_OUTLINED
        case "character_relationship_map": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
        case "item": icon = ft.Icons.STAR_OUTLINE_ROUNDED 
        case "comic_preview": icon = ft.Icons.SLIDESHOW_OUTLINED
        case "chart": 
            if widget.chart_type == "bar":
                icon = ft.Icons.INSERT_CHART_OUTLINED
            else:
                icon = ft.CupertinoIcons.COMPASS
        case "plot_chart": icon = ft.Icons.ACCOUNT_TREE_OUTLINED
        case _: icon = ft.Icons.ERROR_OUTLINE

    
    leading_control = ft.Container(
        ft.Icon(icon, color=widget.color),
        #border=ft.Border.only(left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)) if self.father is not None else None,
        padding=ft.Padding.only(left=6)
    )

    options_button = ft.IconButton(
        icon=ft.Icons.MORE_HORIZ_ROUNDED,
        opacity=0,
        #on_click=lambda _: self.widget.story.open_menu(self.get_menu_options()),
        mouse_cursor=ft.MouseCursor.CLICK,
        visual_density=ft.VisualDensity.COMPACT,
        #visible=ft.context.page.is_mobile()
    )

    is_editing_title, set_is_editing_title = ft.use_state(False)
    highlighting, set_highlighting = ft.use_state(False)

    
    edit_title_tf = ft.TextField(
        value=widget.title,
        visible=is_editing_title, 
        expand=True,
        on_blur=lambda: set_is_editing_title(False),
        #on_submit=self.widget.submit_rename,
        bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
        #border_radius=4, 
        dense=True, capitalization=ft.TextCapitalization.SENTENCES,
        #border_color=ft.Colors.TRANSPARENT,
        #focused_border_color=ft.Colors.PRIMARY,
    )

    return ft.GestureDetector(
        ft.Draggable( 
            group="widgets",
            data=widget.id,
            content_feedback=ft.TextButton(ft.Row([ft.Icon(icon, widget.color, expand=True), ft.Text(widget.title, weight=ft.FontWeight.W_500, expand=True, overflow=ft.TextOverflow.ELLIPSIS)], expand=True)),
            #on_drag_start=lambda _: self.widget.story.workspace.show_pin_drag_targets(),
            content=ft.Container(
                ft.Row([
                    leading_control, 
                    ft.Text(widget.title, weight=ft.FontWeight.W_500, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                    edit_title_tf,
                    #self.options_button
                ], spacing=6),
                bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE) if highlighting else None,
                border_radius=4,
                on_click=widget.show_widget,
                padding=ft.Padding.only(top=2, bottom=2),
                
            ),
        ),
        on_enter=lambda: set_highlighting(True),
        on_exit=lambda: set_highlighting(False),
        #on_secondary_tap = lambda _: self.widget.story.open_menu(self.get_menu_options()),
        #on_tap = self.widget.show_widget,
        mouse_cursor = ft.MouseCursor.CLICK,
    )