''' Widget rail items that don't need to be dragged and dropped but still need all other functionality '''

import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.rail.rail_folder import RailFolder
from models.app import app
from styles.colors import colors
import os
import math

# Class for items within a tree view on the rail
class WidgetRailItem(ft.GestureDetector):

    def __init__(
        self, 
        widget: Widget, 
        father: RailFolder = None,
    ):
        
        
        # Set our widget reference and tag
        self.widget = widget
        self.father = father
        tag = widget.data.get('tag', None)

        match tag:
            case "document": self.icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": self.icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": self.icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            case "note": self.icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": self.icon = ft.Icons.PERSON_OUTLINED
            case "plotline": self.icon = ft.Icons.TIMELINE_OUTLINED
            case "map": self.icon = ft.Icons.MAP_OUTLINED
            case "world": self.icon = ft.Icons.PUBLIC_OUTLINED
            case "character_connection_map": self.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "item": self.icon = ft.Icons.STAR_OUTLINE_ROUNDED 
            case "comic_preview": self.icon = ft.Icons.SLIDESHOW_OUTLINED
            case "chart": 
                if widget.data.get('type', None) == "bar":
                    self.icon = ft.Icons.INSERT_CHART_OUTLINED
                else:
                    self.icon = ft.CupertinoIcons.COMPASS
            case "plot_chart": self.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case _: self.icon = ft.Icons.ERROR_OUTLINE

        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.BOLD,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # Get icon color from widget data if it exists
        self.icon_color = widget.data.get('color', 'primary')

        # Parent constructor
        super().__init__(
            on_enter = self._highlight,
            on_exit = self._stop_highlight,
            on_secondary_tap = lambda _: self.widget.story.open_menu(self.get_menu_options()),
            on_tap = self.widget.show_widget,
            mouse_cursor = ft.MouseCursor.CLICK,
        )
    
    # Called when this item is right clicked
    def get_menu_options(self) -> list[ft.Control]:
        ''' Pops open a column of the menu options for this tree view item'''

        async def handle_rename(e=None):
            await self.widget.story.close_menu()
            self.edit_title_tf.visible = True
            self.title_text.visible = False
            self.update()
            await self.edit_title_tf.focus()

        return [
            MenuOptionStyle(
                on_click=handle_rename,
                content=ft.Row([
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.widget.data.get('color', 'primary'),),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        
                    ), 
                ]),
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
                    style=ft.ButtonStyle(padding=ft.Padding.only(left=8), shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click"),
                    tooltip="Change this widget's color"
                ),
                no_padding=True, no_effects=True
            ),
            MenuOptionStyle(
                on_click=self.widget.delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

    # Called when hovering mouse over a tree view item
    async def _highlight(self, e=None):
        self.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        #self.content.trailing.visible = True    
        self.update()

    # Called when stopping hover over a tree view item
    async def _stop_highlight(self, e=None):
        self.content.bgcolor = ft.Colors.TRANSPARENT
        #self.content.trailing.visible = False
        self.update()

    
    


    # Called to reload our tree view file display
    def build(self):

        leading_control = ft.Container(
            ft.Icon(self.icon, color=self.icon_color),
            border=ft.Border.only(left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)) if self.father is not None else None,
            padding=ft.Padding.only(left=6)
        )

        def hide_edit_title_tf(e=None):
            self.edit_title_tf.visible = False
            self.title_text.visible = True
            self.update()

        self.title_text = ft.Text(self.widget.data.get('title', 'untitled'), style=self.text_style, expand=True, overflow=ft.TextOverflow.ELLIPSIS)

        self.edit_title_tf = ft.TextField(
            value=self.widget.data.get('title', 'untitled'),
            visible=False, expand=True,
            on_blur=hide_edit_title_tf,
            on_submit=self.widget.submit_rename,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border_radius=4, dense=True, capitalization=ft.TextCapitalization.SENTENCES,
            border_color=ft.Colors.TRANSPARENT,
            focused_border_color=ft.Colors.PRIMARY,
        )

        self.content = ft.Container(
            ft.Row([
                leading_control, 
                self.title_text,
                self.edit_title_tf
                #self.options_button
            ], spacing=6),
            border_radius=4,
            padding=ft.Padding.only(top=2, bottom=2),
        )
        