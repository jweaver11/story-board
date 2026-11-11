import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.rail_folder import RailFolder
from models.app import app
from styles.colors import colors
from styles.text_fields import TextField
import os
import asyncio
import math
from styles.snack_bar import SnackBar
import flet_shadcn_ui as shad

# Class for items within a tree view on the rail
class RailFile(ft.GestureDetector):

    def __init__(
        self, 
        widget: Widget, 
        in_base_directory: bool = False,
    ):
        
        
        # Set our widget reference and tag
        self.widget = widget
        self.in_base_directory = in_base_directory
        tag = widget.data.get('tag', None)

        match tag:
            case "manuscript": self.icon = ft.Icons.DESCRIPTION_OUTLINED
            case "canvas": self.icon = ft.Icons.BRUSH_OUTLINED
            case "canvas_board": self.icon = ft.Icons.SPACE_DASHBOARD_OUTLINED
            case "note": self.icon = ft.Icons.LIBRARY_BOOKS_OUTLINED
            case "character": self.icon = ft.Icons.PERSON_OUTLINED
            case "plotline": self.icon = ft.Icons.TIMELINE_OUTLINED
            case "map": self.icon = ft.Icons.MAP_OUTLINED
            case "world": self.icon = ft.Icons.PUBLIC_OUTLINED
            case "character_relationship_map": self.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case "item": self.icon = ft.Icons.STAR_OUTLINE_ROUNDED 
            case "comic_preview": self.icon = ft.Icons.SLIDESHOW_OUTLINED
            case "chart": 
                if widget.data.get('chart_type', None) == "bar":
                    self.icon = ft.Icons.INSERT_CHART_OUTLINED
                else:
                    self.icon = ft.CupertinoIcons.COMPASS
            case "plot_chart": self.icon = ft.Icons.ACCOUNT_TREE_OUTLINED
            case _: self.icon = ft.Icons.ERROR_OUTLINE

        # Set our text style
        self.text_style = ft.TextStyle(
            size=14,
            color=ft.Colors.ON_SURFACE,
            weight=ft.FontWeight.W_500,
            overflow=ft.TextOverflow.ELLIPSIS,
        )

        # Get icon color from widget data if it exists
        self.icon_color = widget.data.get('color', 'primary')

        # Parent constructor
        super().__init__(
            on_enter = self._highlight,
            on_exit = self._stop_highlight,
            #on_secondary_tap = lambda _: self.widget.story.open_menu(self.get_menu_options()),
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

        def toggle_color_popover(e=None):
            color_popover.open = not color_popover.open
            color_popover.update()

        return [
            color_popover := shad.Popover(
                shad.MenuItem(
                    leading=ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, self.widget.data.get('color', 'primary'), size=20),
                    content=ft.Row([ft.Text("Color"), ft.Icon(ft.Icons.ARROW_RIGHT, ft.Colors.OUTLINE, size=16)], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                    trailing=ft.Icons.ARROW_RIGHT,
                    on_click=toggle_color_popover,
                    close_on_click=False,
                ),
                ft.Column(self.widget.get_color_options(), tight=True, spacing=0, width=100)
            ), 
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED, self.widget.data.get('color', 'primary'), size=20), 
                content=f"Rename {self.widget.data.get('title')}", 
                on_click=handle_rename, 
            ),   
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.FILE_DOWNLOAD_OUTLINED, self.widget.data.get('color', 'primary'), size=20), 
                content=f"Export {self.widget.data.get('title')}", data=file_path,
                on_click=self.widget.story.handle_export,
            ),   
            shad.Separator(margin=ft.Margin.symmetric(vertical=4)),
            shad.MenuItem(
                leading=ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR, size=20), content=f"Delete {self.widget.data.get('title')}", 
                on_click=self.widget.delete_clicked, close_on_click=True, 
            ),   
        ]

    # Called when hovering mouse over a tree view item
    async def _highlight(self, e=None):
        self.content.content.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.ON_SURFACE)
        #self.options_button.opacity = 1
        self.update()

    # Called when stopping hover over a tree view item
    async def _stop_highlight(self, e=None):
        self.content.content.content.bgcolor = ft.Colors.TRANSPARENT
        #self.options_button.opacity = 0
        self.update()


    # Called to reload our tree view file display
    def build(self):

        
        leading_control = ft.Container(
            ft.Icon(self.icon, color=self.icon_color),
            border=ft.Border.only(left=ft.BorderSide(2, ft.Colors.OUTLINE_VARIANT)) if self.in_base_directory == False else None,
            padding=ft.Padding.only(left=6)
        )


        #self.options_button = ft.IconButton(
            #icon=ft.Icons.MORE_HORIZ_ROUNDED,
            #opacity=0,
            #on_click=lambda _: self.widget.story.open_menu(self.get_menu_options()),
            #mouse_cursor=ft.MouseCursor.CLICK,
            #visual_density=ft.VisualDensity.COMPACT
        #)
        def hide_edit_title_tf(e=None):
            self.edit_title_tf.visible = False
            self.title_text.visible = True
            self.update()

        self.edit_title_tf = ft.TextField(
            value=self.widget.data.get('title', 'untitled'),
            visible=False, expand=True,
            on_blur=hide_edit_title_tf,
            on_submit=self.widget.submit_rename,
            bgcolor=ft.Colors.SURFACE_CONTAINER_HIGH,
            border=ft.OutlineInputBorder(side=ft.BorderSide(color=ft.Colors.TRANSPARENT), border_radius=4),
            dense=True, capitalization=ft.TextCapitalization.SENTENCES,
        )

        self.title_text = ft.Text(self.widget.data.get('title', 'untitled'), style=self.text_style, expand=True, overflow=ft.TextOverflow.ELLIPSIS)

        self.content = ft.Draggable( 
            group="widgets",
            data=self.widget.data.get('id', ""),
            content_feedback=ft.TextButton(ft.Row([ft.Icon(self.icon, self.icon_color, expand=True), ft.Text(self.widget.data.get('title', 'untitled'), style=self.text_style, expand=True)], expand=True)),
            content=shad.ContextMenu(
                ft.Container(
                    ft.Row([
                        leading_control, 
                        self.title_text,
                        self.edit_title_tf,
                        #self.options_button
                    ], spacing=6),
                    border_radius=4,
                    on_click=self.widget.show_widget,
                    padding=ft.Padding.only(top=2, bottom=2),
                ),
                items=self.get_menu_options(),
                open_on_long_press=True if ft.context.page.platform.is_mobile() else False, 
            ),
            
    )