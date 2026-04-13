import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.rail.tree_view_directory import TreeViewDirectory
from models.app import app
from styles.colors import colors
from utils.check_widget_unique import check_widget_unique
import os
import asyncio
import math

# Class for items within a tree view on the rail
class TreeViewFile(ft.GestureDetector):

    def __init__(
        self, 
        widget: Widget, 
        father: TreeViewDirectory = None,
    ):
        
        
        # Set our widget reference and tag
        self.widget = widget
        self.father = father
        tag = widget.data.get('tag', None)

        match tag:
            case "document": self.icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": self.icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": self.icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            #case "note": self.icon = ft.Icons.STICKY_NOTE_2_OUTLINED
            case "note": self.icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": self.icon = ft.Icons.PERSON_OUTLINED
            case "plotline": self.icon = ft.Icons.TIMELINE_OUTLINED
            case "map": self.icon = ft.Icons.MAP_OUTLINED
            case "world": self.icon = ft.Icons.PUBLIC_OUTLINED
            case "character_connection_map": self.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "item": self.icon = ft.Icons.STAR_OUTLINE_ROUNDED 
            case "chart": 
                if widget.data.get('type', None) == "bar":
                    self.icon = ft.Icons.INSERT_CHART_OUTLINED
                else:
                    self.icon = ft.CupertinoIcons.COMPASS
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


        self.reload()
    
    # Called when this item is right clicked
    def get_menu_options(self) -> list[ft.Control]:
        ''' Pops open a column of the menu options for this tree view item'''

        return [
            MenuOptionStyle(
                on_click=self.widget.rename_clicked,
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
    async def _highlight(self, e):
        self.content.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        self.content.content.trailing.visible = True    
        self.update()

    # Called when stopping hover over a tree view item
    async def _stop_highlight(self, e):
        self.content.content.bgcolor = ft.Colors.TRANSPARENT
        self.content.content.trailing.visible = False
        self.update()


    # Called to reload our tree view file display
    def reload(self):

        # If we're in a sub folder in the directory, make leading contorl also have a line
        if self.father is not None:
            leading_control = ft.Row([ft.VerticalDivider(2, 2), ft.Icon(self.icon, color=self.icon_color)], tight=True)
        else:
            leading_control = ft.Icon(self.icon, color=self.icon_color)

        self.content = ft.Draggable(
            group="widgets",
            data=self.widget.data['key'],
            content_feedback=ft.TextButton(ft.Row([ft.Icon(self.icon, expand=True), ft.Text(self.widget.title, style=self.text_style, expand=True)], expand=True)),
            on_drag_start=lambda _: self.widget.story.workspace.show_pin_drag_targets(),
            
            content=ft.ListTile(
                leading=leading_control, 
                title=ft.Text(self.widget.title, style=self.text_style, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                shape=ft.RoundedRectangleBorder(radius=6),
                bgcolor=ft.Colors.TRANSPARENT, 
                dense=True,
                content_padding=ft.Padding.only(right=10) if self.father is not None else ft.Padding.only(right=10, left=10),
                min_vertical_padding=0,
                mouse_cursor=ft.MouseCursor.CLICK,
                trailing=ft.IconButton(
                    icon=ft.Icons.MORE_VERT_ROUNDED,
                    visible=False,
                    on_click=lambda _: self.widget.story.open_menu(self.get_menu_options()),
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ),
        )

        
        try:
            self.update()
        except Exception as _:
            pass