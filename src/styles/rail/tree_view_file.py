import flet as ft
from models.widget import Widget
from styles.menu_option_style import MenuOptionStyle
from styles.rail.tree_view_directory import TreeViewDirectory
from models.app import app
from styles.colors import colors
from utils.check_widget_unique import check_widget_unique
import os

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
            case "note": self.icon = ft.Icons.NOTE_ALT_OUTLINED
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
            on_enter = self.on_hover,
            on_exit = self.on_stop_hover,
            on_secondary_tap = lambda e: self.widget.story.open_menu(self.get_menu_options()),
            on_tap = lambda e: self.widget.toggle_visibility(value=True),
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
                    ft.Icon(ft.Icons.DRIVE_FILE_RENAME_OUTLINE_OUTLINED),
                    ft.Text(
                        "Rename", 
                        weight=ft.FontWeight.BOLD, 
                        color=ft.Colors.ON_SURFACE
                    ), 
                ]),
            ),
            MenuOptionStyle(
                content=ft.PopupMenuButton(
                    content=ft.Container(
                        ft.Row([ft.Icon(ft.Icons.COLOR_LENS_OUTLINED, color=self.widget.data.get('color', 'primary'),), ft.Text("Color",  weight=ft.FontWeight.BOLD),]),
                        padding=ft.padding.all(8), border_radius=ft.border_radius.all(6),
                    ),
                    tooltip=f"Change {self.widget.title} Color", menu_padding=0,
                    items=self._get_color_options()
                ),
                no_padding=True
            ),
            MenuOptionStyle(
                on_click=self.delete_clicked,
                content=ft.Row([
                    ft.Icon(ft.Icons.DELETE_OUTLINE_ROUNDED, ft.Colors.ERROR),
                    ft.Text("Delete", weight=ft.FontWeight.BOLD, color=ft.Colors.ON_SURFACE, expand=True),
                ]),
            )
        ]

    # Called when hovering mouse over a tree view item
    async def on_hover(self, e):
        self.content.bgcolor = ft.Colors.with_opacity(0.1, ft.Colors.WHITE)
        self.update()

    # Called when stopping hover over a tree view item
    async def on_stop_hover(self, e):
        self.content.bgcolor = ft.Colors.TRANSPARENT
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
                self.widget.p.update()

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
                e.control.error_text = error_text

            # Otherwise remove our error text
            else:
                e.control.error_text = None
                
            self.widget.p.update()

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
                text_field.error_text = "Name already exists"
                text_field.focus()                                  # Auto focus the textfield
                self.widget.p.update()
                
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
        self.content.content.content.content.controls[1] = text_field

        # Clears our popup menu button and applies to the UI
        self.widget.p.overlay.clear()
        self.widget.p.update()

    def _get_color_options(self) -> list[ft.Control]:
        ''' Returns a list of all available colors for icon changing '''

        # Called when a color option is clicked on popup menu to change icon color
        def _change_icon_color(color: str):
            ''' Passes in our kwargs to the widget, and applies the updates '''

            # Change the data
            self.widget.change_data(**{'color': color})
            self.icon_color = color
            
            # Change our icon to match, apply the update
            self.reload()
            self.widget.reload_widget()
            self.widget.story.workspace.reload_workspace()


        # List for our colors when formatted
        color_controls = [] 

        # Create our controls for our color options
        for color in colors:
            color_controls.append(
                ft.PopupMenuItem(
                    content=ft.Text(color.capitalize(), weight=ft.FontWeight.BOLD, color=color),
                    on_click=lambda e, col=color: _change_icon_color(col)
                )
            )

        return color_controls
    
    # Called when the delete button is clicked in the menu options
    def delete_clicked(self, e):
        ''' Deletes this file from the story '''

        def _delete_confirmed(e=None):
            ''' Deletes the widget after confirmation '''

            #self.widget.story.close_menu_instant()
            self.widget.p.pop_dialog()
            self.widget.story.delete_widget(self.widget) 
            self.widget.story.active_rail.content.reload_rail()    # Reload the rail to reflect the deletion
            self.widget.story.active_rail.update()

        # Append an overlay to confirm the deletion
        dlg = ft.AlertDialog(
            title=ft.Text(f"Are you sure you want to delete {self.widget.title} forever? This cannot be undone!", weight=ft.FontWeight.BOLD),
            alignment=ft.Alignment.CENTER,
            title_padding=ft.Padding.all(25),
            actions=[
                ft.TextButton("Cancel", on_click=lambda e: self.widget.p.pop_dialog(dlg)),
                ft.TextButton("Delete", on_click=_delete_confirmed, style=ft.ButtonStyle(color=ft.Colors.ERROR)),
            ]
        )

        self.widget.story.close_menu_instant()

        if app.settings.data.get('confirm_item_delete', False):
            self.widget.p.show_dialog(dlg)
        else:
            _delete_confirmed()


    # Called to reload our tree view file display
    def reload(self):

        self.content = ft.Container(
            expand=True, 
            padding=ft.Padding(0, 2, 5, 2),
            clip_behavior=ft.ClipBehavior.ANTI_ALIAS,
            border_radius=ft.BorderRadius.all(6),
            content=ft.Draggable(
                group="widgets",
                data=self.widget.data['key'],
                content_feedback=ft.TextButton(ft.Row([ft.Icon(self.icon, expand=True), ft.Text(self.widget.title, style=self.text_style, expand=True)], expand=True)),
                on_drag_start=lambda e: self.widget.story.workspace.show_pin_drag_targets(),
                content=ft.GestureDetector(
                    mouse_cursor=ft.MouseCursor.CLICK,
                    content=ft.Row(
                        expand=True,
                        controls=[
                            ft.Icon(self.icon, color=self.icon_color), 
                            ft.Text(value=self.widget.title, style=self.text_style, expand=True, overflow=ft.TextOverflow.ELLIPSIS),   
                        ],
                    ),
                )
            )
        )

        
        try:
            self.update()
        except Exception as e:
            pass