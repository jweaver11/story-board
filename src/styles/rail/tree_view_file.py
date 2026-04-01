import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.rail.tree_view_directory import TreeViewDirectory
from models.app import app
from styles.colors import colors
from utils.check_widget_unique import check_widget_unique
import os
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
            on_secondary_tap = lambda e: self.widget.story.open_menu(self.get_menu_options()),
            on_tap = self.widget.show_widget,
            mouse_cursor = ft.MouseCursor.CLICK,
        )


        self.reload()
    
    # Called when this item is right clicked
    def get_menu_options(self) -> list[ft.Control]:
        ''' Pops open a column of the menu options for this tree view item'''

        return [
            MenuOptionStyle(
                on_click=self.rename_clicked,
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
                    self._get_color_options(), 
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

    # Called when rename button is clicked
    def rename_clicked(self, e):

        # Track if our name is unique for checks, and if we're submitting or not
        is_unique = True
        submitting = False

        # Grab our current name for comparison
        current_name = self.widget.title.lower()

        # Called when clicking outside the input field to cancel renaming
        def _cancel_rename(e):
            ''' Puts our name back to static and unalterable '''

            # Grab our submitting state
            nonlocal submitting

            # Since this auto calls on submit, we need to check. If it is cuz of a submit, do nothing
            if submitting:
                submitting = not submitting     # Change submit status to False so we can de-select the textbox
                return
            
            # Otherwise we're not submitting (just clicking off the textbox), so we cancel the rename
            else:

                self.reload()

        # Called everytime a change in textbox occurs
        def _name_check(e):
            ''' Checks if the name is unique within its type of widget '''


            # Nonlocal variables
            nonlocal is_unique
            nonlocal submitting

            # Set submitting to false, and unique to True
            submitting = False
            is_unique = True

            # Grab out title and tag from the textfield, and set our new key to compare
            title = e.control.value
            if title.lower() == current_name:
                return

            # Generate our new key to compare. Requires normalization
            nk = self.widget.directory_path + "\\" + title + "_" + e.control.data
            new_key = os.path.normpath(nk)

            error_text, is_unique = check_widget_unique(self.widget.story, new_key)

            # If we are NOT unique, show our error text
            if not is_unique:
                e.control.error = error_text

            # Otherwise remove our error text
            else:
                e.control.error = None

            e.control.update()
            

        # Called when submitting our textfield.
        def _submit_name(e):
            ''' Checks that we're unique and renames the widget if so. on_blur is auto called after this, so we handle that as well '''

            # Get our name and check if its unique
            name = e.control.value

            # Non local variables
            nonlocal is_unique
            nonlocal text_field
            nonlocal submitting

            # Set submitting to True
            submitting = True

            # If it is, call the rename function. It will do everything else
            if is_unique:
                self.widget.rename(name)
                
            # Otherwise make sure we show our error
            else:
                text_field.error = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                text_field.update()
                
        # Our text field that our functions use for renaming and referencing
        text_field = ft.TextField(
            value=self.widget.title,
            expand=True, dense=True,
            autofocus=True, 
            data=self.widget.data.get('tag', ''),
            text_style=self.text_style,
            on_submit=_submit_name,
            on_change=_name_check,
            on_blur=_cancel_rename,
        )

        # Replaces our name text with a text field for renaming
        self.content.content.title = text_field

        # Clears our popup menu button and applies to the UI
        #self.widget.story.close_menu_instant()
        self.update()

    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        async def _change_icon_color(e):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            color = e.control.data

            # Change the data
            await self.widget.change_data(**{'color': color})
            self.icon_color = color
            
            # Change our icon to match, apply the update
            self.reload()
            self.widget.story.workspace.reload_workspace()

        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.MenuItemButton(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=_change_icon_color, close_on_click=True, data=color,
                    style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10), mouse_cursor="click")
                )
            )

        return color_controls
    
    


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
            on_drag_start=lambda e: self.widget.story.workspace.show_pin_drag_targets(),
            content=ft.ListTile(
                leading=leading_control, 
                title=ft.Text(self.widget.title, style=self.text_style, expand=True, overflow=ft.TextOverflow.ELLIPSIS),
                shape=ft.RoundedRectangleBorder(radius=6),
                bgcolor=ft.Colors.TRANSPARENT, 
                dense=True,
                content_padding=ft.Padding.all(0),
                min_vertical_padding=0,
                mouse_cursor=ft.MouseCursor.CLICK,
                trailing=ft.IconButton(
                    icon=ft.Icons.MORE_VERT_ROUNDED,
                    visible=False,
                    on_click=lambda e: self.widget.story.open_menu(self.get_menu_options()),
                    mouse_cursor=ft.MouseCursor.CLICK,
                ),
            ),
        )

        
        try:
            self.update()
        except Exception as e:
            pass